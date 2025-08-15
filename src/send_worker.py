import os
import time

from loguru import logger

from utils.db import DatabaseHandler
from utils.helpers import render_email_body, send_email

POLL_SECONDS = int(os.getenv("WORKER_POLL_SECONDS", "20"))


def _send_one_delivery(db: DatabaseHandler, delivery_doc) -> None:
    delivery_id = delivery_doc.doc_id
    campaign_id = delivery_doc.get("campaign_id")
    recipient_email = delivery_doc.get("recipient_email")
    recipient_snapshot = delivery_doc.get("recipient_snapshot") or {}

    if not campaign_id:
        logger.error(f"[delivery {delivery_id}] Missing campaign_id.")
        db.update_delivery_status(delivery_id, "failed", "missing_campaign")
        return

    campaign = db.get_campaign(campaign_id)
    if not campaign:
        logger.error(f"[delivery {delivery_id}] Campaign {campaign_id} not found.")
        db.update_delivery_status(delivery_id, "failed", "campaign_not_found")
        return

    subject = campaign.get("subject", "")
    body_template = campaign.get("body", "")
    attachments = campaign.get("attachments", []) or []
    add_signature = bool(campaign.get("add_signature", True))
    sender_profile = campaign.get("sender_profile", {}) or {}
    body_is_html = bool(campaign.get("body_is_html", False))

    if not recipient_email:
        logger.warning(f"[delivery {delivery_id}] No recipient email in snapshot.")
        db.update_delivery_status(delivery_id, "failed", "missing_email")
        return

    # Personalized body
    rendered_body = render_email_body(
        body_template=body_template,
        recipient_profile=recipient_snapshot,
        sender_profile=sender_profile,
        include_signature=add_signature,
    )

    ok, err = send_email(
        to=recipient_email,
        subject=subject,
        contents=rendered_body,
        attachments=attachments,
        is_html=body_is_html,
    )

    if ok:
        logger.success(f"[delivery {delivery_id}] Sent to {recipient_email}.")
        db.update_delivery_status(delivery_id, "sent", None, rendered_body=rendered_body)

    else:
        logger.error(f"[delivery {delivery_id}] Failed to send to {recipient_email}: {err}")
        db.update_delivery_status(delivery_id, "failed", err or "send_error")


def main() -> None:
    logger.remove()
    logger.add(lambda msg: print(msg, end=""))
    logger.info("📮 Email worker started. Polling for due deliveries...")

    db = DatabaseHandler(db_file="db.json")

    try:
        while True:
            db.reload()
            due_deliveries = db.get_due_deliveries()
            if due_deliveries:
                logger.info(f"Found {len(due_deliveries)} due delivery(ies). Processing...")
                for delivery in due_deliveries:
                    try:
                        _send_one_delivery(db, delivery)
                    except Exception as e:
                        from traceback import format_exc
                        logger.error(f"[delivery {getattr(delivery, 'doc_id', '?')}] Unexpected error: {e}\n{format_exc()}")
                        try:
                            db.update_delivery_status(delivery.doc_id, "failed", "unexpected_error")
                        except Exception:
                            logger.exception("Also failed to mark delivery as failed.")
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Exiting worker.")


if __name__ == "__main__":
    main()
