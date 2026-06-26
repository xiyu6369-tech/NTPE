from pathlib import Path

from core.config import load_config
from core.logger import setup_logger, write_startup_log
from core.utils import ensure_dirs


ROOT_DIR = Path(__file__).resolve().parent


def main() -> None:
    config = load_config()
    logger = setup_logger()

    ensure_dirs(
        ROOT_DIR / "logs",
        ROOT_DIR / "input",
        ROOT_DIR / "output",
        ROOT_DIR / "cache",
        ROOT_DIR / "data",
    )

    write_startup_log(logger, config.get("version", "unknown"))

    print("====================================")
    print(" NTPE 1.0 Beta 1 Base 啟動成功")
    print("====================================")
    print(f"Provider : {config.get('provider')}")
    print(f"Model    : {config.get('model')}")
    print(f"RPM      : {config.get('rpm_limit')}")
    print(f"Timeout  : {config.get('timeout')}")
    print("Logs     : logs/app.log")
    print("====================================")


if __name__ == "__main__":
    main()
