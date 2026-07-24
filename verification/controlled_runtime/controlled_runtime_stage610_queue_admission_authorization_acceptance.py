from pathlib import Path
from tempfile import TemporaryDirectory

from core.controlled_runtime_queue_admission_authorization import (
    ControlledRuntimeQueueAdmissionAuthorizer,
)
from tests.unit.controlled_runtime_queue_admission_authorization import build_context


def main() -> int:
    with TemporaryDirectory() as directory:
        context = build_context(Path(directory))
        left = ControlledRuntimeQueueAdmissionAuthorizer().authorize(**context)
        right = ControlledRuntimeQueueAdmissionAuthorizer().authorize(**context)
        decision = left.decision
        checks = (
            ("authentic Stage 6.9 verified", left.upstream_verified),
            ("one request", left.request_count == 1),
            ("one decision", left.decision_count == 1),
            ("27-layer chain", decision is not None and len(decision.canonical_chain) == 27),
            ("admission authorized", decision is not None and decision.queue_admission_authorized),
            ("authorization unconsumed", decision is not None and not decision.queue_admission_authorization_consumed),
            ("queue records zero", left.queue_record_count == 0),
            ("scheduler zero", left.scheduler_access_count == 0),
            ("runtime zero", left.runtime_execution_count == 0),
            ("provider/network/translation zero", (left.provider_execution_count, left.network_execution_count, left.translation_execution_count) == (0, 0, 0)),
            ("deterministic", left == right),
        )
    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
