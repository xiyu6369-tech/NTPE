import json
import os
import sqlite3
import subprocess
from dataclasses import FrozenInstanceError, replace

import pytest

from core.controlled_runtime_queue_admission import (
    ControlledRuntimeQueueAdmitter,
    ControlledRuntimeQueueAdmissionIntegrityError,
    ControlledRuntimeQueueAdmissionPathError,
    ControlledRuntimeQueueAdmissionSchemaError,
    ControlledRuntimeQueueAdmissionVerificationError,
    ControlledRuntimeQueueRegistry,
    verify_controlled_runtime_queue_record,
)
from core.controlled_runtime_queue_admission.registry import (
    METADATA_TABLE,
    QUEUE_TABLE,
)
from tests.unit.controlled_runtime_queue_admission import build_context


def test_first_admission_succeeds_and_identical_replay_is_closed(tmp_path):
    context = build_context(tmp_path)
    admitter = ControlledRuntimeQueueAdmitter()
    first = admitter.admit(**context)
    second = admitter.admit(**context)
    record = first.queue_record
    assert record is not None
    assert first.verification_succeeded
    assert first.queue_admission_performed
    assert first.queue_record_created
    assert (first.queue_admission_count, first.queue_record_created_count) == (1, 1)
    assert len(record.canonical_chain) == 35
    assert tuple(record.canonical_chain[:33]) == tuple(
        context["stage613_claim"].canonical_chain
    )
    assert record.canonical_chain[33] == context["request"].request_fingerprint
    assert record.canonical_chain[34] == record.queue_record_fingerprint
    assert second.replay_detected
    assert second.reason_codes == ("ALREADY_ADMITTED",)
    assert second.queue_record is None
    registry = ControlledRuntimeQueueRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_records() == 1
    assert registry.read(context["request"].admission_request_id) == record
    with pytest.raises(FrozenInstanceError):
        record.queue_record_created = False


def test_exact_state_transition_and_zero_side_effect_counts(tmp_path):
    result = ControlledRuntimeQueueAdmitter().admit(**build_context(tmp_path))
    record = result.queue_record
    assert record is not None
    assert all((
        record.queue_admission_authorized,
        record.queue_admission_authorization_consumed,
        record.queue_admission_record_prepared,
        record.queue_admission_record_consumed,
        record.queue_admission_performed,
        record.queue_record_created,
    ))
    assert not any((
        record.queue_record_consumed,
        record.queue_record_reusable,
        record.runtime_execution_scheduled,
        record.execution_started,
    ))
    assert (
        result.queue_record_consumed_count,
        result.runtime_schedule_count,
        result.scheduler_count,
        result.task_created_count,
        result.job_created_count,
        result.worker_created_count,
        result.runtime_execution_count,
        result.provider_execution_count,
        result.network_execution_count,
        result.translation_execution_count,
        result.output_write_count,
        result.resume_write_count,
        result.cache_write_count,
    ) == (0,) * 13


@pytest.mark.parametrize(
    "field_name",
    [
        "stage613_claim_fingerprint",
        "stage613_consumption_request_fingerprint",
        "stage612_record_fingerprint",
        "stage612_request_fingerprint",
        "stage611_claim_fingerprint",
        "stage610_decision_fingerprint",
        "stage69_claim_fingerprint",
        "stage68_envelope_fingerprint",
        "stage67_claim_fingerprint",
        "stage66_decision_fingerprint",
        "runtime_boundary_id",
        "selected_adapter_index",
        "capability_state_fingerprint",
        "ordering_key",
    ],
)
def test_authenticated_binding_tamper_is_denied_without_a_row(tmp_path, field_name):
    context = build_context(tmp_path)
    current = getattr(context["request"], field_name)
    replacement = current + 1 if isinstance(current, int) else (
        "0" * 64 if len(current) == 64 else current + "-tampered"
    )
    object.__setattr__(context["request"], field_name, replacement)
    result = ControlledRuntimeQueueAdmitter().admit(**context)
    assert not result.verification_succeeded
    assert result.queue_record is None
    registry = ControlledRuntimeQueueRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_records() == 0


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("verification_succeeded", False),
        ("upstream_verified", False),
        ("durable_claim_created", False),
        ("exactly_one_record_consumed", False),
        ("replay_detected", True),
        ("persistence_committed", False),
        ("durable_readback_verified", False),
    ],
)
def test_failed_or_replay_only_stage613_result_is_denied(
    tmp_path, field_name, value
):
    context = build_context(tmp_path)
    context["stage613_result"] = replace(
        context["stage613_result"], **{field_name: value}
    )
    result = ControlledRuntimeQueueAdmitter().admit(**context)
    assert not result.verification_succeeded
    assert result.queue_record is None


def test_fake_authority_and_wrong_types_are_not_disguised_as_replay(tmp_path):
    context = build_context(tmp_path)
    context["stage613_claim"] = object()
    with pytest.raises(TypeError):
        ControlledRuntimeQueueAdmitter().admit(**context)
    wrong_root = tmp_path / "wrong-result"
    wrong_root.mkdir()
    context = build_context(wrong_root)
    context["stage613_result"] = object()
    with pytest.raises(TypeError):
        ControlledRuntimeQueueAdmitter().admit(**context)


def test_stage613_claim_tamper_is_rejected(tmp_path):
    context = build_context(tmp_path)
    object.__setattr__(context["stage613_claim"], "claim_fingerprint", "0" * 64)
    result = ControlledRuntimeQueueAdmitter().admit(**context)
    assert not result.verification_succeeded
    assert result.queue_record is None


def test_transaction_rolls_back_after_insert_failure(tmp_path, monkeypatch):
    context = build_context(tmp_path)

    def fail(point):
        if point == "after_insert":
            raise RuntimeError("injected failure")

    injected = ControlledRuntimeQueueRegistry(
        context["database_path"], allowed_root=tmp_path, failure_injector=fail
    )
    original = ControlledRuntimeQueueRegistry.admit
    monkeypatch.setattr(
        ControlledRuntimeQueueRegistry,
        "admit",
        lambda self, request, record, **kwargs: original(
            injected, request, record, **kwargs
        ),
    )
    result = ControlledRuntimeQueueAdmitter().admit(**context)
    assert result.reason_codes == ("REGISTRY_ERROR",)
    monkeypatch.setattr(ControlledRuntimeQueueRegistry, "admit", original)
    registry = ControlledRuntimeQueueRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_records() == 0


@pytest.mark.parametrize(
    "database_path",
    [
        "../escape.sqlite3",
        "file:escape.sqlite3",
        "sqlite:escape",
        "http://example.invalid/queue",
        "//server/share.db",
        "\\\\server\\share.db",
    ],
)
def test_traversal_uri_and_network_paths_are_rejected(tmp_path, database_path):
    with pytest.raises(ControlledRuntimeQueueAdmissionPathError):
        ControlledRuntimeQueueRegistry(database_path, allowed_root=tmp_path)


def test_relative_allowed_root_and_no_default_database_are_rejected(tmp_path):
    with pytest.raises(ControlledRuntimeQueueAdmissionPathError):
        ControlledRuntimeQueueRegistry("queue.sqlite3", allowed_root="relative")
    with pytest.raises(ControlledRuntimeQueueAdmissionPathError):
        ControlledRuntimeQueueRegistry("", allowed_root=tmp_path)


def test_symlink_escape_is_rejected(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    link = tmp_path / "link"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        junction = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
            capture_output=True,
            check=False,
        )
        if junction.returncode != 0:
            pytest.skip("symlink and junction creation are unavailable")
    with pytest.raises(ControlledRuntimeQueueAdmissionPathError):
        ControlledRuntimeQueueRegistry(link / "queue.sqlite3", allowed_root=tmp_path)


def test_persisted_identity_and_canonical_payload_tamper_are_rejected(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmitter().admit(**context)
    assert result.queue_record is not None
    connection = sqlite3.connect(context["database_path"])
    payload = json.loads(connection.execute(
        f"SELECT queue_record_payload_json FROM {QUEUE_TABLE}"
    ).fetchone()[0])
    payload["queue_record_id"] = "stage71-runtime-queue-record-tampered"
    connection.execute(
        f"UPDATE {QUEUE_TABLE} SET queue_record_payload_json=?",
        (json.dumps(payload),),
    )
    connection.commit()
    connection.close()
    registry = ControlledRuntimeQueueRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    with pytest.raises(ControlledRuntimeQueueAdmissionIntegrityError):
        registry.read(context["request"].admission_request_id)


def test_persisted_column_fingerprint_tamper_is_rejected(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmitter().admit(**context)
    assert result.queue_record is not None
    connection = sqlite3.connect(context["database_path"])
    connection.execute(
        f"UPDATE {QUEUE_TABLE} SET queue_record_fingerprint=?", ("0" * 64,)
    )
    connection.commit()
    connection.close()
    registry = ControlledRuntimeQueueRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    with pytest.raises(ControlledRuntimeQueueAdmissionIntegrityError):
        registry.read(context["request"].admission_request_id)


def test_registry_metadata_and_table_schema_tamper_are_rejected(tmp_path):
    metadata_root = tmp_path / "metadata"
    metadata_root.mkdir()
    context = build_context(metadata_root)
    registry = ControlledRuntimeQueueRegistry(
        context["database_path"], allowed_root=metadata_root
    )
    assert registry.count_records() == 0
    connection = sqlite3.connect(context["database_path"])
    connection.execute(f"UPDATE {METADATA_TABLE} SET schema_version='tampered'")
    connection.commit()
    connection.close()
    with pytest.raises(ControlledRuntimeQueueAdmissionSchemaError):
        registry.count_records()

    schema_root = tmp_path / "schema"
    schema_root.mkdir()
    path = schema_root / "queue.sqlite3"
    connection = sqlite3.connect(path)
    connection.execute(
        f"CREATE TABLE {METADATA_TABLE}("
        "schema_name TEXT PRIMARY KEY,schema_version TEXT NOT NULL)"
    )
    connection.execute(
        f"INSERT INTO {METADATA_TABLE} VALUES("
        "'ntpe.controlled_runtime_queue_registry','1.0')"
    )
    connection.execute(f"CREATE TABLE {QUEUE_TABLE}(wrong TEXT)")
    connection.commit()
    connection.close()
    malformed = ControlledRuntimeQueueRegistry(path, allowed_root=schema_root)
    with pytest.raises(ControlledRuntimeQueueAdmissionSchemaError):
        malformed.count_records()


def test_official_verifier_checks_commit_readback_payload_and_can_raise(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmitter().admit(**context)
    record = result.queue_record
    assert record is not None
    verification_args = dict(
        request=context["request"],
        stage613_claim=context["stage613_claim"],
        stage613_request=context["stage613_request"],
        stage613_result=context["stage613_result"],
        stage613_verification_context=context["stage613_verification_context"],
        persisted_payload_json=record.to_json(),
        persistence_committed=True,
        durable_readback_verified=True,
    )
    assert verify_controlled_runtime_queue_record(record, **verification_args).valid
    with pytest.raises(ControlledRuntimeQueueAdmissionVerificationError):
        verify_controlled_runtime_queue_record(
            record,
            **{
                **verification_args,
                "persisted_payload_json": "{}",
                "raise_on_error": True,
            },
        )


def test_sensitive_payload_is_not_persisted(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeQueueAdmitter().admit(**context)
    assert result.queue_record is not None
    raw = context["database_path"].read_bytes().lower()
    forbidden = (
        b"source_text", b"prompt", b"translation_output", b"provider_payload",
        b"credential", b"api_key", b"glossary", b"character_memory",
        b"environment_snapshot",
    )
    assert not any(token in raw for token in forbidden)
