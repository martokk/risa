from datetime import UTC, datetime


def filter_nl2br(value: str) -> str:
    """
    Jinja Filter to convert newlines to <br> tags.
    """
    return value.replace("\n", "<br>")


def filter_humanize(dt: datetime) -> str:
    """
    Jinja Filter to convert datetime to human readable string.

    Args:
        dt (datetime): datetime object.

    Returns:
        str: pretty string like 'an hour ago', 'Yesterday',
            '3 months ago', 'just now', etc
    """
    now = datetime.now(UTC)
    diff = now - dt
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ""

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(int(second_diff)) + " sec ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(int(second_diff / 60)) + " min ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(int(second_diff / 3600)) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 14:
        return str(int(day_diff / 7)) + " week ago"
    if day_diff < 31:
        return str(int(day_diff / 7)) + " weeks ago"
    if day_diff < 365:
        return str(int(day_diff / 30)) + " months ago"
    return str(int(day_diff / 365)) + " years ago"


def format_date(value: datetime | None) -> str:
    """Format date to YYYY-MM-DD."""
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d")
