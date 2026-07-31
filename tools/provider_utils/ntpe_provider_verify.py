"""Verify NTPE provider configuration without running translation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent.parent
PROVIDER_CONFIG = ROOT / "config" / "provider_config.json"


def load_provider(provider: str) -> dict:
    with PROVIDER_CONFIG.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    providers = data.get("providers", {})
    config = providers.get(provider)
    if not isinstance(config, dict):
        raise RuntimeError(f"Provider not configured: {provider}")
    return config


def verify(provider: str = "nvidia", require_key: bool = True) -> int:
    print("NTPE Provider Verify")
    print("====================")
    config = load_provider(provider)
    env_var = config.get("env_var")
    model = config.get("default_model", "")
    if not env_var:
        print("Provider env_var .... FAIL")
        return 1
    value = os.getenv(env_var, "")
    print(f"Provider ............ {provider}")
    print(f"Default Model ....... {model or 'unset'}")
    print(f"Environment Variable  {env_var}")
    if value:
        print("API Key ............. PASS")
        print("OVERALL PASS")
        return 0
    status = "FAIL" if require_key else "WARN"
    print(f"API Key ............. {status}  {env_var} not set")
    print(f"OVERALL {status}")
    return 1 if require_key else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify NTPE provider env configuration.")
    parser.add_argument("--provider", default="nvidia")
    parser.add_argument("--allow-missing-key", action="store_true")
    args = parser.parse_args(argv)
    return verify(args.provider, require_key=not args.allow_missing_key)


if __name__ == "__main__":
    raise SystemExit(main())
