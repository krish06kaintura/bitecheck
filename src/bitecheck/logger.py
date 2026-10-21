"""
Structured Logging Module for BiteCheck India.
Provides contextual, formatted loggers across all multi-agent pipelines.
"""

import logging
import sys
from bitecheck.config import settings

# Standard log format showing timestamp, level, module, function name, line number, and message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_root_logger() -> None:
    """Configures the root logger with stdout handler and log level from settings."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Avoid duplicate handlers if already initialized
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT))
        root.addHandler(handler)
        root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance for a given module or agent name.
    
    Example usage:
        from bitecheck.logger import get_logger
        logger = get_logger("agent.auditor")
        logger.info("Audit initialized.")
    """
    setup_root_logger()
    return logging.getLogger(name)
