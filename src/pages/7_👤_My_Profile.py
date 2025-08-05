import streamlit as st

# Ensure the db_handler is initialized from the Home page
if "db_handler" not in st.session_state:
    st.error("Database handler not initialized. Please go to the Home page first.")
    st.stop()

# Access the handler from session state
db = st.session_state.db_handler

st.set_page_config(page_title="My Profile", page_icon="👤")

st.title("👤 My Profile & Signature")
st.write("Set up your personal information. This will be used to populate your sender details and email signature.")

# --- Load existing profile data ---
# The get_user_profile() method returns the single user profile document or None
user_profile = db.get_user_profile()
if user_profile is None:
    # If no profile exists, create an empty dictionary to avoid errors
    user_profile = {}

# --- Profile Form ---
# The form will be pre-filled with existing data
with st.form("my_profile_form"):
    st.subheader("Your Information")
    name = st.text_input(
        "Full Name",
        value=user_profile.get("name", ""),
        placeholder="Your Name",
    )
    # ... (other fields like title, profession) ...
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
    )
    twitter = st.text_input(
        "Twitter/X Profile URL",
        value=user_profile.get("twitter", ""),
    )
    # --- 1. ADD THE NEW GITHUB FIELD HERE ---
    github = st.text_input(
        "GitHub Profile URL",
        value=user_profile.get("github", ""),
    )

    st.subheader("Email Signature")
    signature = st.text_area(
        "Signature",
        value=user_profile.get("signature", "Best regards,\n\n"),
        height=150,
    )

    submitted = st.form_submit_button("Save Profile")
    if submitted:
        # Package all the data into a dictionary
        profile_data = {
            "name": name,
            "title": title,
            "profession": profession,
            "linkedin": linkedin,
            "twitter": twitter,
            # --- 2. ADD GITHUB TO THE DICTIONARY TO BE SAVED ---
            "github": github,
            "signature": signature,
        }
        # Call the database handler method to save the data
        db.update_user_profile(profile_data)
        st.success("✅ Your profile has been saved successfully!")

