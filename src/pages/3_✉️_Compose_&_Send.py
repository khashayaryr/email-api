import datetime
import os
import uuid

import streamlit as st

# --- Page Configuration and Initialization ---
st.set_page_config(page_title="Compose & Send", page_icon="✉️", layout="wide")

# --- Create attachments directory if it doesn't exist ---
ATTACHMENTS_DIR = "attachments"
if not os.path.exists(ATTACHMENTS_DIR):
    os.makedirs(ATTACHMENTS_DIR)

# --- DB Handler and other initial setup (No changes) ---
if "db_handler" not in st.session_state:
    st.error("Database handler not initialized. Please go to the Home page first.")
    st.stop()
db = st.session_state.db_handler
st.title("✉️ Compose & Send")
st.write("Select recipients, choose a template or write a custom email, and schedule it for sending.")
all_profiles = db.get_all_profiles()
all_templates = db.get_all_templates()
my_profile = db.get_user_profile()
if not all_profiles:
    st.warning("No contact profiles found. Please add profiles on the 'Profiles' page first.")
    st.stop()
if not my_profile:
    st.warning("Your user profile is not set up. Please set it up on the 'My Profile' page.")
    st.stop()
profile_map_by_name = {f"{p['name']} ({p['email']})": p for p in all_profiles}
template_map = {t["name"]: t for t in all_templates}
template_names = ["-- Write from scratch --"] + list(template_map.keys())
if "email_subject" not in st.session_state:
    st.session_state.email_subject = ""
if "email_body" not in st.session_state:
    st.session_state.email_body = ""

# --- Helper functions (No changes) ---
def generate_preview(body_template, recipient_profile, sender_profile, include_signature):
    preview_text = body_template
    sender_data = {f"my_{key}": value for key, value in sender_profile.items()}
    all_placeholders = {**recipient_profile, **sender_data}
    for key, value in all_placeholders.items():
        preview_text = preview_text.replace(f"{{{key}}}", str(value))
    if include_signature:
        signature = sender_profile.get("signature", "")
        preview_text = f"{preview_text}\n\n--\n{signature}"
    return preview_text

def on_template_change():
    selected_template_name = st.session_state.get("template_selector", "-- Write from scratch --")
    if selected_template_name != "-- Write from scratch --":
        template = template_map[selected_template_name]
        st.session_state.email_subject = template.get("subject", "")
        st.session_state.email_body = template.get("body", "")
    else:
        st.session_state.email_subject = ""
        st.session_state.email_body = ""

# --- REACTIVE WIDGETS and TWO-COLUMN LAYOUT (No changes) ---
st.selectbox("Select a Template (Optional)", options=template_names, key="template_selector", on_change=on_template_change)
selected_profile_names = st.multiselect("Select Recipients", options=list(profile_map_by_name.keys()))
st.text_input("Subject", key="email_subject")
st.write("---")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Email Editor")
    with st.container(height=650, border=True):
        st.text_area("Body", height=400, key="email_body")
        add_signature = st.toggle("Add signature to email", value=True)
        st.divider()
        uploaded_files = st.file_uploader("Attach files", accept_multiple_files=True)
with col2:
    st.subheader("Live Preview")
    with st.container(height=650, border=True):
        if not selected_profile_names:
            st.info("Select one or more recipients to see a live preview.")
        else:
            tab_names = [name.split(" (")[0].strip() for name in selected_profile_names]
            recipient_tabs = st.tabs(tab_names)
            for i, tab in enumerate(recipient_tabs):
                with tab:
                    current_recipient_name = selected_profile_names[i]
                    current_recipient_profile = profile_map_by_name[current_recipient_name]
                    preview_content = generate_preview(st.session_state.email_body, current_recipient_profile, my_profile, add_signature)
                    st.markdown(f"**To:** {current_recipient_profile['name']} <{current_recipient_profile['email']}>")
                    st.markdown(f"**Subject:** {st.session_state.email_subject}")
                    st.divider()
                    with st.container(border=False, height=450):
                        st.text(preview_content)
st.write("---")


# --- FINAL ACTION FORM ---
with st.form("schedule_form"):
    st.subheader("Action")

    # Scheduling options are here
    sched_col1, sched_col2 = st.columns(2)
    with sched_col1:
        st.markdown("**Schedule for Later**")
        schedule_date = st.date_input("Date", min_value=datetime.date.today(), label_visibility="collapsed")
    with sched_col2:
        st.markdown("**&nbsp;**") # Empty markdown for alignment
        schedule_time = st.time_input("Time", value=datetime.time(9, 0), label_visibility="collapsed")

    st.divider()

    # --- NEW: Two submit buttons for two different actions ---
    submit_col1, submit_col2 = st.columns(2)
    with submit_col1:
        schedule_button = st.form_submit_button("🗓️ Schedule for Later", use_container_width=True)
    with submit_col2:
        send_now_button = st.form_submit_button("✉️ Send Now", type="primary", use_container_width=True)

    # --- NEW: Unified submission logic ---
    if schedule_button or send_now_button:
        # This code runs if EITHER button is clicked
        subject = st.session_state.email_subject
        body = st.session_state.email_body

        if not selected_profile_names:
            st.error("Please select at least one recipient.")
        elif not subject or not body:
            st.error("Subject and Body cannot be empty.")
        else:
            # Prepare data common to both actions
            attachment_paths = []
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    unique_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
                    save_path = os.path.join(ATTACHMENTS_DIR, unique_filename)
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    attachment_paths.append(save_path)

            recipient_doc_ids = [profile_map_by_name[name].doc_id for name in selected_profile_names]

            # Determine the schedule time based on which button was pressed
            if send_now_button:
                schedule_datetime = datetime.datetime.now()
                action_text = "queued for immediate sending"
            else: # schedule_button was pressed
                schedule_datetime = datetime.datetime.combine(schedule_date, schedule_time)
                action_text = f"scheduled for {schedule_datetime.strftime('%Y-%m-%d %H:%M')}"

            # Call the database once with the correct data
            db.schedule_email(
                subject=subject, body=body, recipients=recipient_doc_ids,
                schedule_time=schedule_datetime, sender_profile=my_profile,
                add_signature=add_signature, attachments=attachment_paths,
            )

            st.success(f"✅ Successfully {action_text}! ({len(recipient_doc_ids)} email(s))")
