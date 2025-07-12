from pathlib import Path
from typing import Any

import emails
from emails.template import JinjaTemplate
from loguru import logger as _logger

from app import paths, settings


# Main Logger
logger = _logger.bind(name="logger")
logger.add(paths.LOG_FILE, level=settings.LOG_LEVEL, rotation="10 MB")


async def notify(
    text: str, telegram: bool = True, email: bool = settings.EMAILS_ENABLED
) -> dict[str, Any]:
    """
    Sends a notification via Telegram and email.

    Args:
        text (str): The notification text to send.
        telegram (bool): Whether to send the notification via Telegram. Defaults to True.
        email (bool): Whether to send the notification via email. Defaults to True.

    Returns:
        dict[str, Any]: The response from the notification types APIs.

    """
    response = {}

    if email and settings.NOTIFY_EMAIL_ENABLED:
        response["email"] = send_email(
            email_to=settings.NOTIFY_EMAIL_TO,
            subject_template="Server Notification",
            html_template=text,
            environment={"name": f"{settings.PROJECT_NAME}"},
        )
    return response


def send_email(
    email_to: str | None,
    subject_template: str = "",
    html_template: str = "",
    environment: dict[str, Any] | None = None,
    subject: str | None = None,
    message: str | None = None,
) -> Any:
    """
    Sends an email using the provided templates and environment variables.

    Args:
        email_to (str): The email address to send the email to.
        subject_template (str): The subject template. Defaults to "".
        html_template (str): The HTML template. Defaults to "".
        environment (dict[str, Any] | None): The environment variables to use when
            rendering the templates. Defaults to None.
        subject (str | None): Optional direct subject text. If provided, overrides subject_template.
        message (str | None): Optional direct message text. If provided, overrides html_template.

    Returns:
        Any: The email response.

    Raises:
        ValueError: If the email variables are not set.
    """

    if not settings.EMAILS_ENABLED or email_to is None:
        raise ValueError("Emails are not enabled or email_to is None")

    # Use direct subject/message if provided, otherwise use templates
    final_subject = subject if subject is not None else subject_template
    final_html = message if message is not None else html_template

    # Build the email
    message_obj: emails.Message = emails.Message(  # type: ignore
        subject=final_subject if subject is not None else JinjaTemplate(final_subject),
        html=final_html if message is not None else JinjaTemplate(final_html),
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )

    # Build the SMTP options
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT, "timeout": 20}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    else:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD

    if not environment:
        environment = {}

    # Send the email
    try:
        response = message_obj.send(to=email_to, render=environment, smtp=smtp_options)
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise e
    return response


def get_html_template(template: Path) -> str:
    return template.read_text(encoding="utf8")  # pragma: no cover


def send_test_email(email_to: str) -> None:
    send_email(
        email_to=email_to,
        subject_template=f"{settings.PROJECT_NAME} - Test email",
        html_template=get_html_template(template=paths.EMAIL_TEMPLATES_PATH / "test_email.mjml"),
        environment={"project_name": settings.PROJECT_NAME, "email": email_to},
    )


def send_reset_password_email(email_to: str, username: str, token: str) -> None:
    send_email(
        email_to=email_to,
        subject_template=f"{settings.PROJECT_NAME} - Password recovery for user {username}",
        html_template=get_html_template(
            template=paths.EMAIL_TEMPLATES_PATH / "reset_password.mjml"
        ),
        environment={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": f"{settings.BASE_URL}/reset-password?token={token}",
        },
    )


def send_new_account_email(email_to: str, username: str, password: str) -> None:
    send_email(
        email_to=email_to,
        subject_template=f"{settings.PROJECT_NAME} - New account for user {username}",
        html_template=get_html_template(template=paths.EMAIL_TEMPLATES_PATH / "new_account.mjml"),
        environment={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": settings.SERVER_HOST,
        },
    )
