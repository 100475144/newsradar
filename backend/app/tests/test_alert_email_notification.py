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
from app.modules.sources.models import Source


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

        source = Source(
            medium_name="Example News",
            name=f"Test Source {unique}",
            url=source_url,
            category="science_technology",
            is_active=True
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        created_ids["source_id"] = source.id

        alert = Alert(
            name=alert_name,
            keyword="ai",
            expanded_keywords=["machine learning", "neural networks", "automation"],
            category="science_technology",
            source_ids=[source.id],
            is_active=True,
            notify_in_app=False,
            notify_email=True,
            created_by=user.id,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        created_ids["alert_id"] = alert.id

        news_service = NewsService(NewsRepository(db))
        payload = NewsCreateInternal(
            source_id=source.id,
            title=f"AI breakthrough {unique}",
            link=article_link,
            summary="Machine learning and neural networks are changing the industry.",
            published_at=datetime.now(timezone.utc),
            category="science_technology",
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

        assert "Actualización de" in subject
        assert alert_name in body
        assert "Resumen:" in body
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
            db.query(Source).filter(Source.id == created_ids["source_id"]).delete()
        if created_ids.get("user_id"):
            db.query(User).filter(User.id == created_ids["user_id"]).delete()
        db.commit()
        db.close()
