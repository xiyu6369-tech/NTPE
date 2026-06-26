"""Logging utilities for NTPE."""

from __future__ import annotations

import logging
from pathlib import Path


_LOGGER_NAME = "ntpe"


def setup_logger(project_root: Path, level: str = "INFO", file_name: str = "ntpe.log") -> logging.Logger:
    """Create a console + file logger.

    The function is idempotent: repeated calls return the same configured logger
    without adding duplicate handlers.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    if logger.handlers:
        return logger

    logs_dir = project_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / file_name

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logger.level)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logger.level)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def get_logger() -> logging.Logger:
    """Return the NTPE logger."""
    return logging.getLogger(_LOGGER_NAME)
