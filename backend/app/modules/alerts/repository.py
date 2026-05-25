"""Repositorio del módulo alerts: acceso a datos de alertas.

Adaptado al schema oficial (T6.4): usa ``user_id`` en lugar de
``created_by`` y los campos ``descriptors`` / ``categories`` /
``rss_channels_ids`` / ``information_sources_ids``.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.alerts.models import Alert


class AlertRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_for_user(self, user_id: int) -> int:
        return self.db.query(Alert).filter(Alert.user_id == user_id).count()

    def create(
        self,
        *,
        name: str,
        descriptors: list[str],
        categories: list[dict],
        rss_channels_ids: list[str],
        information_sources_ids: list[str],
        cron_expression: str,
        user_id: int,
        keyword: str | None = None,
        priority: int = 2,
        notify_in_app: bool = True,
        notify_email: bool = False,
        is_active: bool = True,
    ) -> Alert:
        alert = Alert(
            name=name,
            descriptors=descriptors,
            categories=categories,
            rss_channels_ids=rss_channels_ids,
            information_sources_ids=information_sources_ids,
            cron_expression=cron_expression,
            user_id=user_id,
            keyword=keyword,
            priority=priority,
            notify_in_app=notify_in_app,
            notify_email=notify_email,
            is_active=is_active,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def list_for_user(self, user_id: int) -> list[Alert]:
        return (
            self.db.query(Alert)
            .filter(Alert.user_id == user_id)
            .order_by(Alert.id.desc())
            .all()
        )

    def list_all(self) -> list[Alert]:
        return self.db.query(Alert).order_by(Alert.id.desc()).all()

    def list_active(self) -> list[Alert]:
        return (
            self.db.query(Alert)
            .filter(Alert.is_active.is_(True))
            .order_by(Alert.id.desc())
            .all()
        )

    def get_by_id(self, alert_id: int) -> Alert | None:
        return self.db.query(Alert).filter(Alert.id == alert_id).first()

    def get_by_id_for_user(self, alert_id: int, user_id: int) -> Alert | None:
        return (
            self.db.query(Alert)
            .filter(Alert.id == alert_id, Alert.user_id == user_id)
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

    def count_by_category_code(self) -> list[dict]:
        """Cuenta alertas agrupadas por el primer ``code`` de ``categories``.

        Como ``categories`` es un JSONB array de objetos, se usa la primera
        categoría como representativa para el dashboard.
        """
        # Postgres: extract first category code via jsonb operators.
        first_code = func.coalesce(
            Alert.categories[0]["code"].astext, "uncategorized"
        ).label("code")
        rows = (
            self.db.query(first_code, func.count(Alert.id).label("count"))
            .group_by(first_code)
            .order_by(func.count(Alert.id).desc())
            .all()
        )
        return [{"category": r.code, "count": r.count} for r in rows]
