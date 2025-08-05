import os

import yagmail
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

def send_email(to, subject, contents, attachments=None):

    try:
        sender_email = os.getenv("EMAIL_SENDER")
        sender_password = os.getenv("EMAIL_PASS")

        if not sender_email or not sender_password:
            raise ValueError("Sender email or password not found in .env file!")

        yag = yagmail.SMTP(sender_email, sender_password)

        yag.send(
            to=to,
            subject=subject,
            contents=contents,
            attachments=attachments,
        )

        logger.success("Email sent successfully!")
    except Exception as e:
        logger.error(f"An error occured: {e!s}")
        return False
    else:
        return True
    finally:
        if "yag" in locals():
            yag.close()
