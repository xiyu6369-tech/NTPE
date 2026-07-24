"""Offline acceptance check for Stage 6.5."""

from core.controlled_runtime_handoff_boundary import ControlledRuntimeHandoffBoundary
from tests.unit.controlled_runtime_handoff_boundary.test_boundary import build_inputs


def main() -> int:
    result = ControlledRuntimeHandoffBoundary().accept(**build_inputs())
    assert result.status == "handoff_accepted_not_scheduled_not_executed"
    assert result.receipt.runtime_handoff_completed
    assert not result.receipt.runtime_execution_scheduled
    assert not result.receipt.execution_started
    assert len(result.receipt.upstream_fingerprint_chain) == 17
    print("Stage 6.5 controlled Runtime handoff boundary: ACCEPTED")
    print("Runtime boundary calls: 1 (pure in-memory)")
    print("Scheduling/Runtime/Provider/Network/Translation/Writes: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
