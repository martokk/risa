from typing import Any

from loguru import logger as _logger

from app.models.settings import Settings
from app.paths import ERROR_LOG_FILE, LOG_FILE


def setup_logger(settings: Settings) -> Any:
    """Configure and return the application logger."""

    # Configure loggers for file output
    _logger.add(
        LOG_FILE,
        filter=lambda record: record["extra"].get("name") == "logger",
        level=settings.LOG_LEVEL,
        rotation="10 MB",
    )
    _logger.add(
        ERROR_LOG_FILE,
        filter=lambda record: record["extra"].get("name") == "logger",
        level="ERROR",
        rotation="10 MB",
    )
    # Create bound logger
    logger = _logger.bind(name="logger")
    logger.info(f"Log level set by .env to '{settings.LOG_LEVEL}'")

    return logger
