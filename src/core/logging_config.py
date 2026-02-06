"""
Centralized logging configuration for EON Discord Bot

Usage:
    from core.logging_config import get_logger

    logger = get_logger(__name__)
    logger.info("Bot started")
    logger.warning("Missing API key")
    logger.error("Failed to connect", exc_info=True)
"""

import logging
import os
import sys
from typing import Optional
from logging.handlers import RotatingFileHandler


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


def setup_logging(
    log_level: Optional[str] = None,
    log_to_file: bool = True,
    log_file_path: Optional[str] = None
) -> None:
    """
    Configure logging for the entire application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  Defaults to DEBUG if DEBUG_MODE env var is set, else INFO
        log_to_file: Whether to log to file in addition to console
        log_file_path: Path to log file (defaults to logs/eon_bot.log)
    """
    # Determine log level
    if log_level is None:
        debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        log_level = "DEBUG" if debug_mode else "INFO"

    # Get numeric log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    console_format = ColoredFormatter(
        '%(asctime)s %(levelname)-8s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler (rotating)
    if log_to_file:
        if log_file_path is None:
            # Default to logs/eon_bot.log
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            project_root = os.path.dirname(script_dir)
            logs_dir = os.path.join(project_root, "logs")

            # Create logs directory if it doesn't exist
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)

            log_file_path = os.path.join(logs_dir, "eon_bot.log")

        # Rotating file handler (max 10MB, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)

        file_format = logging.Formatter(
            '%(asctime)s %(levelname)-8s [%(name)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)

    # Reduce noise from discord.py and other libraries
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.INFO)

    # Log the logging setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_to_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Usage:
        logger = get_logger(__name__)
        logger.info("Message")

    Args:
        name: Usually __name__ of the calling module

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Convenience function for backward compatibility with print-style debugging
def debug_print(*args, **kwargs):
    """
    DEPRECATED: Use logger.debug() instead.
    Temporary function to ease migration from print() to logging.
    """
    logger = logging.getLogger('debug_print')
    message = ' '.join(str(arg) for arg in args)
    logger.debug(message)
