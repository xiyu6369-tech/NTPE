from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

MANIFEST_FILE = Path(__file__).with_name("foundation_manifest_v1.json")

REQUIRED_KEYS = {
    "name",
    "foundation_version",
    "status",
    "api_level",
    "compatibility",
    "contracts",
    "foundation_series",
    "policy",
}

REQUIRED_CONTRACTS = {
    "runtime_contract",
    "context_pipeline_contract",
    "prompt_pipeline_contract",
    "plugin_contract",
    "production_pipeline_contract",
    "translation_runtime_contract",
    "intelligence_contract",
    "knowledge_contract",
    "snapshot_contract",
}


def load_foundation_manifest(path: str | Path | None = None) -> Dict[str, Any]:
    target = Path(path) if path else MANIFEST_FILE
    with target.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_foundation_manifest(manifest: Dict[str, Any] | None = None) -> bool:
    data = manifest or load_foundation_manifest()
    if not REQUIRED_KEYS.issubset(data.keys()):
        return False
    if data.get("foundation_version") != "1.0":
        return False
    if data.get("status") != "Frozen":
        return False
    contracts = data.get("contracts", {})
    if not REQUIRED_CONTRACTS.issubset(contracts.keys()):
        return False
    return all(value == "Frozen" for value in contracts.values())


def get_foundation_manifest() -> Dict[str, Any]:
    return load_foundation_manifest()


def get_frozen_contracts() -> Dict[str, str]:
    return dict(load_foundation_manifest().get("contracts", {}))
