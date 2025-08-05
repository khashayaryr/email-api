import streamlit as st

# Ensure the db_handler is initialized
if "db_handler" not in st.session_state:
    st.error("Database handler not initialized. Please go to the Home page first.")
    st.stop()

# Access the handler from session state
db = st.session_state.db_handler

st.set_page_config(page_title="Contact Profiles", page_icon="👥")

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
            # Basic validation
            if name and email:
                # Call the database handler method
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
    # Create columns for the header
    col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])
    with col1:
        st.write("**Name**")
    with col2:
        st.write("**Email**")
    with col3:
        st.write("**Title**")
    with col4:
        st.write("**Profession**")
    with col5:
        st.write("**Actions**")

    st.markdown("---")

    # Display each profile with a delete button
    for profile in all_profiles:
        profile_id = profile.doc_id
        col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])

        with col1:
            st.write(profile.get("name", "N/A"))
        with col2:
            st.write(profile.get("email", "N/A"))
        with col3:
            st.write(profile.get("title", "N/A"))
        with col4:
            st.write(profile.get("profession", "N/A"))
        with col5:
            # Use the profile's unique doc_id for the button key
            if st.button("🗑️", key=f"delete_{profile_id}", help="Delete this profile"):
                db.delete_profile(profile_id)
                st.rerun() # Rerun the script to refresh the list immediately
