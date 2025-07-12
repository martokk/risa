from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from app import settings
from vcore.backend.core import logger


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def get_api_key(api_key_header: Annotated[str | None, Security(api_key_header)]) -> str:
    """Validate API key from header.

    Args:
        api_key_header: API key from request header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not settings.EXPORT_API_KEY:
        logger.error("EXPORT_API_KEY is not set in environment variables")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export API key not configured",
        )

    # logger.debug(f"Received API key: {api_key_header}")
    if api_key_header == settings.EXPORT_API_KEY:
        return api_key_header

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )
