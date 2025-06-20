from datetime import datetime, timezone


def filter_humanize_network(dt: datetime | str | None) -> str:
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
        if second_diff < 300:
            return "recently"
        if second_diff < 3600:
            return f"{int(second_diff / 60)}m ago"
        if second_diff < 86400:
            return f"{int(second_diff / 3600)}h ago"
    if day_diff < 7:
        return f"{day_diff}d ago"
    if day_diff < 14:
        return f"{int(day_diff / 7)}w ago"
    return "long ago"


from datetime import datetime


def filter_humanize_network_text_color(dt: datetime | str | None) -> str:
    """ """
    humanized_text = filter_humanize_network(dt)
    if humanized_text == "recently":
        return "text-success"
    if "m ago" in humanized_text or "h ago" in humanized_text:
        return "text-warning"
    return "text-danger"
