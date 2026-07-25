from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier

from core.controlled_runtime_queue_admission_record_consumption import (
    ControlledRuntimeQueueAdmissionRecordConsumer,
    ControlledRuntimeQueueAdmissionRecordConsumptionRegistry,
)
from tests.unit.controlled_runtime_queue_admission_record_consumption import (
    build_context,
)


def main() -> int:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        context = build_context(root)
        first = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**context)
        replay = ControlledRuntimeQueueAdmissionRecordConsumer().consume(**context)
        claim = first.claim
        registry = ControlledRuntimeQueueAdmissionRecordConsumptionRegistry(
            context["database_path"], allowed_root=root
        )

        concurrent_root = root / "concurrent"
        concurrent_root.mkdir()
        concurrent_context = build_context(concurrent_root)
        barrier = Barrier(6)

        def consume(_):
            barrier.wait()
            return ControlledRuntimeQueueAdmissionRecordConsumer().consume(
                **dict(concurrent_context)
            )

        with ThreadPoolExecutor(max_workers=6) as pool:
            concurrent = list(pool.map(consume, range(6)))

        checks = (
            ("authentic Stage 6.12 verified", first.upstream_verified),
            ("one consumption request", first.record_consumption_count == 1),
            ("one durable claim", claim is not None),
            ("33-layer chain", claim is not None and len(claim.canonical_chain) == 33),
            (
                "31-layer upstream preserved",
                claim is not None
                and tuple(claim.canonical_chain[:31])
                == tuple(context["stage612_record"].canonical_chain),
            ),
            (
                "layer 32 request",
                claim is not None
                and claim.canonical_chain[31] == context["request"].request_fingerprint,
            ),
            (
                "layer 33 durable claim",
                claim is not None
                and claim.canonical_chain[32] == claim.claim_fingerprint,
            ),
            (
                "record consumed nonreusable",
                claim is not None
                and claim.queue_admission_record_consumed
                and not claim.queue_admission_record_reusable,
            ),
            (
                "durable readback",
                claim is not None
                and registry.read(context["request"].consumption_request_id) == claim,
            ),
            ("replay closed", replay.replay_detected and replay.claim is None),
            (
                "one concurrent consumer",
                sum(result.claim is not None for result in concurrent) == 1,
            ),
            (
                "five concurrent replays",
                sum(result.replay_detected for result in concurrent) == 5,
            ),
            ("queue admission zero", first.queue_admission_count == 0),
            (
                "queue writes zero",
                first.queue_record_created_count
                == first.queue_record_consumed_count
                == 0,
            ),
            (
                "scheduler and execution zero",
                first.scheduling_queued_count
                == first.scheduler_count
                == first.runtime_execution_count
                == 0,
            ),
            (
                "provider network translation zero",
                first.provider_execution_count
                == first.network_execution_count
                == first.translation_execution_count
                == 0,
            ),
        )

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
