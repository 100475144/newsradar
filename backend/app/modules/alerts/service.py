"""Servicio del módulo alerts: lógica de negocio relacionada con alertas y reglas de coincidencia."""

from fastapi import HTTPException, status

from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.schemas import AlertCreate, AlertUpdate


class AlertService:
    MAX_ALERTS_PER_USER = 20

    def __init__(self, repository: AlertRepository):
        self.repository = repository

    def create_alert(self, data: AlertCreate, user_id: int):
        if self.repository.count_for_user(user_id) >= self.MAX_ALERTS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user can only have up to 20 alerts.",
            )

        return self.repository.create(
            name=data.name.strip(),
            keyword=data.keyword.strip(),
            expanded_keywords=data.expanded_keywords,
            category=data.category.strip(),
            source_ids=data.source_ids,
            notify_in_app=data.notify_in_app,
            notify_email=data.notify_email,
            created_by=user_id,
        )

    def list_alerts(self, user_id: int):
        return self.repository.list_for_user(user_id)

    def get_alert(self, alert_id: int, user_id: int):
        alert = self.repository.get_by_id_for_user(alert_id, user_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found.",
            )
        return alert

    def update_alert(self, alert_id: int, data: AlertUpdate, user_id: int):
        alert = self.get_alert(alert_id, user_id)

        fields = {
            "name": data.name.strip() if data.name is not None else None,
            "keyword": data.keyword.strip() if data.keyword is not None else None,
            "category": data.category.strip() if data.category is not None else None,
            "expanded_keywords": data.expanded_keywords,
            "source_ids": data.source_ids,
            "is_active": data.is_active,
            "notify_in_app": data.notify_in_app,
            "notify_email": data.notify_email,
        }
        return self.repository.update(alert, **fields)

    def delete_alert(self, alert_id: int, user_id: int):
        alert = self.get_alert(alert_id, user_id)
        self.repository.delete(alert)
        return {"message": "Alert deleted successfully."}

    def activate_alert(self, alert_id: int, user_id: int):
        alert = self.get_alert(alert_id, user_id)
        return self.repository.update(alert, is_active=True)

    def deactivate_alert(self, alert_id: int, user_id: int):
        alert = self.get_alert(alert_id, user_id)
        return self.repository.update(alert, is_active=False)
