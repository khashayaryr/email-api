import time

from loguru import logger

# Make sure the script can find your utility modules
from utils.db import DatabaseHandler
from utils.helpers import send_email

# --- Configuration ---
CHECK_INTERVAL_SECONDS = 60  # Check for due emails every 60 seconds

# --- Personalization Helper (similar to the preview function) ---
def personalize_email(body_template, recipient_profile, sender_profile, include_signature):
    """Replaces placeholders and adds a signature for the final email."""
    final_text = body_template

    # Replace recipient placeholders
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

# --- Main Worker Loop ---
def main():
    logger.info("Email Sending Worker started.")
    db = DatabaseHandler(db_file="db.json")

    while True:
        logger.info(f"Checking for due emails... (Next check in {CHECK_INTERVAL_SECONDS}s)")

        due_emails = db.get_due_emails()

        if not due_emails:
            logger.info("No due emails found.")
        else:
            logger.success(f"Found {len(due_emails)} email job(s) to process.")

            all_profiles = db.get_all_profiles()
            profile_id_map = {p.doc_id: p for p in all_profiles}

            for email_job in due_emails:
                job_id = email_job.doc_id
                logger.info(f"Processing job ID: {job_id}")

                sender_profile = email_job["sender_profile"]
                subject = email_job["subject"]
                body_template = email_job["body"]
                include_signature = email_job.get("add_signature", True)
                attachments = email_job.get("attachments", [])

                success_count = 0
                for recipient_id in email_job["recipients"]:
                    recipient_profile = profile_id_map.get(recipient_id)
                    if not recipient_profile:
                        logger.warning(f"Skipping recipient ID {recipient_id} for job {job_id}: Profile not found.")
                        continue

                    final_body = personalize_email(body_template, recipient_profile, sender_profile, include_signature)

                    try:
                        logger.info(f"Sending email to {recipient_profile['email']}...")
                        send_email(
                            to=recipient_profile["email"],
                            subject=subject,
                            contents=final_body,
                            attachments=attachments,
                        )
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send email to {recipient_profile['email']}. Error: {e}")

                # After processing all recipients, update the job status
                db.update_email_status(job_id, new_status="sent")
                logger.success(f"Finished processing job {job_id}. Sent to {success_count} recipient(s). Status updated to 'sent'.")

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
