"""Simple async email sender using a threadpool (SMTP)."""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from app.config import get_settings


async def send_email(subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.smtp_host or not settings.fallback_email:
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_username or settings.fallback_email
    message["To"] = settings.fallback_email
    message.set_content(body)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        _send,
        settings.smtp_host,
        settings.smtp_port,
        settings.smtp_username,
        settings.smtp_password,
        message,
    )


def _send(
    host: str, port: int, username: str | None, password: str | None, message: EmailMessage
) -> None:
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(message)


__all__ = ["send_email"]
