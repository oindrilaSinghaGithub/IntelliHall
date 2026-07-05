"""
IntelliHall — Logging Configuration

Configures Python's standard logging module.
Log level is controlled by the LOG_LEVEL environment variable (default: INFO).
"""

import logging
import sys


def configure_logging() -> None:
    """Set up application-wide logging with a structured console handler."""

    log_level_str = "INFO"

    # Import lazily to avoid circular imports at startup
    try:
        from app.core.config import settings  # noqa: PLC0415
        log_level_str = settings.LOG_LEVEL
    except Exception:
        pass

    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid adding duplicate handlers if called multiple times
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
