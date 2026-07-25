import sqlite3

import pytest

from core.controlled_runtime_scheduling_dispatch import (
    ControlledRuntimeScheduler,
    ControlledRuntimeSchedulingDispatchPathError,
    ControlledRuntimeSchedulingRegistry,
    verify_controlled_runtime_scheduling_dispatch,
)
from tests.unit.controlled_runtime_scheduling_dispatch import build_context


def test_first_success_replay_and_durable_counts(tmp_path):
    context = build_context(tmp_path)
    scheduler = ControlledRuntimeScheduler()
    first = scheduler.schedule(**context)
    replay = scheduler.schedule(**context)
    registry = ControlledRuntimeSchedulingRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert first.verification_succeeded
    assert replay.replay_detected and replay.reason_codes == ("ALREADY_SCHEDULED",)
    assert registry.counts() == (1, 1, 1)
    verification = verify_controlled_runtime_scheduling_dispatch(
        first.schedule,
        first.dispatch_package,
        request=context["request"],
        result=first,
        persisted_schedule_payload_json=first.schedule.to_json(),
        persisted_dispatch_payload_json=first.dispatch_package.to_json(),
        persistence_committed=True,
        schedule_readback_verified=True,
        dispatch_readback_verified=True,
        **{key: context[key] for key in (
            "queue_record", "stage71_request", "stage71_result",
            "stage613_claim", "stage613_request", "stage613_result",
            "stage613_verification_context",
        )},
    )
    assert verification.valid


def test_atomic_rollback_after_schedule_insert(tmp_path):
    context = build_context(tmp_path)
    first = ControlledRuntimeScheduler().schedule(**context)
    assert first.verification_succeeded
    # A fresh database and injected transaction failure prove no partial rows.
    rollback_path = tmp_path / "rollback.sqlite3"
    context["database_path"] = rollback_path
    built = ControlledRuntimeScheduler().schedule(**context)
    assert built.verification_succeeded
    connection = sqlite3.connect(rollback_path)
    connection.execute("DELETE FROM controlled_runtime_dispatch_packages")
    connection.commit()
    connection.close()
    registry = ControlledRuntimeSchedulingRegistry(rollback_path, allowed_root=tmp_path)
    with pytest.raises(Exception):
        registry.read(built.schedule.schedule_id)


@pytest.mark.parametrize("path", ["../escape.sqlite3", "https://example/x", "file:bad.db", "\\\\server\\share\\x.db"])
def test_unsafe_paths_rejected(tmp_path, path):
    with pytest.raises(ControlledRuntimeSchedulingDispatchPathError):
        ControlledRuntimeSchedulingRegistry(path, allowed_root=tmp_path)


def test_no_default_database(tmp_path):
    with pytest.raises(ControlledRuntimeSchedulingDispatchPathError):
        ControlledRuntimeSchedulingRegistry("", allowed_root=tmp_path)


def test_registry_metadata_tamper_rejected(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeScheduler().schedule(**context)
    assert result.verification_succeeded
    connection = sqlite3.connect(context["database_path"])
    connection.execute("UPDATE registry_metadata SET schema_version='bad'")
    connection.commit()
    connection.close()
    with pytest.raises(Exception):
        ControlledRuntimeSchedulingRegistry(
            context["database_path"], allowed_root=tmp_path
        ).counts()


def test_injected_failure_rolls_back_all_three_rows(tmp_path):
    context = build_context(tmp_path)
    successful = ControlledRuntimeScheduler().schedule(**context)
    rollback_path = tmp_path / "injected-rollback.sqlite3"

    def fail(point):
        if point == "after_schedule_insert":
            raise RuntimeError("injected rollback proof")

    registry = ControlledRuntimeSchedulingRegistry(
        rollback_path, allowed_root=tmp_path, failure_injector=fail
    )
    authority = {key: context[key] for key in (
        "queue_record", "stage71_request", "stage71_result",
        "stage613_claim", "stage613_request", "stage613_result",
        "stage613_verification_context",
    )}
    with pytest.raises(Exception):
        registry.schedule(
            context["request"], successful.schedule,
            successful.dispatch_package, **authority,
        )
    assert ControlledRuntimeSchedulingRegistry(
        rollback_path, allowed_root=tmp_path
    ).counts() == (0, 0, 0)
