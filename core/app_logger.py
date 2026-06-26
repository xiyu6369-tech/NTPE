"""
NTPE - Novel Translator Professional Edition
Version : 0.1.0 Alpha
File    : core/app_logger.py
Purpose : Application logging setup.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class AppLogger:
    """Create a reusable NTPE logger."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.log_dir = self.project_root / "logs"
        self.log_file = self.log_dir / "ntpe.log"

    def get_logger(self) -> logging.Logger:
        """Return configured application logger."""
        self.log_dir.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger("ntpe")
        logger.setLevel(logging.INFO)
        logger.propagate = False

        if logger.handlers:
            return logger

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        return logger
