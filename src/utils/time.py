import os
from datetime import UTC, datetime, timezone
from zoneinfo import ZoneInfo

_DEF_TZ = "Europe/Rome"  # default local timezone for UI and for naive inputs
_RUNTIME_TZ: str | None = None  # in-process override (no env mutation)

def set_runtime_tz(tzname: str | None) -> None:
    """Set a process-local timezone override (preferred over env)."""
    global _RUNTIME_TZ
    _RUNTIME_TZ = tzname if tzname else None

def _env_tzname() -> str:
    # Read from dotenv-loaded environment, fallback to default
    return os.getenv("APP_TIMEZONE", _DEF_TZ)

def get_app_tz() -> ZoneInfo | timezone:
    """Resolve the app's local timezone: runtime override → env → UTC fallback."""
    tzname = _RUNTIME_TZ or _env_tzname()
    try:
        return ZoneInfo(tzname)
    except Exception:
        return UTC  # safe fallback

def now_utc() -> datetime:
    return datetime.now(UTC)

def now_utc_iso() -> str:
    # Store with trailing 'Z' for UTC clarity
    return now_utc().isoformat().replace("+00:00", "Z")

def to_utc_iso(dt: datetime) -> str:
    """Convert a datetime to UTC ISO string (with 'Z').
    If 'dt' is naive, interpret it in the app timezone first.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=get_app_tz())
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")

def parse_iso_to_utc(s: str | None) -> datetime | None:
    """Parse any ISO string (with or without 'Z') to an aware UTC datetime."""
    if not s:
        return None
    s2 = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s2)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)

def parse_iso_to_local(s: str | None) -> datetime | None:
    """Parse ISO string to a datetime in the app timezone (aware)."""
    utc_dt = parse_iso_to_utc(s)
    if not utc_dt:
        return None
    return utc_dt.astimezone(get_app_tz())
