from typing import Any


def get_form_str(form_data: dict[str, Any], key: str, default: str = "") -> str:
    """Get string value from form data with proper type handling."""
    value = form_data.get(key, default)
    return str(value) if value is not None else default


def get_form_float(form_data: dict[str, Any], key: str, default: float = 0.0) -> float:
    """Get float value from form data with proper type handling."""
    try:
        value = form_data.get(key, str(default))
        return float(str(value)) if value else default
    except (ValueError, TypeError):
        return default


def get_form_int(form_data: dict[str, Any], key: str, default: int = 0) -> int:
    """Get integer value from form data with proper type handling."""
    try:
        value = form_data.get(key, str(default))
        return int(str(value)) if value else default
    except (ValueError, TypeError):
        return default
