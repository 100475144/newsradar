"""Módulo encargado de enviar notificaciones por correo electrónico."""

import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_smtp_config() -> tuple[str, int, str | None, str | None, str, bool] | None:
    host = settings.smtp_host
    username = settings.smtp_username
    password = settings.smtp_password
    sender = settings.smtp_sender or username

    if not host or not sender:
        return None

    return host, settings.smtp_port, username, password, sender, settings.smtp_use_tls


def send_email(to_email: str, subject: str, body: str) -> bool:
    cfg = _get_smtp_config()
    if cfg is None:
        logger.warning("SMTP not configured — email to %s not sent.", to_email)
        return False

    host, port, username, password, sender, use_tls = cfg

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    try:
        with smtplib.SMTP(host, port) as server:
            if use_tls:
                server.starttls()
            if username and password:
                server.login(username, password)
            server.sendmail(sender, [to_email], msg.as_string())
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False


def send_email_notification(to_email: str, subject: str, body: str) -> None:
    """Backwards-compatible wrapper used by alert matching."""
    send_email(to_email, subject, body)


def send_verification_email(to_email: str, token: str) -> bool:
    verify_url = f"{settings.frontend_url}/verify-email?token={token}"
    subject = "NewsRadar — Verifica tu cuenta"
    body = (
        f"Bienvenido a NewsRadar.\n\n"
        f"Para activar tu cuenta, haz clic en el siguiente enlace:\n\n"
        f"{verify_url}\n\n"
        f"Este enlace caduca en 24 horas.\n\n"
        f"Si no te has registrado, ignora este correo."
    )
    return send_email(to_email, subject, body)
