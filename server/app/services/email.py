import logging
import smtplib
from email.message import EmailMessage

from ..config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Отправка писем через SMTP.

    Если SMTP не настроен, письмо не отправляется, а в debug-режиме
    в лог пишется ссылка для локальной проверки сценария.
    """

    def send_password_reset_email(
        self,
        email: str,
        reset_token: str,
    ) -> None:
        reset_url = (
            f"{settings.frontend_url.rstrip('/')}/reset-password"
            f"?token={reset_token}"
        )

        self.send(
            email=email,
            subject="Восстановление пароля в Task Planner",
            body=(
                "Вы запросили восстановление пароля в Task Planner.\n\n"
                f"Перейдите по ссылке: {reset_url}\n\n"
                "Если вы не запрашивали восстановление, просто проигнорируйте письмо."
            ),
        )

        if settings.app_debug:
            logger.info("Password reset URL (debug): %s", reset_url)

    def send(
        self,
        email: str,
        subject: str,
        body: str,
    ) -> None:
        if not settings.smtp_host:
            logger.info(
                "SMTP is not configured, email to %s was skipped",
                email,
            )
            return

        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = email
        message["Subject"] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=10,
            ) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()

                if settings.smtp_user and settings.smtp_password:
                    smtp.login(
                        settings.smtp_user,
                        settings.smtp_password,
                    )

                smtp.send_message(message)
        except (smtplib.SMTPException, OSError):
            logger.exception("Failed to send email to %s", email)
