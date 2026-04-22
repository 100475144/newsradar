"""Servicio del módulo alerts: lógica de negocio relacionada con alertas y reglas de coincidencia."""

from fastapi import HTTPException, status

from app.modules.alerts.models import Alert
from app.modules.alerts.repository import AlertRepository


class AlertService:
    MAX_ALERTS = 20

    def __init__(self, repository: AlertRepository):
        self.repository = repository

    def list_alerts(self, user_id: int):
        return self.repository.list_for_user(user_id)

    def list_active_alerts(self) -> list[Alert]:
        return self.repository.list_active()

    def get_alert(self, alert_id: int) -> Alert:
        alert = self.repository.get_by_id(alert_id)
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
            keyword=data.keyword.strip(),
            expanded_keywords=[item.strip() for item in (data.expanded_keywords or []) if item and item.strip()],
            category=data.category,
            source_ids=data.source_ids or [],
            notify_in_app=bool(data.notify_in_app),
            notify_email=bool(data.notify_email),
            created_by=user_id,
        )

    def update_alert(self, alert_id: int, data) -> Alert:
        alert = self.get_alert(alert_id)

        fields = {}
        if hasattr(data, "name") and data.name is not None:
            fields["name"] = data.name.strip()
        if hasattr(data, "keyword") and data.keyword is not None:
            fields["keyword"] = data.keyword.strip()
        if hasattr(data, "expanded_keywords") and data.expanded_keywords is not None:
            fields["expanded_keywords"] = [
                item.strip()
                for item in data.expanded_keywords
                if item and item.strip()
            ]
        if hasattr(data, "category") and data.category is not None:
            fields["category"] = data.category
        if hasattr(data, "source_ids") and data.source_ids is not None:
            fields["source_ids"] = data.source_ids
        if hasattr(data, "notify_in_app") and data.notify_in_app is not None:
            fields["notify_in_app"] = bool(data.notify_in_app)
        if hasattr(data, "notify_email") and data.notify_email is not None:
            fields["notify_email"] = bool(data.notify_email)
        if hasattr(data, "is_active") and data.is_active is not None:
            fields["is_active"] = bool(data.is_active)

        return self.repository.update(alert, **fields)
    
    def activate_alert(self, alert_id: int) -> Alert:
        alert = self.get_alert(alert_id)
        return self.repository.update(alert, is_active=True)

    def deactivate_alert(self, alert_id: int) -> Alert:
        alert = self.get_alert(alert_id)
        return self.repository.update(alert, is_active=False)

    def delete_alert(self, alert_id: int) -> None:
        alert = self.get_alert(alert_id)
        self.repository.delete(alert)