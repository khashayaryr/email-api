import datetime
import os
import uuid

import streamlit as st

from utils.helpers import render_email_body
from utils.time import set_runtime_tz
from utils.ui import render_settings_sidebar

# --- Page Configuration (must be the first Streamlit call) ---
st.set_page_config(page_title="Compose & Send", page_icon="✉️", layout="wide")

# --- Init DB handler ---
if "db_handler" not in st.session_state:
    st.error("Database handler not initialized. Please go to the Home page first.")
    st.stop()
db = st.session_state.db_handler  # now we have db

# --- Settings sidebar & timezone (requires db) ---
tz_saved = db.get_timezone()
if tz_saved:
    set_runtime_tz(tz_saved)  # runtime override only (no env writes)
render_settings_sidebar(db)

# --- Attachments setup ---
ATTACHMENTS_DIR = "attachments"
if not os.path.exists(ATTACHMENTS_DIR):
    os.makedirs(ATTACHMENTS_DIR)

# --- Data Loading ---
st.title("✉️ Compose & Send")
st.write("Select recipients, choose a template or write a custom email, and schedule it for sending.")
all_profiles = db.get_all_profiles()
all_templates = db.get_all_templates()
my_profile = db.get_user_profile()

if not all_profiles or not my_profile:
    st.warning("Please ensure both contact profiles and your own profile are set up before composing.")
    st.stop()

profile_map_by_name = {f"{p['name']} ({p['email']})": p for p in all_profiles}
template_map = {t["name"]: t for t in all_templates}
template_names = ["-- Write from scratch --"] + list(template_map.keys())

# --- Session State ---
if "email_subject" not in st.session_state:
    st.session_state.email_subject = ""
if "email_body" not in st.session_state:
    st.session_state.email_body = ""

def on_template_change():
    selected_template_name = st.session_state.get("template_selector", "-- Write from scratch --")
    if selected_template_name != "-- Write from scratch --":
        template = template_map[selected_template_name]
        st.session_state.email_subject = template.get("subject", "")
        st.session_state.email_body = template.get("body", "")
    else:
        st.session_state.email_subject = ""
        st.session_state.email_body = ""

# --- SECTION 1: CORE EMAIL CONTENT (REACTIVE) ---
st.selectbox("Select a Template (Optional)", options=template_names, key="template_selector", on_change=on_template_change)
selected_profile_names = st.multiselect("Select Recipients", options=list(profile_map_by_name.keys()))
st.text_input("Subject", key="email_subject")
st.write("---")

# --- SECTION 2: EDITOR AND PREVIEW (REACTIVE) ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Email Editor")
    st.text_area("Body", height=450, key="email_body")
    add_signature = st.toggle("Add signature to email", value=True)
    uploaded_files = st.file_uploader("Attach files", accept_multiple_files=True)
with col2:
    st.subheader("Live Preview")
    if not selected_profile_names:
        st.info("Select one or more recipients to see a live preview.")
    else:
        tab_names = [name.split(" (")[0].strip() for name in selected_profile_names]
        recipient_tabs = st.tabs(tab_names)
        for i, tab in enumerate(recipient_tabs):
            with tab:
                current_recipient_name = selected_profile_names[i]
                current_recipient_profile = profile_map_by_name[current_recipient_name]
                preview_content = render_email_body(
                    body_template=st.session_state.email_body,
                    recipient_profile=current_recipient_profile,
                    sender_profile=my_profile,
                    include_signature=add_signature,
                )
                st.markdown(f"**To:** {current_recipient_profile['name']} <{current_recipient_profile['email']}>")
                st.markdown(f"**Subject:** {st.session_state.email_subject}")
                st.divider()
                with st.container(border=True, height=450):
                    st.text(preview_content)

st.write("---")

# --- SECTION 3: SCHEDULING AND REMINDERS (REACTIVE) ---
st.subheader("Scheduling & Reminders")

schedule_date = st.date_input("1. Choose Schedule Date", min_value=datetime.date.today())

set_reminder_toggle = st.toggle("2. Set a Follow-up Reminder (Optional)")
reminder_date_input = None
if set_reminder_toggle:
    min_reminder_date = schedule_date + datetime.timedelta(days=1)
    reminder_date_input = st.date_input(
        "Remind me on:",
        value=min_reminder_date,
        min_value=min_reminder_date,
    )

st.divider()

# --- SECTION 4: FINAL ACTION FORM ---
with st.form("action_form"):
    st.markdown("**3. Set Time and Submit**")
    schedule_time = st.time_input("Schedule Time", value=datetime.time(9, 0), label_visibility="collapsed")

    submit_col1, submit_col2 = st.columns(2)
    with submit_col1:
        schedule_button = st.form_submit_button("🗓️ Schedule for Later", use_container_width=True)
    with submit_col2:
        send_now_button = st.form_submit_button("✉️ Send Now", type="primary", use_container_width=True)

    if schedule_button or send_now_button:
        subject = st.session_state.email_subject
        body = st.session_state.email_body
        if not selected_profile_names or not subject or not body:
            st.error("Please select recipients and ensure the subject and body are not empty.")
        else:
            attachment_paths = []
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    unique_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
                    save_path = os.path.join(ATTACHMENTS_DIR, unique_filename)
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    attachment_paths.append(save_path)

            recipient_doc_ids = [profile_map_by_name[name].doc_id for name in selected_profile_names]

            if send_now_button:
                schedule_datetime = datetime.datetime.now()
                action_text = "queued for immediate sending"
            else:
                schedule_datetime = datetime.datetime.combine(schedule_date, schedule_time)
                action_text = f"scheduled for {schedule_datetime.strftime('%Y-%m-%d %H:%M')}"

            reminder_to_save = reminder_date_input if set_reminder_toggle else None

            db.schedule_email(
                subject=subject,
                body=body,
                recipients=recipient_doc_ids,
                schedule_time=schedule_datetime,  # DB layer converts to UTC
                sender_profile=my_profile,
                add_signature=add_signature,
                attachments=attachment_paths,
                reminder_date=reminder_to_save,
            )

            success_message = f"✅ Successfully {action_text}! ({len(recipient_doc_ids)} email(s))"
            if reminder_to_save:
                success_message += f" with a reminder set for {reminder_to_save.strftime('%Y-%m-%d')}."
            st.success(success_message)
