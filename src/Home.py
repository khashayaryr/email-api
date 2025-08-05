import streamlit as st

from utils.db import DatabaseHandler

# --- Initialize the Database Handler in Session State ---
if "db_handler" not in st.session_state:
    st.session_state.db_handler = DatabaseHandler(db_file="db.json")

st.set_page_config(
    page_title="Email Assistant Dashboard",
    page_icon="👋",
    layout="wide",
)

st.title("👋 Welcome to your AI Email Assistant!")

st.sidebar.success("Select a page above to get started.")

# ... (the rest of your Home.py code remains the same) ...
st.markdown(
    """
    This is your central dashboard for managing your professional outreach.
    From here, you can get a quick overview of your email activities.

    **👈 Select a feature from the sidebar** to:
    - Manage contact profiles
    - Create and use email templates
    - Compose and schedule new emails
    - View your email schedule and set reminders
    - Chat with your email history
    - Update your personal sending profile

    ---
    """,
)

st.header("📊 Dashboard")

# --- Placeholder for Search Bar ---
st.subheader("Search Sent Emails")
search_query = st.text_input("Search by keyword in subject or body", key="search_home")
if search_query:
    st.write(f"Searching for: **{search_query}**")
    # Here you would call your database handler to get search results
    # e.g., results = st.session_state.db_handler.search_emails(search_query)
    # and then display them.

# --- Placeholders for Statistics ---
st.subheader("Statistics")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Emails Sent (Last 30 Days)", value="123")
with col2:
    st.metric(label="Emails Scheduled", value="12")
with col3:
    st.metric(label="Upcoming Reminders", value="4")

# --- Placeholder for Recent Emails ---
st.subheader("🕒 Recent Activity")
st.write("A table or list of recently sent emails would appear here.")
st.dataframe({
    "To": ["John Doe", "Jane Smith"],
    "Subject": ["Following Up on our Meeting", "Project Proposal"],
    "Date Sent": ["2025-08-04", "2025-08-03"],
})
