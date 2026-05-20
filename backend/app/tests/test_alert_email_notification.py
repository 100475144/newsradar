import base64
import os
import time
from datetime import datetime, timezone
from email.header import decode_header
from uuid import uuid4

import httpx

from app.core.database import session_newsradar
from app.core.security import get_password_hash
from app.core.config import settings
from app.modules.alerts.models import Alert
from app.modules.auth.models import User
from app.modules.news.models import News
from app.modules.news.repository import NewsRepository
from app.modules.news.schemas import NewsCreateInternal
from app.modules.news.service import NewsService
from app.modules.notifications.models import Notification
from app.modules.sources.models import Category, InformationSource, RSSChannel


MAILHOG_API_URL = os.getenv(
    "MAILHOG_API_URL",
    f"http://{settings.smtp_host or 'localhost'}:8025/api/v2/messages",
)


def _decode_mailhog_body(item: dict) -> str:
    encoded = item["Content"]["Body"].replace("\r", "").replace("\n", "")
    return base64.b64decode(encoded).decode("utf-8")


def _decode_mime_header(value: str) -> str:
    parts = []
    for text, encoding in decode_header(value):
        if isinstance(text, bytes):
            parts.append(text.decode(encoding or "utf-8"))
        else:
            parts.append(text)
    return "".join(parts)


def _find_message_for_recipient(recipient: str) -> dict | None:
    response = httpx.get(MAILHOG_API_URL, timeout=5.0)
    response.raise_for_status()
    payload = response.json()

    for item in payload.get("items", []):
        recipients = item.get("Raw", {}).get("To", [])
        if recipient in recipients:
            return item

    return None


def _wait_for_message(recipient: str, timeout_seconds: float = 10.0) -> dict:
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        message = _find_message_for_recipient(recipient)
        if message is not None:
            return message
        time.sleep(0.5)

    raise AssertionError(f"No MailHog message found for {recipient!r} after {timeout_seconds} seconds.")


def test_matching_news_sends_email_notification_via_mailhog():
    unique = uuid4().hex[:8]
    email = f"alert-email-{unique}@example.com"
    source_url = f"https://example.com/rss/{unique}.xml"
    article_link = f"https://example.com/articles/{unique}"
    alert_name = f"AI Alert {unique}"

    db = session_newsradar()
    created_ids: dict[str, int] = {}

    try:
        user = User(
            email=email,
            first_name="Alert",
            last_name="Email",
            organization="NewsRadar",
            hashed_password=get_password_hash("Password123!"),
            role="gestor",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        created_ids["user_id"] = user.id

        # Asegurar Category IPTC y crear InformationSource + RSSChannel.
        category = (
            db.query(Category)
            .filter(Category.name == "Ciencia y tecnología")
            .first()
        )
        if category is None:
            category = Category(id=13000000, name="Ciencia y tecnología", source="IPTC")
            db.add(category)
            db.commit()
            db.refresh(category)

        medium = InformationSource(
            name=f"Example News {unique}",
            url="https://example.com/",
        )
        db.add(medium)
        db.commit()
        db.refresh(medium)
        created_ids["medium_id"] = medium.id

        channel = RSSChannel(
            url=source_url,
            category_id=category.id,
            information_source_id=medium.id,
            name=f"Test Source {unique}",
            is_active=True,
        )
        db.add(channel)
        db.commit()
        db.refresh(channel)
        created_ids["source_id"] = channel.id

        alert = Alert(
            name=alert_name,
            keyword="ai",
            descriptors=["machine learning", "neural networks", "automation"],
            categories=[{"code": "Ciencia y tecnología", "label": "Science and Technology"}],
            rss_channels_ids=[str(channel.id)],
            information_sources_ids=[],
            cron_expression="*/5 * * * *",
            is_active=True,
            notify_in_app=False,
            notify_email=True,
            user_id=user.id,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        created_ids["alert_id"] = alert.id

        news_service = NewsService(NewsRepository(db))
        payload = NewsCreateInternal(
            source_id=channel.id,
            title=f"AI breakthrough {unique}",
            link=article_link,
            summary="Machine learning and neural networks are changing the industry.",
            published_at=datetime.now(timezone.utc),
            category="Ciencia y tecnología",
            classification_origin="source",
            language="en",
            author="Test Reporter",
            external_id=f"external-{unique}",
        )

        created_news = news_service.create_news_from_crawler(payload)
        created_ids["news_id"] = created_news.id

        message = _wait_for_message(email)
        subject = _decode_mime_header(message["Content"]["Headers"]["Subject"][0])
        body = _decode_mailhog_body(message)

        # El nombre de la alerta aparece en el subject, no en el body.
        assert "Actualización de" in subject
        assert alert_name in subject
        # El body incluye el resumen del RSS (checklist #11) y el enlace.
        assert "Machine learning and neural networks" in body
        assert article_link in body

        notification_count = (
            db.query(Notification)
            .filter(Notification.user_id == user.id)
            .count()
        )
        assert notification_count == 0

    finally:
        if created_ids.get("news_id"):
            db.query(News).filter(News.id == created_ids["news_id"]).delete()
        if created_ids.get("alert_id"):
            db.query(Alert).filter(Alert.id == created_ids["alert_id"]).delete()
        if created_ids.get("source_id"):
            db.query(RSSChannel).filter(RSSChannel.id == created_ids["source_id"]).delete()
        if created_ids.get("medium_id"):
            db.query(InformationSource).filter(
                InformationSource.id == created_ids["medium_id"]
            ).delete()
        if created_ids.get("user_id"):
            db.query(User).filter(User.id == created_ids["user_id"]).delete()
        db.commit()
        db.close()
