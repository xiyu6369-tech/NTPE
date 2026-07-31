"""Interactive Provider Environment Setup for NTPE.

This tool helps users set provider API keys without editing source code. It does
not modify Translation Runtime or Provider Runtime files.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent.parent
PROVIDER_CONFIG = ROOT / "config" / "provider_config.json"
TEMPLATE_PATH = ROOT / "config" / "provider_environment_template.env"


def load_providers() -> dict[str, dict]:
    with PROVIDER_CONFIG.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    providers = data.get("providers", {})
    if not isinstance(providers, dict) or not providers:
        raise RuntimeError("No providers found in config/provider_config.json")
    return providers


def export_template() -> Path:
    providers = load_providers()
    lines = [
        "# NTPE Provider Environment Template",
        "# Fill values locally only. Do not commit real API keys.",
        "",
    ]
    for provider, config in sorted(providers.items()):
        env_var = config.get("env_var")
        if env_var:
            lines.append(f"{env_var}=")
    TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return TEMPLATE_PATH


def set_current_process(env_var: str, value: str) -> None:
    os.environ[env_var] = value


def set_windows_user_env(env_var: str, value: str) -> None:
    if os.name != "nt":
        raise RuntimeError("Permanent setup uses Windows setx and is only available on Windows.")
    subprocess.run(["setx", env_var, value], check=True)


def choose_provider(providers: dict[str, dict]) -> str:
    names = list(providers.keys())
    print("NTPE Provider Setup")
    print("===================")
    for idx, name in enumerate(names, 1):
        env_var = providers[name].get("env_var", "")
        print(f"{idx}. {name} ({env_var})")
    choice = input("請選擇 Provider：").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(names):
        return names[int(choice) - 1]
    if choice in providers:
        return choice
    raise SystemExit("Invalid provider selection")


def interactive_setup() -> int:
    providers = load_providers()
    provider = choose_provider(providers)
    env_var = providers[provider].get("env_var")
    if not env_var:
        raise SystemExit(f"Provider has no env_var: {provider}")
    value = input(f"請輸入 {provider.upper()} API Key：").strip()
    if not value:
        raise SystemExit("API Key cannot be empty")
    print("1. 僅目前執行程序")
    print("2. 永久寫入 Windows 使用者環境變數")
    mode = input("請選擇：").strip()
    if mode == "2":
        set_windows_user_env(env_var, value)
        print(f"{env_var} saved with setx. Please reopen CMD before running NTPE.")
    else:
        set_current_process(env_var, value)
        print(f"{env_var} set for this setup process. For CMD usage, run: set {env_var}=你的APIKEY")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Set up NTPE provider API key environment variables.")
    parser.add_argument("--export", action="store_true", help="write config/provider_environment_template.env")
    args = parser.parse_args(argv)
    if args.export:
        path = export_template()
        print(f"Template written: {path}")
        return 0
    return interactive_setup()


if __name__ == "__main__":
    raise SystemExit(main())
