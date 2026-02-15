"""
Logging configuration for HYPHA SDK

Provides centralized logging setup with consistent formatting
and configurable log levels.
"""

import logging
import sys
import os


def setup_logging(level: str = None, format_string: str = None) -> logging.Logger:
    """
    Configure HYPHA logging

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Defaults to LOG_LEVEL env var or INFO
        format_string: Custom format string for log messages

    Returns:
        Configured logger instance
    """
    # Get log level from env or parameter
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO')

    # Create logger
    logger = logging.getLogger('hypha')
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    # Create formatter
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


# Create default logger instance
logger = setup_logging()


def set_log_level(level: str):
    """
    Change log level at runtime

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger.setLevel(getattr(logging, level.upper()))
    for handler in logger.handlers:
        handler.setLevel(getattr(logging, level.upper()))
