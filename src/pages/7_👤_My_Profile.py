import streamlit as st

from utils.time import set_runtime_tz
from utils.ui import render_settings_sidebar

# Page config must be first
st.set_page_config(page_title="My Profile", page_icon="👤", layout="wide")

# Ensure the db_handler is initialized from the Home page
if "db_handler" not in st.session_state:
    st.error("Database handler not initialized. Please go to the Home page first.")
    st.stop()

# Access the handler from session state
db = st.session_state.db_handler

# Apply saved timezone + show settings sidebar
tz_saved = db.get_timezone()
if tz_saved:
    set_runtime_tz(tz_saved)
render_settings_sidebar(db)

st.title("👤 My Profile & Signature")
st.write("Set up your personal information. This will be used to populate your sender details and email signature.")
st.divider()

# --- Load existing profile data ---
user_profile = db.get_user_profile() or {}

# --- Profile Form ---
with st.form("my_profile_form"):
    st.subheader("Your Information")
    name = st.text_input(
        "Full Name",
        value=user_profile.get("name", ""),
        placeholder="Your Name",
    )
    title = st.text_input(
        "Your Title",
        value=user_profile.get("title", ""),
        placeholder="e.g., Founder, Software Engineer",
    )
    profession = st.text_input(
        "Your Profession",
        value=user_profile.get("profession", ""),
        placeholder="e.g., Technology, Healthcare",
    )

    st.subheader("Social Media (Optional)")
    linkedin = st.text_input(
        "LinkedIn Profile URL",
        value=user_profile.get("linkedin", ""),
        placeholder="https://www.linkedin.com/in/your-handle",
    )
    twitter = st.text_input(
        "Twitter/X Profile URL",
        value=user_profile.get("twitter", ""),
        placeholder="https://x.com/your-handle",
    )
    github = st.text_input(
        "GitHub Profile URL",
        value=user_profile.get("github", ""),
        placeholder="https://github.com/your-handle",
    )

    st.subheader("Email Signature")
    signature = st.text_area(
        "Signature",
        value=user_profile.get("signature", "Best regards,\n\n"),
        height=150,
        help="Tip: You can reference your name/title manually here, or keep it generic.",
    )

    submitted = st.form_submit_button("Save Profile")
    if submitted:
        profile_data = {
            "name": name,
            "title": title,
            "profession": profession,
            "linkedin": linkedin,
            "twitter": twitter,
            "github": github,
            "signature": signature,
        }
        db.update_user_profile(profile_data)
        st.success("✅ Your profile has been saved successfully!")
