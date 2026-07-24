import sqlite3

import pytest

from core.controlled_runtime_atomic_scheduling_consumption import (
    AtomicSchedulingAuthorizationConsumer,
    AtomicSchedulingAuthorizationConsumptionRegistry,
)
from core.controlled_runtime_atomic_scheduling_consumption.errors import (
    AtomicSchedulingConsumptionAlreadyConsumedError,
    AtomicSchedulingConsumptionCommitError,
    AtomicSchedulingConsumptionRegistryPathError,
    AtomicSchedulingConsumptionRegistrySchemaError,
)
from . import build_context


def test_path_must_be_explicit_absolute_root_and_beneath_root(tmp_path):
    with pytest.raises(AtomicSchedulingConsumptionRegistryPathError):
        AtomicSchedulingAuthorizationConsumptionRegistry("", allowed_root=tmp_path)
    with pytest.raises(AtomicSchedulingConsumptionRegistryPathError):
        AtomicSchedulingAuthorizationConsumptionRegistry("claim.sqlite3", allowed_root="")
    with pytest.raises(AtomicSchedulingConsumptionRegistryPathError):
        AtomicSchedulingAuthorizationConsumptionRegistry("claim.sqlite3", allowed_root="relative")
    with pytest.raises(AtomicSchedulingConsumptionRegistryPathError):
        AtomicSchedulingAuthorizationConsumptionRegistry(
            tmp_path / ".." / "escape.sqlite3", allowed_root=tmp_path
        )
    with pytest.raises(AtomicSchedulingConsumptionRegistryPathError):
        AtomicSchedulingAuthorizationConsumptionRegistry(
            tmp_path.parent / "escape.sqlite3", allowed_root=tmp_path
        )


def test_symlink_escape_is_rejected_when_supported(tmp_path):
    outside = tmp_path.parent / "stage67-outside"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable")
    with pytest.raises(AtomicSchedulingConsumptionRegistryPathError):
        AtomicSchedulingAuthorizationConsumptionRegistry(
            link / "claim.sqlite3", allowed_root=tmp_path
        )


def test_registry_schema_metadata_uniqueness_and_no_timestamp(tmp_path):
    context = build_context(tmp_path)
    result = AtomicSchedulingAuthorizationConsumer().consume(**context)
    assert result.claim is not None
    connection = sqlite3.connect(context["database_path"])
    try:
        metadata_columns = tuple(
            row[1] for row in connection.execute("PRAGMA table_info(registry_metadata)")
        )
        assert metadata_columns == ("schema_name", "schema_version", "component")
        metadata = connection.execute("SELECT * FROM registry_metadata").fetchone()
        assert metadata == (
            "ntpe.atomic_scheduling_authorization_consumption_registry",
            "1.0",
            "ntpe.stage6.7.atomic_scheduling_authorization_consumption",
        )
        sql = " ".join(
            row[0] for row in connection.execute(
                "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"
            )
        ).lower()
        assert "created_at" not in sql
        assert "datetime" not in sql
        indexes = {
            tuple(info[2] for info in connection.execute(f"PRAGMA index_info({row[1]})"))
            for row in connection.execute(
                "PRAGMA index_list(atomic_scheduling_consumption_claims)"
            )
            if row[2]
        }
        assert ("scheduling_authorization_id",) in indexes
        assert ("scheduling_consumption_id",) in indexes
    finally:
        connection.close()


def test_readback_reconstructs_exact_claim_and_count(tmp_path):
    context = build_context(tmp_path)
    result = AtomicSchedulingAuthorizationConsumer().consume(**context)
    registry = AtomicSchedulingAuthorizationConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_claims() == 1
    assert registry.read(context["request"].scheduling_consumption_id) == result.claim


def test_same_authorization_replay_is_rejected_without_mutation(tmp_path):
    context = build_context(tmp_path)
    first = AtomicSchedulingAuthorizationConsumer().consume(**context)
    second = AtomicSchedulingAuthorizationConsumer().consume(**context)
    assert first.status == "scheduling_authorization_consumed_not_scheduled"
    assert second.status == "already_consumed"
    registry = AtomicSchedulingAuthorizationConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_claims() == 1
    assert registry.read(context["request"].scheduling_consumption_id) == first.claim


def test_new_consumption_id_cannot_reuse_authorization(tmp_path):
    context = build_context(tmp_path)
    first = AtomicSchedulingAuthorizationConsumer().consume(**context)
    replay = build_context(tmp_path, scheduling_consumption_id="schedule-consume-002")
    second = AtomicSchedulingAuthorizationConsumer().consume(**replay)
    assert first.claim is not None
    assert second.status == "already_consumed"
    assert AtomicSchedulingAuthorizationConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    ).count_claims() == 1


def test_precommit_failures_roll_back_without_partial_claim(tmp_path):
    source = build_context(tmp_path)
    source["database_path"] = tmp_path / "source.sqlite3"
    claim = AtomicSchedulingAuthorizationConsumer().consume(**source).claim
    assert claim is not None

    for point in ("after_begin", "before_insert", "after_insert", "before_commit"):
        database_path = tmp_path / f"rollback-{point}.sqlite3"
        def fail(actual, expected=point):
            if actual == expected:
                raise RuntimeError("injected failure")
        registry = AtomicSchedulingAuthorizationConsumptionRegistry(
            database_path,
            allowed_root=tmp_path,
            failure_injector=fail,
        )
        with pytest.raises(AtomicSchedulingConsumptionCommitError):
            registry.claim(source["request"], claim)
        clean = AtomicSchedulingAuthorizationConsumptionRegistry(
            database_path, allowed_root=tmp_path
        )
        assert clean.count_claims() == 0


def test_wrong_and_corrupt_schema_fail_closed(tmp_path):
    wrong = tmp_path / "wrong.sqlite3"
    connection = sqlite3.connect(wrong)
    connection.execute("CREATE TABLE unrelated(value TEXT)")
    connection.commit()
    connection.close()
    with pytest.raises(AtomicSchedulingConsumptionRegistrySchemaError):
        AtomicSchedulingAuthorizationConsumptionRegistry(
            wrong, allowed_root=tmp_path
        ).count_claims()

    corrupt = tmp_path / "corrupt.sqlite3"
    corrupt.write_bytes(b"not sqlite")
    with pytest.raises(AtomicSchedulingConsumptionRegistrySchemaError):
        AtomicSchedulingAuthorizationConsumptionRegistry(
            corrupt, allowed_root=tmp_path
        ).count_claims()


def test_registry_has_no_destructive_or_mutation_api():
    forbidden = ("delete", "update", "upsert", "reset", "release", "revoke", "reuse")
    for name in forbidden:
        assert not hasattr(AtomicSchedulingAuthorizationConsumptionRegistry, name)


def test_registry_payload_excludes_sensitive_and_machine_values(tmp_path):
    context = build_context(tmp_path)
    AtomicSchedulingAuthorizationConsumer().consume(**context)
    connection = sqlite3.connect(context["database_path"])
    try:
        payloads = " ".join(
            str(value)
            for row in connection.execute(
                "SELECT request_payload_json, claim_payload_json FROM atomic_scheduling_consumption_claims"
            )
            for value in row
        ).lower()
    finally:
        connection.close()
    for forbidden in (
        "source_text", "prompt_text", "credentials", "provider_payload",
        "translated_output", "hostname", "username", "process_id", "timestamp",
        "created_at",
    ):
        assert forbidden not in payloads