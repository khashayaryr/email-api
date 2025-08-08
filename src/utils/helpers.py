import os
from typing import Any

import yagmail
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from the .env file in the project root
load_dotenv()


def send_email(
    to: str | list[str],
    subject: str,
    contents: str | list[Any],
    attachments: list[str] | None = None,
) -> bool:
    """Sends an email using Gmail via yagmail with credentials from environment variables.

    This function fetches the sender's email and an app-specific password from
    a .env file, connects to the Gmail SMTP server, and sends the email.

    :param to: The recipient's email address or a list of recipient email addresses.
    :param subject: The subject line of the email.
    :param contents: The body of the email. Can be a string or a list for complex content (e.g., HTML).
    :param attachments: An optional list of file paths to attach to the email.
    :return: True if the email was sent successfully, False otherwise.
    """
    yag_connection = None  # Initialize to None to ensure it's defined for the finally block
    try:
        sender_email = os.getenv("EMAIL_SENDER")
        sender_password = os.getenv("EMAIL_PASS")

        if not sender_email or not sender_password:
            raise ValueError("Sender email (EMAIL_SENDER) or password (EMAIL_PASS) not found in .env file!")

        # Initialize the SMTP connection
        yag_connection = yagmail.SMTP(sender_email, sender_password)

        # Send the email
        yag_connection.send(
            to=to,
            subject=subject,
            contents=contents,
            attachments=attachments,
        )

        logger.success(f"Email successfully sent to: {to}")
        return True

    except Exception as e:
        logger.error(f"An error occurred while sending email to {to}: {e!s}")
        return False

    finally:
        # Ensure the connection is closed if it was successfully opened
        if yag_connection:
            yag_connection.close()
