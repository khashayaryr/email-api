import os
from zoneinfo import ZoneInfo

import streamlit as st

from utils.time import set_runtime_tz  # NEW

COMMON_TZS = [
    "Europe/Rome",
    "UTC",
    "Europe/London",
    "Europe/Paris",
    "America/New_York",
    "America/Los_Angeles",
    "Asia/Tehran",
    "Asia/Dubai",
    "Asia/Tokyo",
    "Asia/Kolkata",
    "Australia/Sydney",
]

def render_settings_sidebar(db) -> None:
    """Tiny settings sidebar for app timezone, persisted in TinyDB."""
    with st.sidebar.expander("⚙️ Settings", expanded=False):
        saved_tz = db.get_timezone() or os.getenv("APP_TIMEZONE") or "Europe/Rome"

        # Ensure current process uses the saved timezone immediately
        set_runtime_tz(saved_tz)

        st.caption("Local Timezone (for display and interpreting naive inputs)")
        default_index = COMMON_TZS.index(saved_tz) if saved_tz in COMMON_TZS else 0
        choice = st.selectbox("Timezone", COMMON_TZS, index=default_index, key="tz_choice")
        custom = st.text_input("Custom IANA timezone (optional)", placeholder="e.g., Europe/Berlin", key="tz_custom")

        if st.button("Save timezone"):
            tzname = (custom or choice).strip()
            try:
                ZoneInfo(tzname)  # validate
                db.set_timezone(tzname)
                set_runtime_tz(tzname)  # immediate effect, no env mutation
                st.success(f"Timezone set to {tzname}.")
                st.rerun()
            except Exception:
                st.error("Invalid timezone. Use a valid IANA name like Europe/Berlin.")
