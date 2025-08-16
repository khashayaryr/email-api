import os
import smtplib
from typing import Any

import yagmail
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from the .env file in the project root
load_dotenv()


def render_email_body(
    body_template: str,
    recipient_profile: dict[str, Any],
    sender_profile: dict[str, Any],
    include_signature: bool = True,
) -> str:
    """Render the email body by replacing placeholders with recipient and sender fields.
    - Recipient fields: {name}, {email}, {title}, {profession}, ...
    - Sender fields (prefixed with my_): {my_name}, {my_title}, {my_profession}, ...
    """
    rendered = body_template or ""
    sender_prefixed = {f"my_{k}": v for k, v in (sender_profile or {}).items()}
    data = {**(recipient_profile or {}), **sender_prefixed}

    for key, value in data.items():
        rendered = rendered.replace(f"{{{key}}}", str(value))

    if include_signature:
        signature = (sender_profile or {}).get("signature", "")
        if signature:
            rendered = f"{rendered}\n\n--\n{signature}"

    return rendered


def _map_smtp_error(e: Exception) -> str:
    """Map smtplib / transport exceptions to concise error codes for logs/UI."""
    if isinstance(e, smtplib.SMTPAuthenticationError):
        return "auth_error"
    if isinstance(e, smtplib.SMTPRecipientsRefused):
        return "invalid_recipient"
    if isinstance(e, smtplib.SMTPSenderRefused):
        return "sender_refused"

    if isinstance(e, smtplib.SMTPDataError):
        code = getattr(e, "smtp_code", None)
        if code in (421, 451, 452):
            return "temp_rate_limited"
        if code in (550, 551, 552, 553):
            return "mailbox_unavailable"
        if code == 554:
            return "transaction_failed"
        return "data_error"

    if isinstance(e, smtplib.SMTPConnectError):
        return "connect_error"
    if isinstance(e, smtplib.SMTPHeloError):
        return "helo_error"
    if isinstance(e, smtplib.SMTPException):
        return "smtp_error"

    return "send_error"


def send_email(
    to: str | list[str],
    subject: str,
    contents: str | list[Any],
    attachments: list[str] | None = None,
    *,
    is_html: bool = False,  # kept for future branching if needed
) -> tuple[bool, str | None]:
    """Send an email using Gmail via yagmail with credentials from .env.
    Returns (ok, error_code). error_code is None on success.
    """
    yag_connection = None
    try:
        sender_email = os.getenv("EMAIL_SENDER")
        sender_password = os.getenv("EMAIL_PASS")

        if not sender_email or not sender_password:
            raise ValueError("missing_sender_creds")

        # Filter out missing attachments for safety
        if attachments:
            attachments = [p for p in attachments if p and os.path.exists(p)] or None

        yag_connection = yagmail.SMTP(sender_email, sender_password)
        # yagmail auto-detects HTML if contents looks like HTML; is_html flag reserved for future logic
        yag_connection.send(
            to=to,
            subject=subject,
            contents=contents,
            attachments=attachments,
        )

        logger.success(f"Email successfully sent to: {to}")
        return True, None

    except Exception as e:
        code = _map_smtp_error(e) if not isinstance(e, ValueError) else str(e)
        logger.error(f"Send error to {to}: {code} ({e!s})")
        return False, code

    finally:
        if yag_connection:
            try:
                yag_connection.close()
            except Exception as close_err:
                logger.warning(f"SMTP close error (non-fatal): {close_err!s}")
