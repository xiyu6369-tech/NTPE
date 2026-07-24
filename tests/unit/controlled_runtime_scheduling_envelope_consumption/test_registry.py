import sqlite3

import pytest

from core.controlled_runtime_scheduling_envelope_consumption import (
    ControlledRuntimeSchedulingEnvelopeConsumer,
    ControlledRuntimeSchedulingEnvelopeConsumptionRegistry,
    SchedulingEnvelopeConsumptionCommitError,
    SchedulingEnvelopeConsumptionRegistryIntegrityError,
    SchedulingEnvelopeConsumptionRegistryPathError,
)
from core.controlled_runtime_scheduling_envelope_consumption.registry import (
    CLAIMS_TABLE,
)
from tests.unit.controlled_runtime_scheduling_envelope_consumption import (
    build_context,
)


def test_first_consumption_succeeds_and_identical_replay_fails(tmp_path):
    context = build_context(tmp_path)
    first = ControlledRuntimeSchedulingEnvelopeConsumer().consume(**context)
    second = ControlledRuntimeSchedulingEnvelopeConsumer().consume(**context)
    assert first.status == (
        "scheduling_envelope_consumed_not_admitted_not_scheduled"
    )
    assert first.claim is not None
    assert second.status == "already_consumed"
    assert second.replay_detected
    registry = ControlledRuntimeSchedulingEnvelopeConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert registry.count_claims() == 1
    assert registry.read(context["request"].consumption_request_id) == first.claim


def test_transaction_failure_rolls_back_without_partial_row(tmp_path):
    context = build_context(tmp_path)

    def fail(point):
        if point == "after_insert":
            raise RuntimeError("injected")

    registry = ControlledRuntimeSchedulingEnvelopeConsumptionRegistry(
        context["database_path"],
        allowed_root=tmp_path,
        failure_injector=fail,
    )
    consumer = ControlledRuntimeSchedulingEnvelopeConsumer()
    normal_registry = ControlledRuntimeSchedulingEnvelopeConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    original = (
        ControlledRuntimeSchedulingEnvelopeConsumptionRegistry.claim
    )
    try:
        ControlledRuntimeSchedulingEnvelopeConsumptionRegistry.claim = (
            lambda self, request, claim: original(registry, request, claim)
        )
        result = consumer.consume(**context)
    finally:
        ControlledRuntimeSchedulingEnvelopeConsumptionRegistry.claim = original
    assert result.status == "registry_error"
    assert normal_registry.count_claims() == 0


@pytest.mark.parametrize(
    "database_path",
    ["../escape.sqlite3", "../../escape.sqlite3"],
)
def test_traversal_is_rejected(tmp_path, database_path):
    with pytest.raises(SchedulingEnvelopeConsumptionRegistryPathError):
        ControlledRuntimeSchedulingEnvelopeConsumptionRegistry(
            database_path, allowed_root=tmp_path
        )


def test_outside_allowed_root_and_missing_paths_are_rejected(tmp_path):
    with pytest.raises(SchedulingEnvelopeConsumptionRegistryPathError):
        ControlledRuntimeSchedulingEnvelopeConsumptionRegistry(
            tmp_path.parent / "outside.sqlite3", allowed_root=tmp_path
        )
    with pytest.raises(TypeError):
        ControlledRuntimeSchedulingEnvelopeConsumptionRegistry()


def test_symlink_escape_is_rejected_when_supported(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(SchedulingEnvelopeConsumptionRegistryPathError):
        ControlledRuntimeSchedulingEnvelopeConsumptionRegistry(
            link / "escape.sqlite3", allowed_root=tmp_path
        )


def test_malformed_durable_row_is_rejected(tmp_path):
    context = build_context(tmp_path)
    result = ControlledRuntimeSchedulingEnvelopeConsumer().consume(**context)
    assert result.claim is not None
    connection = sqlite3.connect(context["database_path"])
    connection.execute(
        f"UPDATE {CLAIMS_TABLE} SET claim_payload_json='{{}}'"
    )
    connection.commit()
    connection.close()
    registry = ControlledRuntimeSchedulingEnvelopeConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    with pytest.raises(SchedulingEnvelopeConsumptionRegistryIntegrityError):
        registry.read(context["request"].consumption_request_id)


def test_independent_registries_and_connection_cleanup(tmp_path):
    context = build_context(tmp_path)
    left = ControlledRuntimeSchedulingEnvelopeConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    right = ControlledRuntimeSchedulingEnvelopeConsumptionRegistry(
        context["database_path"], allowed_root=tmp_path
    )
    assert left is not right
    assert left.count_claims() == right.count_claims() == 0
    context["database_path"].unlink()

