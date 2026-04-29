"""Servicio del módulo alerts.

Adaptado al schema oficial (T6.4).
"""

from fastapi import HTTPException, status

from app.core.iptc import IPTC_CATEGORIES
from app.modules.alerts.models import Alert
from app.modules.alerts.repository import AlertRepository


def _normalize_categories(categories: list) -> list[dict]:
    """Normalize categories list of objects/dicts into [{code, label}]."""
    cleaned: list[dict] = []
    seen: set[str] = set()
    for entry in categories or []:
        if hasattr(entry, "model_dump"):
            data = entry.model_dump()
        elif isinstance(entry, dict):
            data = entry
        else:
            continue
        code = (data.get("code") or "").strip().lower()
        if not code or code in seen:
            continue
        seen.add(code)
        label = (data.get("label") or IPTC_CATEGORIES.get(code) or code).strip()
        cleaned.append({"code": code, "label": label})
    return cleaned


def _normalize_id_list(values: list) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return cleaned


class AlertService:
    MAX_ALERTS = 20

    def __init__(self, repository: AlertRepository):
        self.repository = repository

    def list_alerts_for_user(self, user_id: int):
        return self.repository.list_for_user(user_id)

    def list_active_alerts(self) -> list[Alert]:
        return self.repository.list_active()

    def get_alert(self, alert_id: int, user_id: int) -> Alert:
        alert = self.repository.get_by_id_for_user(alert_id, user_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found.",
            )
        return alert

    def create_alert(self, data, user_id: int) -> Alert:
        if self.repository.count_for_user(user_id) >= self.MAX_ALERTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A manager can only create up to 20 alerts.",
            )

        return self.repository.create(
            name=data.name.strip(),
            descriptors=list(data.descriptors or []),
            categories=_normalize_categories(data.categories or []),
            rss_channels_ids=_normalize_id_list(data.rss_channels_ids or []),
            information_sources_ids=_normalize_id_list(data.information_sources_ids or []),
            cron_expression=data.cron_expression,
            user_id=user_id,
            keyword=getattr(data, "keyword", None),
            notify_in_app=bool(getattr(data, "notify_in_app", True)),
            notify_email=bool(getattr(data, "notify_email", False)),
            is_active=True,
        )

    def update_alert(self, alert_id: int, data, user_id: int) -> Alert:
        alert = self.get_alert(alert_id, user_id)

        fields: dict = {}
        if getattr(data, "name", None) is not None:
            fields["name"] = data.name.strip()
        if getattr(data, "descriptors", None) is not None:
            fields["descriptors"] = list(data.descriptors)
        if getattr(data, "categories", None) is not None:
            fields["categories"] = _normalize_categories(data.categories)
        if getattr(data, "rss_channels_ids", None) is not None:
            fields["rss_channels_ids"] = _normalize_id_list(data.rss_channels_ids)
        if getattr(data, "information_sources_ids", None) is not None:
            fields["information_sources_ids"] = _normalize_id_list(
                data.information_sources_ids
            )
        if getattr(data, "cron_expression", None) is not None:
            fields["cron_expression"] = data.cron_expression
        if getattr(data, "keyword", None) is not None:
            fields["keyword"] = data.keyword
        if getattr(data, "notify_in_app", None) is not None:
            fields["notify_in_app"] = bool(data.notify_in_app)
        if getattr(data, "notify_email", None) is not None:
            fields["notify_email"] = bool(data.notify_email)
        if getattr(data, "is_active", None) is not None:
            fields["is_active"] = bool(data.is_active)

        return self.repository.update(alert, **fields)

    def activate_alert(self, alert_id: int, user_id: int) -> Alert:
        alert = self.get_alert(alert_id, user_id)
        return self.repository.update(alert, is_active=True)

    def deactivate_alert(self, alert_id: int, user_id: int) -> Alert:
        alert = self.get_alert(alert_id, user_id)
        return self.repository.update(alert, is_active=False)

    def delete_alert(self, alert_id: int, user_id: int) -> None:
        alert = self.get_alert(alert_id, user_id)
        self.repository.delete(alert)
