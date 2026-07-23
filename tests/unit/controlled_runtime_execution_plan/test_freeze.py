from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path, PurePosixPath

import pytest

import core.controlled_runtime_adapter as adapter
import core.controlled_runtime_execution_plan as execution_plan
import core.controlled_runtime_submission as submission
from core.controlled_runtime_execution_plan import (
    ControlledRuntimePreparationFreezeValidationError,
    get_controlled_runtime_preparation_freeze_metadata,
    validate_controlled_runtime_preparation_freeze,
)
from core.controlled_runtime_execution_plan import freeze


ROOT = Path(__file__).resolve().parents[3]


def test_metadata_is_frozen_complete_and_globally_disabled() -> None:
    metadata = get_controlled_runtime_preparation_freeze_metadata()
    assert metadata.component_name == "ntpe.controlled_runtime_preparation"
    assert metadata.freeze_version == "5.4"
    assert metadata.activation_gate == "controlled_runtime_preparation_frozen"
    assert (
        metadata.submission_schema_name,
        metadata.submission_schema_version,
    ) == ("ntpe.controlled_runtime_submission_package", "1.0")
    assert (metadata.adapter_schema_name, metadata.adapter_schema_version) == (
        "ntpe.controlled_runtime_adapter_request",
        "1.0",
    )
    assert (
        metadata.execution_plan_schema_name,
        metadata.execution_plan_schema_version,
    ) == ("ntpe.controlled_runtime_execution_plan", "1.0")
    assert isinstance(metadata.frozen_modules, tuple)
    assert isinstance(metadata.public_api, tuple)
    assert isinstance(metadata.invariants, tuple)
    boolean_values = (
        value
        for name, value in vars(metadata).items()
        if name.endswith("_authorized")
        or name.endswith("_enabled")
        or name == "production_integration_authorized"
    )
    assert not any(boolean_values)
    with pytest.raises(FrozenInstanceError):
        metadata.freeze_version = "changed"  # type: ignore[misc]


def test_public_api_inventory_is_exact_importable_unique_and_ordered() -> None:
    metadata = get_controlled_runtime_preparation_freeze_metadata()
    expected = (
        tuple(submission.__all__)
        + tuple(adapter.__all__)
        + tuple(execution_plan.__all__[:-5])
        + tuple(execution_plan.__all__[-5:])
    )
    assert metadata.public_api == expected
    assert len(metadata.public_api) == 41
    assert len(metadata.public_api) == len(set(metadata.public_api))
    inventories = (
        (submission, submission.__all__),
        (adapter, adapter.__all__),
        (execution_plan, execution_plan.__all__),
    )
    for module, names in inventories:
        assert all(name and not name.startswith("_") for name in names)
        assert all(getattr(module, name, None) is not None for name in names)
    assert submission.ControlledRuntimeSubmissionBuilder is not None
    assert adapter.ControlledRuntimeAdapter is not None
    assert execution_plan.ControlledRuntimeExecutionPlanner is not None


def test_manifest_is_canonical_environment_free_and_boundary_zero() -> None:
    path = ROOT / "manifests/controlled_runtime_stage54_freeze_manifest.json"
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8")
    payload = json.loads(text)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    assert text in {canonical, canonical + "\n"}
    assert "timestamp" not in payload
    assert "commit" not in payload
    assert "hostname" not in payload
    assert "username" not in payload
    assert all(
        payload[name] == 0
        for name in (
            "runtime_executions_added",
            "provider_requests_added",
            "network_requests_added",
            "translation_executions_added",
            "output_writes_added",
            "resume_writes_added",
            "cache_writes_added",
            "retry_executions_added",
            "fallback_executions_added",
            "production_hooks_added",
        )
    )
    assert payload["production_integration_authorized"] is False


def test_hash_inventory_is_exact_sorted_valid_and_source_only() -> None:
    metadata = get_controlled_runtime_preparation_freeze_metadata()
    assert len(metadata.frozen_modules) == 16
    assert metadata.frozen_modules == tuple(sorted(metadata.frozen_modules))
    assert len(metadata.frozen_modules) == len(set(metadata.frozen_modules))
    manifest = json.loads(
        (
            ROOT / "manifests/controlled_runtime_stage54_freeze_manifest.json"
        ).read_text(encoding="utf-8")
    )
    entries = manifest["frozen_files"]
    assert tuple(entry["path"] for entry in entries) == metadata.frozen_modules
    for entry in entries:
        relative = entry["path"]
        pure = PurePosixPath(relative)
        assert not pure.is_absolute()
        assert ".." not in pure.parts
        assert relative.startswith("core/controlled_runtime_")
        assert relative.endswith(".py")
        assert not any(
            token in relative
            for token in ("tests/", "docs/", "artifacts/", "verification/")
        )
        path = ROOT.joinpath(*pure.parts)
        assert path.is_file()
        assert (
            hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
        )


def test_validation_succeeds_and_result_is_frozen() -> None:
    first = validate_controlled_runtime_preparation_freeze()
    second = validate_controlled_runtime_preparation_freeze()
    assert first == second
    assert first.valid
    assert first.frozen_file_count == 16
    assert first.public_api_count == 41
    assert first.invariant_count == 49
    with pytest.raises(FrozenInstanceError):
        first.valid = False  # type: ignore[misc]


def test_source_hash_drift_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = hashlib.sha256

    class ChangedHash:
        def hexdigest(self) -> str:
            return "0" * 64

    monkeypatch.setattr(
        freeze.hashlib,
        "sha256",
        lambda value=b"": ChangedHash(),
    )
    with pytest.raises(
        ControlledRuntimePreparationFreezeValidationError,
        match="hash mismatch",
    ):
        validate_controlled_runtime_preparation_freeze()
    monkeypatch.setattr(freeze.hashlib, "sha256", original)


def test_public_api_and_manifest_drift_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        execution_plan,
        "__all__",
        execution_plan.__all__[:-1],
    )
    with pytest.raises(
        ControlledRuntimePreparationFreezeValidationError,
        match="Public API",
    ):
        validate_controlled_runtime_preparation_freeze()
