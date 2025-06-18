import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar


T = TypeVar("T")


def allow_sync(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to run an async function synchronously if called from sync code, or return a coroutine if called from async code."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            # If we're in an event loop, return the coroutine for the caller to await
            asyncio.get_running_loop()
            return func(*args, **kwargs)
        except RuntimeError:
            # No running event loop, so run the coroutine to completion
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(func(*args, **kwargs))
            finally:
                loop.close()

    return wrapper


def allow_sync_func(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run an async function synchronously without using a decorator.

    This utility allows running any async function in a synchronous context
    by managing the event loop internally.

    Args:
        func: The async function to run
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the async function

    Example:
        async def my_async_function(x: int) -> int:
            return x + 1

        # Run the async function synchronously
        result = allow_sync_func(my_async_function, 5)  # Returns 6
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Create new event loop if one doesn't exist
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Check if we're already in an event loop
    try:
        asyncio.get_running_loop()
        # We're in an event loop, so we need to create a new one
        new_loop = asyncio.new_event_loop()
        return new_loop.run_until_complete(func(*args, **kwargs))
    except RuntimeError:
        # No running loop, use the current one
        return loop.run_until_complete(func(*args, **kwargs))
