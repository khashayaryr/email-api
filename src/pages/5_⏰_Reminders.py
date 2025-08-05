import streamlit as st

st.set_page_config(page_title="Follow-Up Reminders", page_icon="⏰")

st.title("⏰ Follow-Up Reminders")
st.write("After sending an email, you can set a reminder to follow up. View your upcoming reminders here.")

st.warning("A list of your pending reminders will be displayed here.")
# Placeholder for reminders list
st.dataframe({
    'Original Email To': ['John Doe'],
    'Original Subject': ['Following Up on our Meeting'],
    'Reminder Date': ['2025-08-10']
})