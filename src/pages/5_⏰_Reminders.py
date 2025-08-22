from datetime import datetime

import streamlit as st

from utils.time import (
    get_app_tz,
    parse_iso_to_local,
    set_runtime_tz,
)
from utils.ui import render_settings_sidebar

# Page config must come first
st.set_page_config(page_title="Follow-Up Reminders", page_icon="⏰", layout="wide")

# Init DB
if "db_handler" not in st.session_state:
    st.error("Database handler not initialized. Please go to the Home page first.")
    st.stop()
db = st.session_state.db_handler

# Apply saved timezone + sidebar
tz_saved = db.get_timezone()
if tz_saved:
    set_runtime_tz(tz_saved)
render_settings_sidebar(db)

st.title("⏰ Follow-Up Reminders")
st.write("Review your sent emails and set reminders to follow up. Your upcoming reminders are listed at the top.")
st.divider()

# Data
all_emails = db.emails_table.all()
all_profiles = db.get_all_profiles()
profile_id_map = {p.doc_id: p for p in all_profiles}

emails_with_reminders = [e for e in all_emails if e.get("reminder_date")]

# Allow reminders for 'sent' and 'partial' (not already having a reminder)
sent_emails_without_reminders = [
    e for e in all_emails
    if e.get("status") in ("sent", "partial") and not e.get("reminder_date")
]

# Sort upcoming reminders by date (stored as YYYY-MM-DD)
try:
    sorted_reminders = sorted(
        emails_with_reminders,
        key=lambda e: datetime.fromisoformat(e["reminder_date"]),
    )
except Exception as e:
    st.error(f"Error sorting reminders: {e}")
    sorted_reminders = []

# Use app timezone for today's date
local_today = datetime.now(get_app_tz()).date()

# SECTION 1: Display Upcoming Reminders
st.subheader("🔔 Upcoming Reminders")
if not sorted_reminders:
    st.info("You have no pending reminders.")
else:
    for reminder_email in sorted_reminders:
        reminder_id = reminder_email.doc_id
        reminder_dt = datetime.fromisoformat(reminder_email["reminder_date"])
        reminder_day = reminder_dt.date()

        is_due = reminder_day <= local_today
        icon = "❗️" if is_due else "⏳"

        recipient_ids = reminder_email.get("recipients", [])
        recipient_names = [profile_id_map.get(rid, {}).get("name", "Unknown") for rid in recipient_ids]

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f"{icon} **{reminder_day.strftime('%B %d, %Y')}**: "
                f"Follow up on '{reminder_email['subject']}' with **{', '.join(recipient_names)}**.",
            )
        with col2:
            if st.button("Clear Reminder", key=f"clear_{reminder_id}", help="Remove this reminder"):
                db.clear_email_reminder(reminder_id)
                st.rerun()

st.divider()

# SECTION 2: Set Reminders from Sent Email History
st.subheader("📜 Sent Email History")
st.write("Set a reminder for any email you've already sent.")

if not sent_emails_without_reminders:
    st.info("No sent emails available to set reminders for.")
else:
    for email in sent_emails_without_reminders:
        email_id = email.doc_id
        sent_local = parse_iso_to_local(email.get("sent_time"))  # UTC->local
        sent_label = sent_local.strftime("%Y-%m-%d %H:%M") if sent_local else "—"

        recipient_ids = email.get("recipients", [])
        recipient_names = [profile_id_map.get(rid, {}).get("name", "Unknown") for rid in recipient_ids]

        with st.expander(f"Email to **{', '.join(recipient_names)}** on {sent_label} — Subject: {email['subject']}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                reminder_day = st.date_input(
                    "Set follow-up date",
                    min_value=local_today,
                    key=f"date_{email_id}",
                )
            with col2:
                st.write("")
                st.write("")
                if st.button("Set Reminder", key=f"set_{email_id}"):
                    db.set_email_reminder(email_id, reminder_day)
                    st.rerun()
