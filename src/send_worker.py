import time
from typing import Any

from loguru import logger

from utils.db import DatabaseHandler
from utils.helpers import send_email

# A type alias for a TinyDB Document for cleaner annotations
Document = dict[str, Any]

# --- Configuration ---
CHECK_INTERVAL_SECONDS: int = 60  # Check for due emails every 60 seconds


def personalize_email(
    body_template: str,
    recipient_profile: Document,
    sender_profile: Document,
    include_signature: bool,
) -> str:
    """Replaces placeholders in an email body with personalized data.

    This function takes a template string and populates it with data from
    both the recipient's and sender's profiles.

    :param body_template: The raw email body with placeholders like {name}.
    :param recipient_profile: The database document for the email recipient.
    :param sender_profile: The database document for the email sender.
    :param include_signature: A boolean indicating whether to append the sender's signature.
    :return: The personalized, final email body as a string.
    """
    final_text = body_template

    # Replace recipient placeholders (e.g., {name}, {title})
    for key, value in recipient_profile.items():
        final_text = final_text.replace(f"{{{key}}}", str(value))

    # Replace sender placeholders (e.g., {my_name})
    for key, value in sender_profile.items():
        final_text = final_text.replace(f"{{my_{key}}}", str(value))

    # Add signature if toggled for this email
    if include_signature:
        signature = sender_profile.get("signature", "")
        final_text = f"{final_text}\n\n--\n{signature}"

    return final_text


def main() -> None:
    """The main worker loop for processing and sending scheduled emails.

    This function runs indefinitely, periodically checking the database for
    emails that are due to be sent, processing them, and updating their status.
    """
    logger.info("Email Sending Worker started. Press Ctrl+C to stop.")
    db = DatabaseHandler(db_file="db.json")

    while True:
        try:
            logger.info(f"Checking for due emails... (Next check in {CHECK_INTERVAL_SECONDS}s)")

            due_emails: list[Document] = db.get_due_emails()

            if not due_emails:
                logger.info("No due emails found.")
            else:
                logger.success(f"Found {len(due_emails)} email job(s) to process.")

                # Fetch all profiles once per cycle for efficiency
                all_profiles: list[Document] = db.get_all_profiles()
                profile_id_map: dict[int, Document] = {p.doc_id: p for p in all_profiles}

                for email_job in due_emails:
                    job_id: int = email_job.doc_id
                    logger.info(f"Processing job ID: {job_id}")

                    # Safely get all required data from the email job document
                    sender_profile: Document = email_job.get("sender_profile", {})
                    subject: str = email_job.get("subject", "No Subject")
                    body_template: str = email_job.get("body", "")
                    include_signature: bool = email_job.get("add_signature", True)
                    attachments: list[str] = email_job.get("attachments", [])
                    recipient_ids: list[int] = email_job.get("recipients", [])

                    success_count = 0
                    for recipient_id in recipient_ids:
                        recipient_profile = profile_id_map.get(recipient_id)
                        if not recipient_profile:
                            logger.warning(f"Skipping recipient ID {recipient_id} for job {job_id}: Profile not found.")
                            continue

                        final_body = personalize_email(
                            body_template, recipient_profile, sender_profile, include_signature
                            )

                        try:
                            email_sent = send_email(
                                to=recipient_profile["email"],
                                subject=subject,
                                contents=final_body,
                                attachments=attachments,
                            )
                            if email_sent:
                                success_count += 1
                        except Exception as e:
                            logger.error(
                                f"An unexpected error occurred sending to {recipient_profile.get('email', 'N/A')}. Error: {e}"
                                )

                    # After processing all recipients, update the job status
                    db.update_email_status(job_id, new_status="sent")
                    logger.success(
                        f"Finished processing job {job_id}.Sent to {success_count} of {len(recipient_ids)} recipient(s). Status updated to 'sent'."
                        )

        except Exception as e:
            logger.critical(f"A critical error occurred in the main worker loop: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
