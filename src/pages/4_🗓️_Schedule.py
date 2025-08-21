import os
from datetime import datetime, timedelta
from typing import Any

import streamlit as st

from utils.time import get_app_tz, parse_iso_to_local, set_runtime_tz
from utils.ui import render_settings_sidebar

# Page config must be first
st.set_page_config(page_title="Email Schedule", page_icon="🗓️", layout="wide")

# Init DB
if "db_handler" not in st.session_state:
    st.error("Database handler not initialized. Please go to the Home page first.")
    st.stop()
db = st.session_state.db_handler

# TZ + settings
tz_saved = db.get_timezone()
if tz_saved:
    set_runtime_tz(tz_saved)
render_settings_sidebar(db)

st.title("🗓️ Email Schedule")
st.write("View all your scheduled emails. The sending process happens in the background.")
st.divider()

Document = dict[str, Any]

def status_badge(status: str) -> str:
    s = (status or "").lower()
    return {
        "sent": "✅ **sent**",
        "partial": "🟡 **partial**",
        "failed": "❌ **failed**",
        "scheduled": "🕒 **scheduled**",
    }.get(s, f"**{status}**")

def dt_local(s: str | None) -> datetime | None:
    return parse_iso_to_local(s)

def display_delivery_log(email: Document) -> None:
    deliveries = db.get_deliveries_for_campaign(email.doc_id)
    if not deliveries:
        st.info("No delivery entries for this campaign yet.")
        return
    st.write("**Delivery log:**")
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
            + (f" · error: `{rerr}`" if rerr and rerr != "—" else "")
        )

# ---------------- Scheduled Queue ----------------
scheduled_emails = db.get_scheduled_emails()
all_profiles = db.get_all_profiles()
profile_id_map = {p.doc_id: p for p in all_profiles}

# Sort by local schedule time for user-friendly order
sorted_scheduled = sorted(
    scheduled_emails,
    key=lambda e: dt_local(e.get("schedule_time")) or datetime.max.replace(tzinfo=get_app_tz()),
)

st.subheader("📤 Scheduled Queue")
if not sorted_scheduled:
    st.info("No emails are currently scheduled.")
else:
    st.caption(f"{len(sorted_scheduled)} email(s) in the queue.")
    for email in sorted_scheduled:
        email_id = email.doc_id  # ensure we have a stable id for widget keys
        sched_local = dt_local(email.get("schedule_time"))
        now_local = datetime.now(get_app_tz())
        relative = ""
        if sched_local:
            diff = sched_local - now_local
            if diff.total_seconds() > 0:
                days, hours = diff.days, diff.seconds // 3600
                relative = f"in {days} day(s), {hours} hour(s)"
            else:
                ago = timedelta(seconds=abs(diff.total_seconds()))
                days, hours = ago.days, ago.seconds // 3600
                relative = f"{days} day(s), {hours} hour(s) ago"

        recipient_ids = email.get("recipients", [])
        recipient_names = [profile_id_map.get(rid, {}).get("name", "Unknown Profile") for rid in recipient_ids]
        counts = email.get("counts", {}) or {}
        sent_c = counts.get("sent", 0)
        failed_c = counts.get("failed", 0)
        pending_c = counts.get("pending", 0)
        total_c = counts.get("total", len(recipient_ids))

        header = f"**{email.get('subject', 'No Subject')}** — {status_badge(email.get('status'))}"
        header += f" · {sent_c} sent · {failed_c} failed · {pending_c} pending / {total_c}"
        if sched_local:
            header += f" · **{sched_local.strftime('%B %d, %Y at %I:%M %p')}** ({relative})"

        with st.expander(header):
            st.markdown(f"**To:** {', '.join(recipient_names)}")
            attachments = email.get("attachments", [])
            if attachments:
                filenames = [os.path.basename(p) for p in attachments]
                st.markdown(f"**Attachments:** {', '.join(filenames)}")
            st.text_area(
                "Body",
                value=email.get("body", ""),
                height=150,
                disabled=True,
                key=f"scheduled_body_{email_id}",  # unique key
            )
            if st.button("🗑️ Cancel Schedule", key=f"cancel_{email_id}", help="Permanently delete pending deliveries in this campaign"):
                db.delete_scheduled_email(email_id)
                st.rerun()

st.divider()

# ---------------- Recently Completed ----------------
st.subheader("✅ Recently Completed Jobs")
completed = [
    e for e in db.emails_table.all()
    if e.get("status") in ("sent", "partial", "failed")
]
# Sort by local sent time for consistency with TZ
completed_sorted = sorted(
    completed,
    key=lambda e: dt_local(e.get("sent_time")) or datetime.min.replace(tzinfo=get_app_tz()),
    reverse=True,
)[:10]

if not completed_sorted:
    st.info("No completed jobs found yet.")
else:
    for email in completed_sorted:
        email_id = email.doc_id  # define the id here too
        sent_local = dt_local(email.get("sent_time"))
        when = sent_local.strftime("%B %d, %Y at %I:%M %p") if sent_local else "—"

        recipient_ids = email.get("recipients", [])
        recipient_names = [profile_id_map.get(rid, {}).get("name", "Unknown Profile") for rid in recipient_ids]
        counts = email.get("counts", {}) or {}
        sent_c = counts.get("sent", 0)
        failed_c = counts.get("failed", 0)
        total_c = counts.get("total", len(recipient_ids))

        header = f"**{email.get('subject', 'No Subject')}** — {status_badge(email.get('status'))} · {when}"
        header += f" · {sent_c} sent · {failed_c} failed / {total_c}"

        with st.expander(header):
            st.markdown(f"**To:** {', '.join(recipient_names)}")
            st.text_area(
                "Body",
                value=email.get("body", ""),
                height=150,
                disabled=True,
                key=f"completed_body_{email_id}",  # unique key
            )
            with st.expander("Delivery Log"):
                display_delivery_log(email)
