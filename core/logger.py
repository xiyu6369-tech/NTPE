from __future__ import annotations

import logging
from pathlib import Path
from datetime import datetime


ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT_DIR / "logs"


def setup_logger(name: str = "ntpe") -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app_handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    app_handler.setFormatter(formatter)
    logger.addHandler(app_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def write_startup_log(logger: logging.Logger, version: str) -> None:
    logger.info("NTPE 啟動")
    logger.info("版本：%s", version)
    logger.info("啟動時間：%s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
