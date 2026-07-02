from __future__ import annotations

from dataclasses import dataclass, asdict
from importlib import import_module
from pathlib import Path
from typing import Dict, Any, List

FOUNDATION_COMPATIBILITY_MODULES: Dict[str, str] = {
    "runtime": "core.runtime",
    "context_pipeline": "core.context",
    "prompt_pipeline": "core.prompt_builder",
    "plugin_system": "core.plugins",
    "production_pipeline": "core.production",
    "translation_runtime": "core.translation",
    "intelligence": "core.intelligence",
    "knowledge": "core.knowledge",
}

@dataclass
class CompatibilityCheckResult:
    name: str
    passed: bool
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _module_or_path_exists(module_name: str) -> bool:
    try:
        import_module(module_name)
        return True
    except Exception:
        parts = module_name.split(".")
        root = Path.cwd().joinpath(*parts)
        return root.exists()


def check_component_compatibility(name: str, module_name: str) -> CompatibilityCheckResult:
    ok = _module_or_path_exists(module_name)
    return CompatibilityCheckResult(
        name=name,
        passed=ok,
        detail="available" if ok else f"missing: {module_name}",
    )


def check_foundation_compatibility() -> List[CompatibilityCheckResult]:
    return [
        check_component_compatibility(name, module_name)
        for name, module_name in FOUNDATION_COMPATIBILITY_MODULES.items()
    ]


def build_compatibility_report() -> Dict[str, Any]:
    results = check_foundation_compatibility()
    return {
        "foundation_version": "1.0",
        "status": "Frozen",
        "passed": all(r.passed for r in results),
        "results": [r.to_dict() for r in results],
    }


def is_foundation_compatible() -> bool:
    return bool(build_compatibility_report()["passed"])
