from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app import models


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


def format_currency(value: float | int | None) -> str:
    """Format number as currency."""
    if value is None:
        return "0.00"
    try:
        # Convert to float if it's a string
        if isinstance(value, str):
            value = float(value)
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return "0.00"


def active_status(status: Enum) -> str:
    """Get Bootstrap color class for organization status."""
    if status.value == "Active":
        return "success"
    return "secondary"


def status_color(status: models.GrantCycleStatus) -> str:
    """Get Bootstrap color class for grant cycle status."""
    colors = {
        models.GrantCycleStatus.DIDNT_APPLY: "secondary",
        models.GrantCycleStatus.IN_PROGRESS: "primary",
        models.GrantCycleStatus.SUBMITTED: "info",
        models.GrantCycleStatus.AWARDED: "success",
        models.GrantCycleStatus.REJECTED: "danger",
    }
    return colors.get(status, "secondary")


def verification_color(verification: models.DateVerification) -> str:
    """Get Bootstrap color class for date verification status."""
    colors = {
        models.DateVerification.VERIFIED: "success",
        models.DateVerification.UNVERIFIED: "warning",
        models.DateVerification.UNKNOWN: "danger",
    }
    return colors.get(verification, "secondary")


def css_class_ss_status(status: models.GrantCycleStatus) -> str:
    """Get CSS class for grant cycle status."""
    colors = {
        models.GrantCycleStatus.DIDNT_APPLY: "status-didnt-apply",
        models.GrantCycleStatus.IN_PROGRESS: "status-in-progress",
        models.GrantCycleStatus.SUBMITTED: "status-submitted",
        models.GrantCycleStatus.AWARDED: "status-awarded",
        models.GrantCycleStatus.REJECTED: "status-rejected",
    }
    return colors.get(status, "status-unknown")


def css_class_ss_date(
    date: datetime | None,
    status: models.GrantCycleStatus,
    date_verification: models.DateVerification,
) -> str:
    """Get CSS class for date override."""
    css_class = []

    # Handle No Date
    if date is None:
        if date_verification == models.DateVerification.NOT_APPLICABLE:
            return ""
        if (
            status == models.GrantCycleStatus.DIDNT_APPLY
            or status == models.GrantCycleStatus.WONT_APPLY
        ):
            return ""
        if status == models.GrantCycleStatus.REJECTED:
            return ""
        return "date-missing"

    # # Handle Didnt Apply
    # if status == models.GrantCycleStatus.DIDNT_APPLY:
    #     return "status-didnt-apply"

    # Handle Dates
    now = datetime.now()
    diff = date - now

    # Handle Past Date
    if diff.days < 0:
        css_class.append("date-past")

    # Handle Soon Date
    if diff.days <= 10 and diff.days > 0:
        if status in [
            models.GrantCycleStatus.IN_PROGRESS,
            models.GrantCycleStatus.AWAITING,
        ]:
            css_class.append("date-soon")
        elif status in [models.GrantCycleStatus.SUBMITTED, models.GrantCycleStatus.AWARDED]:
            css_class.append("date-awaiting")

    # Handle Verification Status
    colors = {
        models.DateVerification.VERIFIED: "date-verified",
        models.DateVerification.UNVERIFIED: "date-unverified",
        models.DateVerification.NOT_APPLICABLE: "date-not-applicable",
        models.DateVerification.SPECULATIVE: "date-speculative",
        models.DateVerification.LIKELY: "date-likely",
        models.DateVerification.UNKNOWN: "date-unknown",
    }

    css_class.append(colors.get(date_verification, ""))
    return " ".join(css_class)


def css_class_missing_past_date(
    value: Any, status: models.GrantCycleStatus, date: datetime | None
) -> str:
    """Get CSS class for missing past date."""
    if date is None:
        return ""
    if (
        status == models.GrantCycleStatus.DIDNT_APPLY
        or status == models.GrantCycleStatus.WONT_APPLY
    ):
        return ""
    if status == models.GrantCycleStatus.REJECTED:
        return ""
    if not value:
        if status in [
            models.GrantCycleStatus.IN_PROGRESS,
            models.GrantCycleStatus.AWAITING,
            models.GrantCycleStatus.SUBMITTED,
            models.GrantCycleStatus.AWARDED,
        ]:
            if date < datetime.now():
                return "missing-past-date"
    return ""
