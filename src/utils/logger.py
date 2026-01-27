# src/utils/logger.py
"""
Logging configuration and utilities.
"""

import logging
import logging.config
from config.settings import LOGGING_CONFIG


def setup_logging():
    """
    Configure logging for the application.
    """
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
