from datetime import datetime, timezone

import markdown


def filter_nl2br(value: str) -> str:
    """
    Jinja Filter to convert newlines to <br> tags.
    """
    return value.replace("\n", "<br>")


def filter_humanize(dt: datetime | str | int | None) -> str:
    """
    Jinja Filter to convert datetime to human readable string.

    Args:
        dt (datetime | str | None): datetime object or string.

    Returns:
        str: pretty string like 'an hour ago', 'Yesterday',
            '3 months ago', 'just now', etc
    """
    if not dt:
        return ""

    if isinstance(dt, str):
        try:
            # Handle ISO format strings, including those with 'Z' for UTC
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            try:
                # Fallback for other common formats like YYYY-MM-DD HH:MM:SS
                dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                return ""  # Silently fail on unparsable strings
    elif isinstance(dt, int):
        try:
            dt = datetime.fromtimestamp(dt, tz=timezone.utc)
        except (ValueError, TypeError):
            return ""

    if not isinstance(dt, datetime):
        return ""

    # Assume naive datetimes are UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    diff = now - dt
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ""

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return f"{int(second_diff)} seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return f"{int(second_diff / 60)} minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return f"{int(second_diff / 3600)} hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return f"{day_diff} days ago"
    if day_diff < 14:
        return "a week ago"
    if day_diff < 31:
        return f"{int(day_diff / 7)} weeks ago"
    if day_diff < 365:
        return f"{int(day_diff / 30)} months ago"
    return f"{int(day_diff / 365)} years ago"


def format_date(value: datetime | None) -> str:
    """Format date to YYYY-MM-DD."""
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d")


def filter_markdown(text: str) -> str:
    """
    Jinja Filter to convert markdown to html.
    """
    return str(markdown.markdown(text, extensions=["nl2br"]))
