from datetime import UTC, datetime

from app import settings


def parse_datetime(dt: str | datetime) -> datetime:
    """Convert string to datetime if needed."""
    if isinstance(dt, str):
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))
    return dt


def utc_to_local(dt: str | datetime) -> datetime:
    """Convert UTC datetime to local timezone."""
    dt = parse_datetime(dt)
    if dt.tzinfo is None:  # If naive datetime, assume it's UTC
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(settings.TIMEZONE_INFO)


def format_datetime(dt: str | datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime in local timezone."""
    local_dt = utc_to_local(dt)
    return local_dt.strftime(format)
