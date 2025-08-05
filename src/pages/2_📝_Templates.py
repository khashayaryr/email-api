import streamlit as st

# Ensure the db_handler is initialized from the Home page
if "db_handler" not in st.session_state:
    st.error("Database handler not initialized. Please go to the Home page first.")
    st.stop()

# Access the handler from session state
db = st.session_state.db_handler

st.set_page_config(page_title="Email Templates", page_icon="📝")

st.title("📝 Email Templates")
st.write("Create and manage reusable email templates to speed up your workflow.")

# --- Form to Create a New Template ---
with st.expander("➕ Create New Template", expanded=False):
    with st.form("new_template_form", clear_on_submit=True):
        st.subheader("Enter Template Details")
        template_name = st.text_input("Template Name", placeholder="e.g., 'Initial Outreach'")
        subject = st.text_input("Email Subject", placeholder="e.g., 'Quick Question'")
        body = st.text_area("Email Body", height=250, placeholder="""Hi {name},

I came across your profile and was impressed by your work in {profession}.

I'd love to connect.

Best,
{signature}""")

        st.info(
            """You can use placeholders like `{name}`, `{title}`, `{profession}` in the body.
            These will be filled automatically when you compose an email."""
        )

        submitted = st.form_submit_button("Save Template")
        if submitted:
            # Basic validation
            if template_name and subject and body:
                # Call the database handler method
                success = db.add_template(name=template_name, subject=subject, body=body)
                if success:
                    st.success(f"✅ Template '{template_name}' saved successfully!")
                else:
                    st.warning(f"⚠️ A template with the name '{template_name}' already exists.")
            else:
                st.error("❌ All fields (Template Name, Subject, Body) are required.")

# --- Display Existing Templates ---
st.write("---")
st.subheader("Saved Templates")

all_templates = db.get_all_templates()

if not all_templates:
    st.info("No templates found. Create a new template using the form above.")
else:
    # Display each template in its own expander
    for template in all_templates:
        template_id = template.doc_id
        with st.expander(f"**{template.get('name')}**"):
            st.write(f"**Subject:** {template.get('subject')}")
            # Use a markdown block for better formatting of the body
            st.markdown("**Body:**")
            st.code(template.get("body"), language="text")

            # Delete button for each template
            if st.button("🗑️ Delete Template", key=f"delete_template_{template_id}", help="Delete this template"):
                db.delete_template(template_id)
                st.rerun() # Refresh the page to update the list
