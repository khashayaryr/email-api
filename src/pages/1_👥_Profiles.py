import streamlit as st

from utils.time import set_runtime_tz
from utils.ui import render_settings_sidebar

st.set_page_config(page_title="Contact Profiles", page_icon="👥")

if "db_handler" not in st.session_state:
    st.error("Database handler not initialized. Please go to the Home page first.")
    st.stop()

db = st.session_state.db_handler

# TZ + settings sidebar
tz_saved = db.get_timezone()
if tz_saved:
    set_runtime_tz(tz_saved)
render_settings_sidebar(db)

st.title("👥 Contact Profiles")
st.write("Manage the profiles of people you want to email. You can add, edit, or delete profiles here.")

# --- Form to Add a New Profile ---
with st.expander("➕ Add New Profile", expanded=False):
    with st.form("new_profile_form", clear_on_submit=True):
        st.subheader("Enter Profile Details")
        name = st.text_input("Name", placeholder="e.g., Jane Doe")
        email = st.text_input("Email", placeholder="e.g., jane.doe@example.com")
        title = st.text_input("Title", placeholder="e.g., Professor")
        profession = st.text_input("Profession", placeholder="e.g., Head of Marketing")

        submitted = st.form_submit_button("Add Profile")
        if submitted:
            if name and email:
                success = db.add_profile(name=name, email=email, title=title, profession=profession)
                if success:
                    st.success(f"✅ Profile for '{name}' added successfully!")
                else:
                    st.warning(f"⚠️ A profile with the email '{email}' already exists.")
            else:
                st.error("❌ Name and Email are required fields.")

# --- Display Existing Profiles ---
st.write("---")
st.subheader("Existing Profiles")

all_profiles = db.get_all_profiles()

if not all_profiles:
    st.info("No profiles found. Add a new profile using the form above.")
else:
    col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])
    with col1: st.write("**Name**")
    with col2: st.write("**Email**")
    with col3: st.write("**Title**")
    with col4: st.write("**Profession**")
    with col5: st.write("**Actions**")

    st.markdown("---")

    for profile in all_profiles:
        profile_id = profile.doc_id
        col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])

        with col1: st.write(profile.get("name", "N/A"))
        with col2: st.write(profile.get("email", "N/A"))
        with col3: st.write(profile.get("title", "N/A"))
        with col4: st.write(profile.get("profession", "N/A"))
        with col5:
            if st.button("🗑️", key=f"delete_{profile_id}", help="Delete this profile"):
                db.delete_profile(profile_id)
                st.rerun()
