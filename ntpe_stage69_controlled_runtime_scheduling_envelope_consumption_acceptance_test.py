from pathlib import Path
from tempfile import TemporaryDirectory

from core.controlled_runtime_scheduling_envelope_consumption import (
    ControlledRuntimeSchedulingEnvelopeConsumer,
    ControlledRuntimeSchedulingEnvelopeConsumptionRegistry,
)
from tests.unit.controlled_runtime_scheduling_envelope_consumption import (
    build_context,
)


def main() -> int:
    checks = []
    with TemporaryDirectory() as directory:
        root = Path(directory)
        context = build_context(root)
        first = ControlledRuntimeSchedulingEnvelopeConsumer().consume(**context)
        second = ControlledRuntimeSchedulingEnvelopeConsumer().consume(**context)
        registry = ControlledRuntimeSchedulingEnvelopeConsumptionRegistry(
            context["database_path"], allowed_root=root
        )
        claim = first.claim
        checks.extend(
            [
                ("authentic upstream verified", first.upstream_verification_succeeded),
                ("durable claim created", first.durable_claim_created),
                ("one envelope consumed", first.exactly_one_envelope_consumed),
                ("25-layer chain", claim is not None and len(claim.canonical_chain) == 25),
                ("replay rejected", second.replay_detected and second.claim is None),
                ("exactly one durable row", registry.count_claims() == 1),
                ("queue admission remains false", claim is not None and not claim.queue_admission_authorized),
                ("runtime scheduling remains false", claim is not None and not claim.runtime_execution_scheduled),
                ("queue writes remain zero", claim is not None and not claim.queue_record_created),
                ("execution remains false", claim is not None and not claim.execution_started),
            ]
        )
    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
    passed = all(value for _, value in checks)
    print(f"{'PASS' if passed else 'FAIL'}: Stage 6.9 acceptance")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
