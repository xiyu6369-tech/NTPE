from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RuntimeCapability:
    name: str
    stable: bool = True
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeContract:
    """Formal NTPE 1.2 Professional Translation Runtime contract.

    The contract is additive and is used by launchers, TXT runtime, batch runtime,
    tests, and future SDK/UI layers to verify that a runtime instance keeps the
    public surface introduced during NTPE 1.2 Stage-01.
    """

    version: str
    root: str
    entrypoints: tuple[str, ...]
    pipeline: tuple[str, ...]
    capabilities: tuple[RuntimeCapability, ...]
    compatibility_floor: str = "1.1-lts-stable"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["entrypoints"] = list(self.entrypoints)
        payload["pipeline"] = list(self.pipeline)
        payload["capabilities"] = [capability.to_dict() for capability in self.capabilities]
        return payload


REQUIRED_ENTRYPOINTS: tuple[str, ...] = (
    "translate_package_file",
    "translate_package",
    "translate_txt",
    "translate_batch",
    "main_txt",
    "main_batch",
)

OFFICIAL_PIPELINE: tuple[str, ...] = (
    "Encoding",
    "Chunk",
    "Context",
    "Glossary",
    "Character Memory",
    "Prompt Builder",
    "AI Provider",
    "QA",
    "Taiwan Formatter",
    "Output",
)

RUNTIME_CAPABILITIES: tuple[RuntimeCapability, ...] = (
    RuntimeCapability("package_translation", True, "Translate prompt package JSON files through TranslationEngine."),
    RuntimeCapability("txt_translation", True, "Translate a single TXT through the unified runtime facade."),
    RuntimeCapability("batch_translation", True, "Translate multiple TXT files through the unified runtime facade."),
    RuntimeCapability("encoding_normalization", True, "Read common Korean/Chinese encodings and normalize line endings."),
    RuntimeCapability("chunking", True, "Split long-form text into stable translation chunks."),
    RuntimeCapability("taiwan_formatter", True, "Normalize punctuation and common Taiwan Traditional Chinese variants."),
    RuntimeCapability("lts_compatibility", True, "Keep NTPE 1.1 LTS TXT and batch runtime contracts callable."),
)


def build_runtime_contract(version: str, root: str | Path) -> RuntimeContract:
    return RuntimeContract(
        version=version,
        root=str(Path(root)),
        entrypoints=REQUIRED_ENTRYPOINTS,
        pipeline=OFFICIAL_PIPELINE,
        capabilities=RUNTIME_CAPABILITIES,
    )


def validate_runtime_contract(runtime: Any) -> dict[str, Any]:
    missing = [name for name in REQUIRED_ENTRYPOINTS if not callable(getattr(runtime, name, None))]
    contract = build_runtime_contract(getattr(runtime, "version", "unknown"), getattr(runtime, "root", Path.cwd()))
    return {
        "status": "success" if not missing else "failed",
        "version": contract.version,
        "compatibility_floor": contract.compatibility_floor,
        "missing_entrypoints": missing,
        "pipeline": list(contract.pipeline),
        "capabilities": [capability.to_dict() for capability in contract.capabilities],
    }
