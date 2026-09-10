import logging

# todo |EmailService
# todo |     ├── SMTP
# todo |     ├── Resend
# todo |     ├── SendGrid
# todo |     └── другой provider
logger = logging.getLogger(__name__)


class EmailService:
    def send_password_reset_email(
        self,
        email: str,
        reset_token: str,
    ) -> None:
        reset_url = "http://localhost:3000/reset-password" f"?token={reset_token}"

        logger.info(
            "Password reset email would be sent to %s",
            email,
        )

        logger.info(
            "Password reset URL: %s",
            reset_url,
        )
