from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException

from app import settings


def restrict_to(*allowed_types: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to restrict access to certain ENV_NAMEs. For instance, you can restrict access to only the 'production'
    and 'staging' ENV_NAMEs by passing 'production' and 'staging' to the decorator.

    Args:
        *allowed_types: List of allowed ENV_NAMEs.

    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: Decorator function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if settings.ENV_NAME not in allowed_types and settings.ENV_NAME != "dev":
                raise HTTPException(
                    status_code=403,
                    detail=f"Restricted. ENV_NAME '{settings.ENV_NAME}' is not allowed. Allowed types: {allowed_types}. Use the @restrict_to('{settings.ENV_NAME}') decorator to restrict access to certain ENV_NAMEs.",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
