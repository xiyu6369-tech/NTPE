"""NTPE launcher.

Entry point for Novel Translator Professional Edition.
"""

from __future__ import annotations

import sys
from pathlib import Path

from config.config_manager import ConfigManager
from core.exceptions import NTPEError
from core.logger import setup_logger
from core.scheduler import RPMScheduler

VERSION = "0.1.1 Alpha"


def main() -> int:
    """Start NTPE foundation services."""
    project_root = Path(__file__).resolve().parent

    try:
        config_manager = ConfigManager(project_root)
        config = config_manager.load()

        logger = setup_logger(
            project_root=project_root,
            level=config_manager.get("logging.level", "INFO"),
            file_name=config_manager.get("logging.file_name", "ntpe.log"),
        )

        nvidia_rpm = int(config_manager.get("api.nvidia.rpm_limit", 38))
        gemini_rpm = int(config_manager.get("api.gemini.rpm_limit", 14))

        nvidia_scheduler = RPMScheduler("NVIDIA", nvidia_rpm)
        gemini_scheduler = RPMScheduler("Gemini", gemini_rpm)

        logger.info("NTPE launcher initialized")
        logger.info("Configuration loaded from %s", config_manager.user_config_path)
        logger.info("NVIDIA Scheduler: %s RPM", nvidia_scheduler.rpm_limit)
        logger.info("Gemini Scheduler: %s RPM", gemini_scheduler.rpm_limit)

        app_name = config.get("app", {}).get("short_name", "NTPE")
        print(f"{app_name} {VERSION} - Infrastructure OK")
        return 0

    except NTPEError as exc:
        print(f"NTPE startup failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # defensive guard for alpha stage
        print(f"Unexpected startup error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
