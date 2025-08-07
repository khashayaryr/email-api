import re
from datetime import date, datetime
from typing import Any

from tinydb import Query, TinyDB, where

# A type alias for a TinyDB Document for cleaner annotations
Document = dict[str, Any]


class DatabaseHandler:
    """A class to handle all database operations with TinyDB for the Streamlit Email App."""

    def __init__(self, db_file: str = "db.json"):
        """Initializes the database and creates tables if they don't exist.

        :param db_file: The path to the database file.
        """
        self.db = TinyDB(db_file)
        self.profiles_table = self.db.table("profiles")
        self.templates_table = self.db.table("templates")
        self.user_profile_table = self.db.table("user_profile")
        self.emails_table = self.db.table("emails")

    # --- User Profile Methods ---
    def get_user_profile(self) -> Document | None:
        """Retrieves the user's profile. Assumes only one user profile exists.

        :return: The user profile document or None if it doesn't exist.
        """
        # More robust way to get the single profile, as doc_id is not guaranteed
        if self.user_profile_table:
            return self.user_profile_table.all()[0]
        return None

    def update_user_profile(self, data: Document) -> None:
        """Creates or updates the user's profile.

        For a single-profile setup, this method clears the table and inserts the new profile.

        :param data: A dictionary containing the user's profile information.
        """
        self.user_profile_table.truncate()
        self.user_profile_table.insert(data)

    # --- Contact Profiles Methods ---
    def add_profile(self, name: str, email: str, title: str, profession: str) -> bool:
        """Adds a new contact profile to the database if the email is unique.

        :param name: The contact's full name.
        :param email: The contact's email address.
        :param title: The contact's job title.
        :param profession: The contact's profession or industry.
        :return: True if the profile was added successfully, False otherwise.
        """
        if not self.profiles_table.contains(where("email") == email):
            self.profiles_table.insert({
                "name": name, "email": email, "title": title, "profession": profession,
            })
            return True
        return False

    def get_all_profiles(self) -> list[Document]:
        """Retrieves all contact profiles.

        :return: A list of all profile documents.
        """
        return self.profiles_table.all()

    def delete_profile(self, doc_id: int) -> None:
        """Deletes a contact profile by its document ID.

        :param doc_id: The unique document ID of the profile to delete.
        """
        self.profiles_table.remove(doc_ids=[doc_id])

    # --- Email Templates Methods ---
    def add_template(self, name: str, subject: str, body: str) -> bool:
        """Adds a new email template if the name is unique.

        :param name: The name of the template.
        :param subject: The subject line of the template.
        :param body: The body content of the template.
        :return: True if the template was added successfully, False otherwise.
        """
        if not self.templates_table.contains(where("name") == name):
            self.templates_table.insert({"name": name, "subject": subject, "body": body})
            return True
        return False

    def get_all_templates(self) -> list[Document]:
        """Retrieves all email templates.

        :return: A list of all template documents.
        """
        return self.templates_table.all()

    def delete_template(self, doc_id: int) -> None:
        """Deletes a template by its document ID.

        :param doc_id: The unique document ID of the template to delete.
        """
        self.templates_table.remove(doc_ids=[doc_id])

    # --- Email Scheduling and History Methods ---
    def schedule_email(
        self, subject: str, body: str, recipients: list[int], schedule_time: datetime,
        sender_profile: Document, add_signature: bool = True,
        attachments: list[str] | None = None, reminder_date: date | None = None,
    ) -> None:
        """Schedules an email to be sent.

        :param subject: The email subject.
        :param body: The email body template.
        :param recipients: A list of recipient profile document IDs.
        :param schedule_time: The datetime object for when to send the email.
        :param sender_profile: A snapshot of the sender's profile.
        :param add_signature: Whether to add the user's signature to the email.
        :param attachments: A list of file paths for attachments.
        :param reminder_date: An optional date for a follow-up reminder.
        """
        if attachments is None:
            attachments = []

        self.emails_table.insert({
            "subject": subject, "body": body, "recipients": recipients,
            "sender_profile": sender_profile, "status": "scheduled",
            "schedule_time": schedule_time.isoformat(), "sent_time": None,
            "reminder_date": reminder_date.isoformat() if reminder_date else None,
            "add_signature": add_signature, "attachments": attachments,
        })

    def get_scheduled_emails(self) -> list[Document]:
        """Retrieves all emails with the status 'scheduled'.

        :return: A list of scheduled email documents.
        """
        Email = Query()
        return self.emails_table.search(Email.status == "scheduled")

    def delete_scheduled_email(self, email_doc_id: int) -> None:
        """Deletes a scheduled email by its document ID.

        :param email_doc_id: The document ID of the scheduled email to delete.
        """
        self.emails_table.remove(doc_ids=[email_doc_id])

    def get_sent_emails(self) -> list[Document]:
        """Retrieves all emails with the status 'sent'.

        :return: A list of sent email documents.
        """
        Email = Query()
        return self.emails_table.search(Email.status == "sent")

    def search_emails(self, search_term: str) -> list[Document]:
        """Searches sent emails for a term in the subject or body, case-insensitively.

        :param search_term: The string to search for.
        :return: A list of matching sent email documents.
        """
        Email = Query()
        return self.emails_table.search(
            (Email.status == "sent") &
            (
                (Email.subject.search(search_term, flags=re.IGNORECASE)) |
                (Email.body.search(search_term, flags=re.IGNORECASE))
            ),
        )

    def get_due_emails(self) -> list[Document]:
        """Retrieves scheduled emails where the schedule_time is in the past.

        :return: A list of due email documents.
        """
        Email = Query()
        now_iso = datetime.now().isoformat()
        return self.emails_table.search(
            (Email.status == "scheduled") & (Email.schedule_time <= now_iso),
        )

    def update_email_status(self, email_id: int, new_status: str) -> None:
        """Updates an email's status (e.g., to 'sent') and records the sent time.

        :param email_id: The document ID of the email to update.
        :param new_status: The new status string (e.g., 'sent', 'failed').
        """
        self.emails_table.update(
            {"status": new_status, "sent_time": datetime.now().isoformat()},
            doc_ids=[email_id],
        )

    # --- Reminder Methods ---
    def set_email_reminder(self, email_doc_id: int, reminder_date: date) -> None:
        """Sets or updates the reminder date for a specific email.

        :param email_doc_id: The document ID of the email to set a reminder for.
        :param reminder_date: The date object for the reminder.
        """
        self.emails_table.update(
            {"reminder_date": reminder_date.isoformat()},
            doc_ids=[email_doc_id],
        )

    def clear_email_reminder(self, email_doc_id: int) -> None:
        """Removes the reminder date from a specific email by setting it to None.

        :param email_doc_id: The document ID of the email to clear the reminder from.
        """
        self.emails_table.update({"reminder_date": None}, doc_ids=[email_doc_id])

    def close_db(self) -> None:
        """Closes the database connection."""
        self.db.close()
