from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .classifier import classify_failure
from .decision import execution_decision
from .execution_policy import EXECUTION_POLICIES
from .failure_types import FAILURE_TYPES
from .review import summarize_execution
from .schema import SCHEMA_VERSION


COMPONENT_NAME = "provider_failure_characterization"
FREEZE_VERSION = "LCR-Batch-10.9"
TAXONOMY_VERSION = "1.0"
FREEZE_POLICY_VERSION = "1.0"
FROZEN_AT = "2026-07-18T14:36:34Z"

_SOURCE_HASHES = {
    "core/provider_failure_characterization/__init__.py": "39de85910f04fe66420c439666bfbc0efdf046d462dc5f1331d1c1dcafa7086f",
    "core/provider_failure_characterization/failure_types.py": "37aa82ecfe2d54b2d3472f5de6ae0fa8cc4cb81577e8b86eb94bdeb3707ec876",
    "core/provider_failure_characterization/classifier.py": "a3858bed7066c91938e220fa26761d471a125cd76f937a3638477ac7d462c286",
    "core/provider_failure_characterization/execution_policy.py": "9691b6d0acfe2a102c106a7dcdd5dea42f85cddd3ca02bf9fec9188ab2f1fd84",
    "core/provider_failure_characterization/decision.py": "37655b26a14b4d832985e0124fe904d54140fc980b4bedb3a7fa84fb77cb34bf",
    "core/provider_failure_characterization/review.py": "09eac83bd05bd3f494307eeba571b61fe4d5b2ca3473a11ea785b6b50116e205",
    "core/provider_failure_characterization/schema.py": "708b97d56a50466cf00154ac74e23623c2a8495a67d3b16837504dbc4f1b24d4",
}
FROZEN_SOURCE_HASHES: Mapping[str, str] = MappingProxyType(_SOURCE_HASHES)


@dataclass(frozen=True)
class ProviderFailurePolicyFreezeMetadata:
    component_name: str
    freeze_version: str
    schema_version: str
    taxonomy_version: str
    policy_version: str
    frozen_at: str
    public_api: tuple[str, ...]
    immutable_contracts: tuple[str, ...]
    failure_type_count: int
    retry_policy: str
    fallback_policy: str
    deterministic: bool
    read_only: bool
    production_integration_authorized: bool
    source_files: tuple[str, ...]
    source_hashes: Mapping[str, str]

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["source_hashes"] = dict(self.source_hashes)
        return value


_FREEZE_METADATA = ProviderFailurePolicyFreezeMetadata(
    component_name=COMPONENT_NAME,
    freeze_version=FREEZE_VERSION,
    schema_version=SCHEMA_VERSION,
    taxonomy_version=TAXONOMY_VERSION,
    policy_version=FREEZE_POLICY_VERSION,
    frozen_at=FROZEN_AT,
    public_api=("classify_failure", "execution_decision", "summarize_execution"),
    immutable_contracts=(
        "FailureType", "FailureExecutionPolicy", "ExecutionDecision", "ExecutionSummary",
    ),
    failure_type_count=19,
    retry_policy="forbidden",
    fallback_policy="forbidden",
    deterministic=True,
    read_only=True,
    production_integration_authorized=False,
    source_files=tuple(_SOURCE_HASHES),
    source_hashes=FROZEN_SOURCE_HASHES,
)


def get_provider_failure_policy_freeze_metadata() -> ProviderFailurePolicyFreezeMetadata:
    return _FREEZE_METADATA


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_provider_failure_policy_freeze(root: str | Path | None = None) -> tuple[str, ...]:
    base = Path(root).resolve() if root is not None else Path(__file__).resolve().parents[2]
    errors: list[str] = []
    if len(FAILURE_TYPES) != 19 or len(set(FAILURE_TYPES)) != 19:
        errors.append("failure_taxonomy_count_changed")
    if any(policy.retry_allowed for policy in EXECUTION_POLICIES.values()):
        errors.append("retry_policy_relaxed")
    if any(policy.fallback_allowed for policy in EXECUTION_POLICIES.values()):
        errors.append("fallback_policy_relaxed")
    if not all(callable(item) for item in (classify_failure, execution_decision, summarize_execution)):
        errors.append("public_api_unavailable")
    if _FREEZE_METADATA.production_integration_authorized:
        errors.append("production_integration_authorized")
    for relative, expected in FROZEN_SOURCE_HASHES.items():
        path = base / relative
        if not path.is_file():
            errors.append(f"frozen_source_missing:{relative}")
        elif _sha256_file(path) != expected:
            errors.append(f"frozen_source_hash_mismatch:{relative}")
    return tuple(errors)
