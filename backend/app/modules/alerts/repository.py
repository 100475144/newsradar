"""Repositorio del módulo alerts: acceso a datos de alertas."""

from sqlalchemy.orm import Session

from app.modules.alerts.models import Alert


class AlertRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_for_user(self, user_id: int) -> int:
        return self.db.query(Alert).filter(Alert.created_by == user_id).count()

    def create(
        self,
        *,
        name: str,
        keyword: str,
        expanded_keywords: list[str],
        category: str,
        source_ids: list[int],
        cron_expression: str,
        notify_in_app: bool,
        notify_email: bool,
        created_by: int,
    ) -> Alert:
        alert = Alert(
            name=name,
            keyword=keyword,
            expanded_keywords=expanded_keywords,
            category=category,
            source_ids=source_ids,
            cron_expression=cron_expression,
            notify_in_app=notify_in_app,
            notify_email=notify_email,
            created_by=created_by,
            is_active=True,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert
    
    def list_for_user(self, user_id: int) -> list[Alert]:
        return (
            self.db.query(Alert)
            .filter(Alert.created_by == user_id)
            .order_by(Alert.id.desc())
            .all()
        )

    def list_all(self) -> list[Alert]:
        return self.db.query(Alert).order_by(Alert.id.desc()).all()

    def list_active(self) -> list[Alert]:
        return (
            self.db.query(Alert)
            .filter(Alert.is_active == True)  # noqa: E712
            .order_by(Alert.id.desc())
            .all()
        )

    def get_by_id(self, alert_id: int) -> Alert | None:
        return self.db.query(Alert).filter(Alert.id == alert_id).first()

    def get_by_id_created_by(self, alert_id: int, user_id: int) -> Alert | None:
        return (
            self.db.query(Alert)
            .filter(Alert.id == alert_id, Alert.created_by == user_id)
            .first()
        )

    def update(self, alert: Alert, **fields) -> Alert:
        for key, value in fields.items():
            if value is not None:
                setattr(alert, key, value)

        self.db.commit()
        self.db.refresh(alert)
        return alert

    def delete(self, alert: Alert) -> None:
        self.db.delete(alert)
        self.db.commit()
