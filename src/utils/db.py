import re
from contextlib import suppress  # NEW
from datetime import date, datetime
from typing import Any

from filelock import FileLock
from tinydb import Query, TinyDB, where

from utils.time import now_utc_iso, to_utc_iso  # UTC helpers

Document = dict[str, Any]


class DatabaseHandler:
    """Database operations with TinyDB for the Email App.

    Schema:
      - emails       (campaigns): one row per composed job (subject/body/attachments/sender); groups many deliveries
      - deliveries   (per recipient): one row per recipient; the worker sends these one by one
      - profiles, templates, user_profile, settings: as before
    """

    def __init__(self, db_file: str = "db.json"):
        self.db_path = db_file
        self._lock = FileLock(f"{db_file}.lock")
        self._open_db()

    # ----- internals -----
    def _open_db(self) -> None:
        self.db = TinyDB(self.db_path)
        self.profiles_table = self.db.table("profiles")
        self.templates_table = self.db.table("templates")
        self.user_profile_table = self.db.table("user_profile")
        self.emails_table = self.db.table("emails")          # "campaigns"
        self.deliveries_table = self.db.table("deliveries")  # per-recipient
        self.settings_table = self.db.table("settings")

    def reload(self) -> None:
        with self._lock:
            with suppress(Exception):
                self.db.close()
            self._open_db()

    # ---------------- Settings ----------------
    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._lock:
            row = self.settings_table.get(where("key") == key)
            return row.get("value") if row else default

    def set_setting(self, key: str, value: Any) -> None:
        with self._lock:
            row = self.settings_table.get(where("key") == key)
            if row:
                self.settings_table.update({"value": value}, doc_ids=[row.doc_id])
            else:
                self.settings_table.insert({"key": key, "value": value})

    def get_timezone(self) -> str | None:
        return self.get_setting("APP_TIMEZONE", None)

    def set_timezone(self, tzname: str) -> None:
        self.set_setting("APP_TIMEZONE", tzname)

    # ---------------- User Profile ----------------
    def get_user_profile(self) -> Document | None:
        with self._lock:
            rows = self.user_profile_table.all()
            return rows[0] if rows else None

    def update_user_profile(self, data: Document) -> None:
        with self._lock:
            self.user_profile_table.truncate()
            self.user_profile_table.insert(data)

    # ---------------- Profiles ----------------
    def add_profile(self, name: str, email: str, title: str, profession: str) -> bool:
        with self._lock:
            if not self.profiles_table.contains(where("email") == email):
                self.profiles_table.insert({
                    "name": name, "email": email, "title": title, "profession": profession,
                })
                return True
            return False

    def get_all_profiles(self) -> list[Document]:
        with self._lock:
            return self.profiles_table.all()

    def get_profiles_by_ids(self, ids: list[int]) -> list[Document]:
        with self._lock:
            results: list[Document] = []
            for rid in ids or []:
                row = self.profiles_table.get(doc_id=rid)
                if row is not None:
                    results.append(row)
            return results

    def delete_profile(self, doc_id: int) -> None:
        with self._lock:
            self.profiles_table.remove(doc_ids=[doc_id])

    # ---------------- Templates ----------------
    def add_template(self, name: str, subject: str, body: str) -> bool:
        with self._lock:
            if not self.templates_table.contains(where("name") == name):
                self.templates_table.insert({"name": name, "subject": subject, "body": body})
                return True
            return False

    def get_all_templates(self) -> list[Document]:
        with self._lock:
            return self.templates_table.all()

    def delete_template(self, doc_id: int) -> None:
        with self._lock:
            self.templates_table.remove(doc_ids=[doc_id])

    # ---------------- Emails (campaigns) ----------------
    def schedule_email(
        self, subject: str, body: str, recipients: list[int], schedule_time: datetime,
        sender_profile: Document, add_signature: bool = True,
        attachments: list[str] | None = None, reminder_date: date | None = None,
        body_is_html: bool = False,
    ) -> int:
        """Schedules an email campaign. Also creates one delivery row per recipient.
        Returns the campaign_id.
        """
        if attachments is None:
            attachments = []
        sched_utc = to_utc_iso(schedule_time)

        subject = str(subject or "")
        body = str(body or "")

        with self._lock:
            campaign_id = self.emails_table.insert({
                "subject": subject,
                "body": body,
                "body_is_html": bool(body_is_html),
                "recipients": recipients,
                "sender_profile": sender_profile,
                "status": "scheduled",
                "schedule_time": sched_utc,
                "sent_time": None,
                "reminder_date": reminder_date.isoformat() if reminder_date else None,
                "add_signature": add_signature,
                "attachments": attachments,
                "counts": {"total": len(recipients), "pending": len(recipients), "sent": 0, "failed": 0},
            })

            for rid in recipients:
                prof = self.profiles_table.get(doc_id=rid) or {}
                snapshot = {
                    "name": prof.get("name"),
                    "email": prof.get("email"),
                    "title": prof.get("title"),
                    "profession": prof.get("profession"),
                }
                self.deliveries_table.insert({
                    "campaign_id": campaign_id,
                    "recipient_id": rid,
                    "recipient_email": snapshot.get("email"),
                    "recipient_snapshot": snapshot,
                    "status": "pending",   # pending | sent | failed
                    "error": None,
                    "schedule_time": sched_utc,
                    "sent_time": None,
                    "last_attempt": None,
                })

            return campaign_id

    def get_campaign(self, campaign_id: int) -> Document | None:
        with self._lock:
            return self.emails_table.get(doc_id=campaign_id)

    def get_scheduled_emails(self) -> list[Document]:
        with self._lock:
            Email = Query()
            return self.emails_table.search(Email.status == "scheduled")

    def delete_scheduled_email(self, email_doc_id: int) -> None:
        """Cancel a scheduled campaign:
        - remove only PENDING deliveries (keep sent/failed history)
        - recompute campaign counts/status
        - if no deliveries remain at all, remove the campaign row
        """
        with self._lock:
            Delivery = Query()
            deliveries = self.deliveries_table.search(Delivery.campaign_id == email_doc_id)
            pending_ids = [d.doc_id for d in deliveries if d.get("status") == "pending"]
            if pending_ids:
                self.deliveries_table.remove(doc_ids=pending_ids)

            # Recompute aggregates; may become sent/failed/partial or remain scheduled with fewer pending
            self._recompute_campaign_aggregates(email_doc_id)

            # If there are literally no deliveries left, delete the campaign
            remaining = self.deliveries_table.search(Delivery.campaign_id == email_doc_id)
            if not remaining:
                self.emails_table.remove(doc_ids=[email_doc_id])

    def get_sent_emails(self) -> list[Document]:
        with self._lock:
            Email = Query()
            return self.emails_table.search(Email.status == "sent")

    def search_emails(self, search_term: str) -> list[Document]:
        """Search campaigns that are fully sent, case-insensitive on subject/body."""
        with self._lock:
            Email = Query()
            return self.emails_table.search(
                (Email.status == "sent") &
                (
                    (Email.subject.search(search_term, flags=re.IGNORECASE)) |
                    (Email.body.search(search_term, flags=re.IGNORECASE))
                ),
            )

    # ---------------- Deliveries (per recipient) ----------------
    def get_deliveries_for_campaign(self, campaign_id: int) -> list[Document]:
        with self._lock:
            Delivery = Query()
            return self.deliveries_table.search(Delivery.campaign_id == campaign_id)

    def get_due_deliveries(self) -> list[Document]:
        """Deliveries that are ready to send now (pending & schedule_time <= now)."""
        with self._lock:
            Delivery = Query()
            now_iso = now_utc_iso()
            return self.deliveries_table.search(
                (Delivery.status == "pending") & (Delivery.schedule_time <= now_iso),
            )

    def update_delivery_status(self, delivery_id: int, status: str, error: str | None, rendered_body: str | None = None) -> None:
        """Update a delivery row when an attempt is made; also refresh campaign aggregates."""
        now_iso = now_utc_iso()
        with self._lock:
            patch: dict[str, Any] = {"status": status, "last_attempt": now_iso}
            if status == "sent":
                patch["sent_time"] = now_iso
                patch["error"] = None
                if rendered_body is not None:
                    patch["rendered_body"] = rendered_body  # <- NEW: store personalized final text
            else:
                patch["error"] = error or "send_error"
            self.deliveries_table.update(patch, doc_ids=[delivery_id])

            delivery = self.deliveries_table.get(doc_id=delivery_id)
            if not delivery:
                return
            self._recompute_campaign_aggregates(delivery["campaign_id"])


    def _recompute_campaign_aggregates(self, campaign_id: int) -> None:
        """Recalculate counts and final campaign status based on deliveries."""
        Delivery = Query()
        deliveries = self.deliveries_table.search(Delivery.campaign_id == campaign_id)

        total = len(deliveries)
        pending = sum(1 for d in deliveries if d.get("status") == "pending")
        sent = sum(1 for d in deliveries if d.get("status") == "sent")
        failed = sum(1 for d in deliveries if d.get("status") == "failed")

        counts = {"total": total, "pending": pending, "sent": sent, "failed": failed}
        patch: dict[str, Any] = {"counts": counts}

        if pending == 0:
            if total == 0:
                # No deliveries at all — leave status untouched; caller may delete the campaign row.
                pass
            else:
                if sent == total:
                    status = "sent"
                elif failed == total:
                    status = "failed"
                else:
                    status = "partial"
                patch["status"] = status
                patch["sent_time"] = now_utc_iso()

        self.emails_table.update(patch, doc_ids=[campaign_id])

    # Back-compat helper (legacy)
    def get_due_emails(self) -> list[Document]:
        with self._lock:
            Email = Query()
            now_iso = now_utc_iso()
            return self.emails_table.search(
                (Email.status == "scheduled") & (Email.schedule_time <= now_iso),
            )

    # ---------------- Reminders ----------------
    def set_email_reminder(self, email_doc_id: int, reminder_date: date) -> None:
        with self._lock:
            self.emails_table.update(
                {"reminder_date": reminder_date.isoformat()},
                doc_ids=[email_doc_id],
            )

    def clear_email_reminder(self, email_doc_id: int) -> None:
        with self._lock:
            self.emails_table.update({"reminder_date": None}, doc_ids=[email_doc_id])

    def close_db(self) -> None:
        with self._lock:
            self.db.close()
