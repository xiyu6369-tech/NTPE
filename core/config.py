from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from core.exceptions import ConfigError


ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "app_name": "NTPE",
    "version": "1.0 Beta 1 Base",
    "provider": "nvidia",
    "api_key": "",
    "model": "meta/llama-3.3-70b-instruct",
    "timeout": 180,
    "rpm_limit": 40,
    "chunk_size": 3000,
    "context_size": 800,
    "target_language": "zh-TW",
    "opencc": True,
    "auto_retry": True,
    "auto_review": False,
}


def ensure_config() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not DEFAULT_CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)


def load_config(path: Path | None = None) -> Dict[str, Any]:
    config_path = path or DEFAULT_CONFIG_PATH
    ensure_config()
    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        raise ConfigError(f"設定檔讀取失敗：{config_path}") from exc

    merged = DEFAULT_CONFIG.copy()
    merged.update(data)
    return merged


def save_config(config: Dict[str, Any], path: Path | None = None) -> None:
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
