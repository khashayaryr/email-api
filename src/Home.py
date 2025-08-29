"""Home (Dashboard) page for the Streamlit Email Assistant.

This module renders the main dashboard with:
- A hero image (if present at `src/pages/assets/home_hero.png`).
- A compact settings sidebar (timezone selection is wired via `render_settings_sidebar`).
- Key statistics (sent/scheduled/partial/failed counts and upcoming reminders).
- A searchable list of sent campaigns.
- A "recent activity" section with the latest completed campaigns.
- Per-campaign delivery logs (per-recipient outcomes).

It relies on:
- `utils.db.DatabaseHandler` (TinyDB) as the persistence layer.
- `utils.time` for timezone-aware conversions between stored UTC ISO strings and local time.
- `utils.ui` for the settings sidebar.

Notes
-----
- Time values are stored in UTC ISO strings (with "Z") and converted to the app's
  local timezone for display.
- Campaigns (rows in `emails` table) aggregate per-recipient deliveries (rows in
  `deliveries` table). Delivery logs shown here are derived from the deliveries.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import streamlit as st

from utils.db import DatabaseHandler
from utils.time import get_app_tz, parse_iso_to_local
from utils.ui import render_settings_sidebar

Document = dict[str, Any]

st.set_page_config(page_title="Email Assistant Dashboard", page_icon="👋", layout="wide")

if "db_handler" not in st.session_state:
    st.session_state.db_handler = DatabaseHandler(db_file="db.json")
db: DatabaseHandler = st.session_state.db_handler

# Apply saved TZ + sidebar
tz_saved = db.get_timezone()
if tz_saved:
    from utils.time import set_runtime_tz
    set_runtime_tz(tz_saved)
render_settings_sidebar(db)

st.title("👋 Welcome to your AI Email Assistant!")

assets_dir = Path(__file__).resolve().parent / "assets"
hero_path = assets_dir / "home_hero.png"

if hero_path.exists():
    # Center it nicely
    c1, c2, c3 = st.columns([1, 6, 1])
    with c2:
        st.image(str(hero_path), use_container_width=True)
else:
    st.info(f"Place a hero image at: {hero_path}")

st.sidebar.success("Select a page above to get started.")
st.markdown("This is your central dashboard for managing your professional outreach.")
st.divider()

all_emails: list[Document] = db.emails_table.all()
all_profiles: list[Document] = db.get_all_profiles()
profile_id_map: dict[int, Document] = {p.doc_id: p for p in all_profiles}

now_local: datetime = datetime.now(get_app_tz())
thirty_days_ago: datetime = now_local - timedelta(days=30)

def dt_local(s: str | None) -> datetime | None:
    """Convert a stored UTC ISO string to a timezone-aware local datetime.

    Parameters
    ----------
    s : str | None
        An ISO 8601 string (e.g., "2025-08-11T11:13:57.701269Z") or None.

    Returns
    -------
    datetime | None
        A timezone-aware datetime in the app's local timezone, or None if input is falsy/invalid.
    """
    return parse_iso_to_local(s)

sent_emails = [e for e in all_emails if e.get("status") == "sent"]
partial_emails = [e for e in all_emails if e.get("status") == "partial"]
failed_emails = [e for e in all_emails if e.get("status") == "failed"]
scheduled_emails = [e for e in all_emails if e.get("status") == "scheduled"]

sent_last_30_days = [e for e in sent_emails if (dt := dt_local(e.get("sent_time"))) and dt >= thirty_days_ago]
scheduled_count = len(scheduled_emails)

upcoming_reminders = [
    e for e in all_emails
    if e.get("reminder_date")
    and datetime.fromisoformat(e["reminder_date"]).date() >= now_local.date()
]
partial_last_30_days = [e for e in partial_emails if (dt := dt_local(e.get("sent_time"))) and dt >= thirty_days_ago]
failed_last_30_days = [e for e in failed_emails if (dt := dt_local(e.get("sent_time"))) and dt >= thirty_days_ago]

st.header("📊 Dashboard")
st.subheader("At a Glance")
col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.metric("Emails Sent (Last 30 Days)", len(sent_last_30_days))
with col2: st.metric("Emails Scheduled", scheduled_count)
with col3: st.metric("Upcoming Reminders", len(upcoming_reminders))
with col4: st.metric("Partial (Last 30 Days)", len(partial_last_30_days))
with col5: st.metric("Failed (Last 30 Days)", len(failed_last_30_days))
st.divider()

def status_badge(status: str) -> str:
    """Return a small Markdown badge for a campaign status.

    Parameters
    ----------
    status : str
        One of {"sent", "partial", "failed", "scheduled"} (case-insensitive). Any other
        string is returned in bold without an icon.

    Returns
    -------
    str
        A Markdown-formatted string with an icon + bolded status label.
    """
    s = (status or "").lower()
    return {"sent":"✅ **sent**","partial":"🟡 **partial**","failed":"❌ **failed**","scheduled":"🕒 **scheduled**"}.get(s, f"**{status}**")

def display_delivery_log(email: Document) -> None:
    """Render the per-recipient delivery log for a campaign.

    This function looks up all deliveries tied to the given campaign (email),
    sorts them by last attempt (or sent time), and prints a compact list with
    recipient, status, timestamp (local), and error (if any).

    Parameters
    ----------
    email : dict[str, Any]
        The campaign document (row from `emails` table) whose deliveries should be displayed.

    Returns
    -------
    None
        This function renders directly to the Streamlit app.
    """
    deliveries = db.get_deliveries_for_campaign(email.doc_id)
    if not deliveries:
        st.info("No delivery entries for this campaign yet.")
        return
    st.write("**Delivery log:**")
    # Show in attempt order (by last_attempt/sent_time)
    deliveries_sorted = sorted(
        deliveries,
        key=lambda d: d.get("last_attempt") or d.get("sent_time") or "",
    )
    for row in deliveries_sorted:
        snap = row.get("recipient_snapshot") or {}
        rname = snap.get("name") or "Unknown"
        remail = row.get("recipient_email") or "—"
        rstatus = row.get("status", "—")
        rtime_local = dt_local(row.get("sent_time") or row.get("last_attempt"))
        rtime_str = rtime_local.strftime("%Y-%m-%d %H:%M") if rtime_local else "—"
        rerr = row.get("error") or "—"
        st.markdown(
            f"- `{rname}` <{remail}> — **{rstatus}** at `{rtime_str}`"
            + (f" · error: `{rerr}`" if rerr and rerr != "—" else ""),
        )

def display_email_entry(email: Document, profile_map: dict[int, Document]) -> None:
    """Render a single campaign entry with recipients, subject, status, and body/log expanders.

    Parameters
    ----------
    email : dict[str, Any]
        The campaign (row from `emails` table) to display.
    profile_map : dict[int, dict[str, Any]]
        Mapping from profile doc_id to profile document; used to show recipient names.

    Returns
    -------
    None
        This function renders directly to the Streamlit app.
    """
    # Build recipient names from profiles for quick glance
    recipient_ids: list[int] = email.get("recipients", [])
    recipient_names: list[str] = [profile_map.get(rid, {}).get("name", "Unknown") for rid in recipient_ids]
    counts = email.get("counts", {}) or {}
    sent_c, failed_c, pending_c, total_c = counts.get("sent", 0), counts.get("failed", 0), counts.get("pending", 0), counts.get("total", len(recipient_ids))

    with st.container(border=True):
        c1, c2, c3 = st.columns([4,2,2])
        with c1:
            st.markdown(f"**To:** `{', '.join(recipient_names)}`")
            st.markdown(f"**Subject:** {email.get('subject', 'No Subject')}")
        with c2:
            st.markdown(f"Status: {status_badge(email.get('status'))}")
            st.caption(f"{sent_c} sent · {failed_c} failed · {pending_c} pending / {total_c}")
        with c3:
            label = ""
            if email.get("status") in ("sent", "partial", "failed"):
                dt = dt_local(email.get("sent_time"))
                label = f"Completed: {dt.strftime('%b %d, %Y')}" if dt else ""
            elif email.get("status") == "scheduled":
                dt = dt_local(email.get("schedule_time"))
                label = f"Sends: {dt.strftime('%b %d, %Y')}" if dt else ""
            if label: st.write(label)

        with st.expander("View Body"):
            st.text(email.get("body", "No content available."))
        with st.expander("Delivery Log"):
            display_delivery_log(email)

st.subheader("Search Sent Emails")
search_query: str = st.text_input("Search by keyword in subject or body", key="search_home", label_visibility="collapsed")
if search_query:
    results = db.search_emails(search_query)
    st.write(f"Found **{len(results)}** result(s) for '{search_query}':")
    if not results:
        st.info("No matching emails found.")
    else:
        for e in results:
            display_email_entry(e, profile_id_map)

st.subheader("🕒 Recent Activity (Last 5 Completed)")
completed = [e for e in all_emails if e.get("status") in ("sent", "partial", "failed")]
sorted_completed = sorted(completed, key=lambda e: e.get("sent_time", ""), reverse=True)
if not sorted_completed:
    st.info("No completed emails yet.")
else:
    for email in sorted_completed[:5]:
        display_email_entry(email, profile_id_map)
