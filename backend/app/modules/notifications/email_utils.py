"""Módulo encargado de enviar notificaciones por correo electrónico a los usuarios cuando se activan sus alertas."""

import os
import smtplib
from email.mime.text import MIMEText


def send_email_notification(to_email: str, subject: str, body: str) -> None:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_SENDER", username)

    if not host or not username or not password or not sender:
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(username, password)
        server.sendmail(sender, [to_email], msg.as_string())
