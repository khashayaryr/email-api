import os
from datetime import datetime

import streamlit as st

# --- Page Configuration and Initialization ---
st.set_page_config(page_title="Email Schedule", page_icon="🗓️", layout="wide")

if "db_handler" not in st.session_state:
    st.error("Database handler not initialized. Please go to the Home page first.")
    st.stop()

db = st.session_state.db_handler
st.title("🗓️ Email Schedule")
st.write("View all your scheduled emails. The sending process will happen in the background.")
st.divider()

# --- Data Loading and Preparation ---
scheduled_emails = db.get_scheduled_emails()
all_profiles = db.get_all_profiles()

# Create a lookup dictionary for profile IDs to names for efficient access
profile_id_map = {p.doc_id: p for p in all_profiles}

# Sort emails by schedule time, soonest first
# The time is stored as an ISO string, so we can parse it back to a datetime object
try:
    sorted_emails = sorted(
        scheduled_emails,
        key=lambda e: datetime.fromisoformat(e["schedule_time"]),
    )
except (TypeError, ValueError) as e:
    st.error(f"Error parsing schedule times: {e}. Some data might be corrupt.")
    sorted_emails = []


# --- Display Scheduled Emails ---
if not sorted_emails:
    st.info("No emails are currently scheduled.")
else:
    st.subheader(f"You have {len(sorted_emails)} email(s) in the queue.")

    # Display each scheduled email using an expander for a clean look
    for email in sorted_emails:
        email_id = email.doc_id

        # Format the schedule time for display
        schedule_time_obj = datetime.fromisoformat(email["schedule_time"])
        # Current time is August 4th, 2025. This will show how many hours/days until sending.
        time_diff = schedule_time_obj - datetime.now()
        relative_time = f"in {time_diff.days} days, {time_diff.seconds // 3600} hours" if time_diff.total_seconds() > 0 else "now"

        expander_title = f"**{email['subject']}** scheduled for **{schedule_time_obj.strftime('%B %d, %Y at %I:%M %p')}** ({relative_time})"

        with st.expander(expander_title):
            # Look up recipient names from their IDs
            recipient_ids = email.get("recipients", [])
            recipient_names = [
                profile_id_map.get(rid, {}).get("name", "Unknown Profile")
                for rid in recipient_ids
            ]

            st.markdown(f"**To:** {', '.join(recipient_names)}")

            # Display attachments, if any
            attachments = email.get("attachments", [])
            if attachments:
                # Show just the filename, not the full path
                attachment_filenames = [os.path.basename(p) for p in attachments]
                st.markdown(f"**Attachments:** {', '.join(attachment_filenames)}")

            # Show a snippet of the body
            st.text_area("Body Snippet", value=email["body"], height=150, disabled=True)

            # Add a cancel button
            if st.button("🗑️ Cancel Schedule", key=f"cancel_{email_id}", help="Permanently delete this scheduled email"):
                db.delete_scheduled_email(email_id)
                st.rerun() # Immediately refresh the page to reflect the change
