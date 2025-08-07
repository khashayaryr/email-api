from datetime import datetime, timedelta
from typing import Any

import streamlit as st

from utils.db import DatabaseHandler

# A type alias for a TinyDB Document for cleaner annotations
Document = dict[str, Any]

# --- Page Config and DB Initialization ---
st.set_page_config(
    page_title="Email Assistant Dashboard",
    page_icon="👋",
    layout="wide",
)

if "db_handler" not in st.session_state:
    st.session_state.db_handler = DatabaseHandler(db_file="db.json")

db: DatabaseHandler = st.session_state.db_handler

st.title("👋 Welcome to your AI Email Assistant!")
st.sidebar.success("Select a page above to get started.")
st.markdown(
    """
    This is your central dashboard for managing your professional outreach.
    From here, you can get a quick overview of your email activities.
    """,
)
st.divider()

# --- Data Loading and Preparation ---
# Load all necessary data once at the start for efficiency
all_emails: list[Document] = db.emails_table.all()
all_profiles: list[Document] = db.get_all_profiles()
profile_id_map: dict[int, Document] = {p.doc_id: p for p in all_profiles}

# --- Statistics Calculation ---
now: datetime = datetime.now()
thirty_days_ago: datetime = now - timedelta(days=30)

# 1. Emails Sent (Last 30 Days)
sent_emails: list[Document] = [e for e in all_emails if e.get("status") == "sent"]
sent_last_30_days: list[Document] = [
    e for e in sent_emails
    if e.get("sent_time") and datetime.fromisoformat(e["sent_time"]) >= thirty_days_ago
]
sent_count: int = len(sent_last_30_days)

# 2. Emails Scheduled
scheduled_count: int = len([e for e in all_emails if e.get("status") == "scheduled"])

# 3. Upcoming Reminders
upcoming_reminders: list[Document] = [
    e for e in all_emails
    if e.get("reminder_date") and datetime.fromisoformat(e["reminder_date"]).date() >= now.date()
]
reminders_count: int = len(upcoming_reminders)


# --- UI Display ---
st.header("📊 Dashboard")

# --- Dynamic Statistics ---
st.subheader("At a Glance")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Emails Sent (Last 30 Days)", value=sent_count)
with col2:
    st.metric(label="Emails Scheduled", value=scheduled_count)
with col3:
    st.metric(label="Upcoming Reminders", value=reminders_count)

st.divider()


def display_email_entry(email: Document, profile_map: dict[int, Document]) -> None:
    """Renders a single email entry in a standardized format for the dashboard.

    :param email: The email document object from the database.
    :param profile_map: A dictionary mapping profile document IDs to profile documents.
    """
    recipient_ids: list[int] = email.get("recipients", [])
    recipient_names: list[str] = [
        profile_map.get(rid, {}).get("name", "Unknown") for rid in recipient_ids
    ]

    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**To:** `{', '.join(recipient_names)}`")
            st.markdown(f"**Subject:** {email.get('subject', 'No Subject')}")
        with col2:
            if email.get("status") == "sent" and email.get("sent_time"):
                sent_time_str = datetime.fromisoformat(email["sent_time"]).strftime("%b %d, %Y")
                st.write(f"Sent: {sent_time_str}")
            elif email.get("status") == "scheduled" and email.get("schedule_time"):
                schedule_time_str = datetime.fromisoformat(email["schedule_time"]).strftime("%b %d, %Y")
                st.write(f"Sends: {schedule_time_str}")

        with st.expander("View Body"):
            st.text(email.get("body", "No content available."))


# --- Functional Search Bar ---
st.subheader("Search Sent Emails")
search_query: str = st.text_input(
    "Search by keyword in subject or body",
    key="search_home",
    label_visibility="collapsed",
)
if search_query:
    search_results: list[Document] = db.search_emails(search_query)
    st.write(f"Found **{len(search_results)}** result(s) for '{search_query}':")
    if not search_results:
        st.info("No matching emails found.")
    else:
        for result in search_results:
            display_email_entry(result, profile_id_map)

# --- Dynamic Recent Activity ---
st.subheader("🕒 Recent Activity (Last 5 Sent)")
# Sort sent emails by date, most recent first
sorted_sent_emails: list[Document] = sorted(
    sent_emails, key=lambda e: e.get("sent_time", ""), reverse=True,
)

if not sorted_sent_emails:
    st.info("No emails have been sent yet.")
else:
    # Display the top 5 most recent
    for email in sorted_sent_emails[:5]:
        display_email_entry(email, profile_id_map)
