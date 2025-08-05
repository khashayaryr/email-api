from datetime import datetime

from tinydb import Query, TinyDB, where


class DatabaseHandler:
    """A class to handle all database operations with TinyDB for the Streamlit Email App.
    """

    def __init__(self, db_file="db.json"):
        """Initializes the database and creates tables if they don't exist.
        """
        self.db = TinyDB(db_file)
        self.profiles_table = self.db.table("profiles")
        self.templates_table = self.db.table("templates")
        self.user_profile_table = self.db.table("user_profile")
        self.emails_table = self.db.table("emails")

    # --- User Profile Methods ---
    def get_user_profile(self):
        """Retrieves the user's profile. Assumes only one user profile."""
        return self.user_profile_table.get(doc_id=1)

    def update_user_profile(self, data):
        """Creates or updates the user's profile.
        For a single-profile setup, we clear the table and insert the new profile.
        """
        # Clear the entire table first to ensure only one profile exists
        self.user_profile_table.truncate()
        # Insert the new profile data as the single document
        self.user_profile_table.insert(data)

    # --- Contact Profiles Methods ---
    def add_profile(self, name, email, title, profession):
        """Adds a new contact profile to the database."""
        if not self.profiles_table.contains(where("email") == email):
            self.profiles_table.insert({
                "name": name,
                "email": email,
                "title": title,
                "profession": profession,
            })
            return True
        return False # Profile with this email already exists

    def get_all_profiles(self):
        """Retrieves all contact profiles."""
        return self.profiles_table.all()

    def delete_profile(self, doc_id):
        """Deletes a contact profile by its document ID."""
        self.profiles_table.remove(doc_ids=[doc_id])

    # --- Email Templates Methods ---
    def add_template(self, name, subject, body):
        """Adds a new email template if the name doesn't already exist."""
        # Add a check for existing template name
        if not self.templates_table.contains(where("name") == name):
            self.templates_table.insert({"name": name, "subject": subject, "body": body})
            return True
        return False # Template with this name already exists

    def get_all_templates(self):
        """Retrieves all email templates."""
        return self.templates_table.all()

    def delete_template(self, doc_id):
        """Deletes a template by its document ID."""
        self.templates_table.remove(doc_ids=[doc_id])

    # --- Email Scheduling and History Methods ---
    def schedule_email(
        self, subject, body, recipients, schedule_time, sender_profile,
        add_signature=True, attachments=None,
    ):
        """Schedules an email to be sent, including attachments."""
        # Ensure attachments is a list if None is passed
        if attachments is None:
            attachments = []

        self.emails_table.insert({
            "subject": subject,
            "body": body,
            "recipients": recipients,
            "sender_profile": sender_profile,
            "status": "scheduled",
            "schedule_time": schedule_time.isoformat(),
            "sent_time": None,
            "reminder_date": None,
            "add_signature": add_signature,
            "attachments": attachments,  # <-- ADD THIS NEW FIELD
        })

    def get_scheduled_emails(self):
        """Retrieves all emails with 'scheduled' status."""
        Email = Query()
        return self.emails_table.search(Email.status == "scheduled")

    def delete_scheduled_email(self, email_doc_id):
        """Deletes an email from the emails_table by its document ID."""
        self.emails_table.remove(doc_ids=[email_doc_id])

    def get_sent_emails(self):
        """Retrieves all emails with 'sent' status."""
        Email = Query()
        return self.emails_table.search(Email.status == "sent")

    def search_emails(self, search_term):
        """Searches sent emails for a specific term in subject or body."""
        Email = Query()
        # A simple search query
        return self.emails_table.search(
            (Email.status == "sent") &
            ((Email.subject.search(search_term)) | (Email.body.search(search_term))),
        )

    # --- Reminder Methods ---
    def set_reminder(self, email_doc_id, reminder_date):
        """Sets a follow-up reminder for a sent email."""
        self.emails_table.update(
            {"reminder_date": reminder_date.isoformat()},
            doc_ids=[email_doc_id],
        )

    def get_reminders(self):
        """Retrieves all emails that have a reminder set."""
        Email = Query()
        return self.emails_table.search(Email.reminder_date.exists())

    def close_db(self):
        """Closes the database connection."""
        self.db.close()

    def get_due_emails(self):
        """Retrieves all emails with 'scheduled' status where the schedule_time is in the past.
        """
        Email = Query()
        now_iso = datetime.now().isoformat()
        # Find emails that are scheduled and whose schedule time is less than or equal to now
        return self.emails_table.search(
            (Email.status == "scheduled") & (Email.schedule_time <= now_iso),
        )

    def update_email_status(self, email_id, new_status):
        """Updates the status of an email (e.g., to 'sent') and records the sent time."""
        self.emails_table.update(
            {"status": new_status, "sent_time": datetime.now().isoformat()},
            doc_ids=[email_id],
        )
