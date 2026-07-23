from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

import core.translation_execution_approval as approval
import core.translation_execution_authorization as authorization
import core.translation_execution_package as package
from core.translation_execution_approval import (
    TranslationExecutionGovernanceFreezeMetadata,
    TranslationExecutionGovernanceFreezeValidationError,
    TranslationExecutionGovernanceFreezeValidationResult,
    get_translation_execution_governance_freeze_metadata,
    validate_translation_execution_governance_freeze,
)


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "manifests/translation_execution_stage44_freeze_manifest.json"


def test_metadata_is_frozen_deterministic_and_globally_denied() -> None:
    first = get_translation_execution_governance_freeze_metadata()
    assert isinstance(first, TranslationExecutionGovernanceFreezeMetadata)
    assert dataclasses.is_dataclass(first)
    assert first.__dataclass_params__.frozen is True
    assert first is get_translation_execution_governance_freeze_metadata()
    assert (
        first.component_name,
        first.freeze_version,
        first.activation_gate,
    ) == (
        "ntpe.translation_execution_governance",
        "4.4",
        "translation_execution_governance_frozen",
    )
    assert (
        first.package_schema_name,
        first.package_schema_version,
        first.authorization_schema_name,
        first.authorization_schema_version,
        first.approval_schema_name,
        first.approval_schema_version,
    ) == (
        "ntpe.translation_execution_package",
        "1.0",
        "ntpe.translation_execution_authorization_decision",
        "1.0",
        "ntpe.translation_execution_approval_record",
        "1.0",
    )
    assert isinstance(first.frozen_modules, tuple)
    assert isinstance(first.public_api, tuple)
    assert isinstance(first.invariants, tuple)
    assert not any(
        (
            first.provider_execution_authorized,
            first.translation_execution_authorized,
            first.runtime_submission_authorized,
            first.automatic_retry_authorized,
            first.automatic_fallback_authorized,
            first.output_replacement_authorized,
            first.production_integration_authorized,
        )
    )
    rendered = repr(first).lower()
    assert all(token not in rendered for token in ("timestamp", "uuid", "d:\\", "c:\\"))
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.freeze_version = "changed"  # type: ignore[misc]


def test_public_api_inventory_is_exact_importable_and_unique() -> None:
    metadata = get_translation_execution_governance_freeze_metadata()
    expected = tuple(package.__all__) + tuple(authorization.__all__) + tuple(approval.__all__)
    assert metadata.public_api == expected
    assert len(metadata.public_api) == 34
    assert len(metadata.public_api) == len(set(metadata.public_api))
    assert all(not name.startswith("_") for name in metadata.public_api)
    for module in (package, authorization, approval):
        assert len(module.__all__) == len(set(module.__all__))
        assert all(getattr(module, name, None) is not None for name in module.__all__)
    assert package.TranslationExecutionPackageBuilder is not None
    assert authorization.TranslationExecutionAuthorizationEvaluator is not None
    assert approval.TranslationExecutionApprover is not None


def test_manifest_is_canonical_complete_and_environment_free() -> None:
    raw = MANIFEST.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    data = json.loads(raw.decode("utf-8"))
    assert raw.decode("utf-8").rstrip("\n") == json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    assert data["component"] == "ntpe.translation_execution_governance"
    assert data["schemas"] == {
        "approval": ["ntpe.translation_execution_approval_record", "1.0"],
        "authorization": [
            "ntpe.translation_execution_authorization_decision",
            "1.0",
        ],
        "package": ["ntpe.translation_execution_package", "1.0"],
    }
    assert all(
        data[name] == 0
        for name in (
            "provider_requests_added",
            "network_requests_added",
            "translation_executions_added",
            "runtime_submissions_added",
            "output_writes_added",
            "retry_executions_added",
            "fallback_executions_added",
            "production_hooks_added",
        )
    )
    text = raw.decode("utf-8").lower()
    assert all(token not in text for token in ("timestamp", "git_hash", "commit_hash", "d:\\", "c:\\"))


def test_source_hash_inventory_is_exact_sorted_and_valid() -> None:
    metadata = get_translation_execution_governance_freeze_metadata()
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))["frozen_files"]
    paths = tuple(item["path"] for item in entries)
    assert len(paths) == 16
    assert paths == metadata.frozen_modules == tuple(sorted(paths))
    assert len(paths) == len(set(paths))
    assert all("\\" not in path and not Path(path).is_absolute() for path in paths)
    assert all(
        not any(part in path for part in ("tests/", "docs/", "artifacts/", "__pycache__"))
        for path in paths
    )
    for entry in entries:
        source = ROOT / entry["path"]
        assert source.is_file()
        assert len(entry["sha256"]) == 64 and entry["sha256"].islower()
        assert hashlib.sha256(source.read_bytes()).hexdigest() == entry["sha256"]


def test_freeze_validation_succeeds_and_result_is_frozen() -> None:
    result = validate_translation_execution_governance_freeze()
    assert isinstance(result, TranslationExecutionGovernanceFreezeValidationResult)
    assert result.valid is True
    assert (result.frozen_file_count, result.public_api_count, result.invariant_count) == (
        16,
        34,
        38,
    )
    assert result is validate_translation_execution_governance_freeze()
    assert result.__dataclass_params__.frozen is True


def test_freeze_validation_reads_only_manifest_and_frozen_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[Path] = []
    original = Path.read_bytes

    def recording_read(path: Path) -> bytes:
        observed.append(path.resolve())
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", recording_read)
    validate_translation_execution_governance_freeze()
    metadata = get_translation_execution_governance_freeze_metadata()
    expected = {MANIFEST.resolve()} | {
        (ROOT / relative).resolve() for relative in metadata.frozen_modules
    }
    assert set(observed) == expected


def test_source_hash_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    target = (ROOT / "core/translation_execution_package/models.py").resolve()
    original = Path.read_bytes

    def drifting_read(path: Path) -> bytes:
        content = original(path)
        return content + b"\n# drift" if path.resolve() == target else content

    monkeypatch.setattr(Path, "read_bytes", drifting_read)
    with pytest.raises(
        TranslationExecutionGovernanceFreezeValidationError,
        match="hash mismatch",
    ):
        validate_translation_execution_governance_freeze()


def test_public_api_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(package, "__all__", package.__all__[:-1])
    with pytest.raises(
        TranslationExecutionGovernanceFreezeValidationError,
        match="Public API inventory drifted",
    ):
        validate_translation_execution_governance_freeze()


def test_manifest_inventory_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = Path.read_bytes
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["frozen_files"] = data["frozen_files"][:-1]
    drifted = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")

    def drifting_manifest(path: Path) -> bytes:
        return drifted if path.resolve() == MANIFEST.resolve() else original(path)

    monkeypatch.setattr(Path, "read_bytes", drifting_manifest)
    with pytest.raises(
        TranslationExecutionGovernanceFreezeValidationError,
        match="incomplete, extra, or unsorted",
    ):
        validate_translation_execution_governance_freeze()
