from datetime import date, datetime

import streamlit as st

# --- Page Configuration and Initialization ---
st.set_page_config(page_title="Follow-Up Reminders", page_icon="⏰", layout="wide")

if "db_handler" not in st.session_state:
    st.error("Database handler not initialized. Please go to the Home page first.")
    st.stop()

db = st.session_state.db_handler
st.title("⏰ Follow-Up Reminders")
st.write("Review your sent emails and set reminders to follow up. Your upcoming reminders are listed at the top.")
st.divider()

# --- Data Loading ---
all_emails = db.emails_table.all()
all_profiles = db.get_all_profiles()
profile_id_map = {p.doc_id: p for p in all_profiles}

# Separate emails with reminders from those without
emails_with_reminders = [e for e in all_emails if e.get("reminder_date")]
sent_emails_without_reminders = [e for e in all_emails if e["status"] == "sent" and not e.get("reminder_date")]

# Sort upcoming reminders by date
try:
    sorted_reminders = sorted(
        emails_with_reminders,
        key=lambda e: datetime.fromisoformat(e["reminder_date"]),
    )
except Exception as e:
    st.error(f"Error sorting reminders: {e}")
    sorted_reminders = []


# --- SECTION 1: Display Upcoming Reminders ---
st.subheader("🔔 Upcoming Reminders")
if not sorted_reminders:
    st.info("You have no pending reminders.")
else:
    for reminder_email in sorted_reminders:
        reminder_id = reminder_email.doc_id
        reminder_date = datetime.fromisoformat(reminder_email["reminder_date"]).date()

        # Determine if the reminder is due
        is_due = reminder_date <= date.today()
        icon = "❗️" if is_due else "⏳"

        # Get recipient names
        recipient_ids = reminder_email.get("recipients", [])
        recipient_names = [profile_id_map.get(rid, {}).get("name", "Unknown") for rid in recipient_ids]

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f"{icon} **{reminder_date.strftime('%B %d, %Y')}**: Follow up on "
                f"'{reminder_email['subject']}' with **{', '.join(recipient_names)}**.",
            )
        with col2:
            if st.button("Clear Reminder", key=f"clear_{reminder_id}", help="Remove this reminder"):
                db.clear_email_reminder(reminder_id)
                st.rerun()

st.divider()


# --- SECTION 2: Set Reminders from Sent Email History ---
st.subheader("📜 Sent Email History")
st.write("Set a reminder for any email you've already sent.")

if not sent_emails_without_reminders:
    st.info("No sent emails available to set reminders for.")
else:
    for email in sent_emails_without_reminders:
        email_id = email.doc_id
        sent_time = datetime.fromisoformat(email["sent_time"]).strftime("%Y-%m-%d %H:%M")

        recipient_ids = email.get("recipients", [])
        recipient_names = [profile_id_map.get(rid, {}).get("name", "Unknown") for rid in recipient_ids]

        with st.expander(f"Email to **{', '.join(recipient_names)}** on {sent_time} - Subject: {email['subject']}"):

            col1, col2 = st.columns([2, 1])
            with col1:
                reminder_date = st.date_input(
                    "Set follow-up date",
                    min_value=date.today(),
                    key=f"date_{email_id}",
                )
            with col2:
                # Add a little space for alignment
                st.write("")
                st.write("")
                if st.button("Set Reminder", key=f"set_{email_id}"):
                    db.set_email_reminder(email_id, reminder_date)
                    st.rerun()
