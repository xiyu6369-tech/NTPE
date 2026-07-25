from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier

from core.controlled_runtime_queue_admission import (
    ControlledRuntimeQueueAdmitter,
    ControlledRuntimeQueueRegistry,
    verify_controlled_runtime_queue_record,
)
from tests.unit.controlled_runtime_queue_admission import build_context


def main() -> int:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        context = build_context(root)
        admitter = ControlledRuntimeQueueAdmitter()
        first = admitter.admit(**context)
        replay = admitter.admit(**context)
        record = first.queue_record
        registry = ControlledRuntimeQueueRegistry(
            context["database_path"], allowed_root=root
        )
        verification = None
        if record is not None:
            verification = verify_controlled_runtime_queue_record(
                record,
                request=context["request"],
                stage613_claim=context["stage613_claim"],
                stage613_request=context["stage613_request"],
                stage613_result=context["stage613_result"],
                stage613_verification_context=(
                    context["stage613_verification_context"]
                ),
                persisted_payload_json=record.to_json(),
                persistence_committed=True,
                durable_readback_verified=True,
            )

        concurrent_root = root / "concurrent"
        concurrent_root.mkdir()
        concurrent_context = build_context(concurrent_root)
        barrier = Barrier(6)

        def admit(_):
            barrier.wait()
            return ControlledRuntimeQueueAdmitter().admit(
                **dict(concurrent_context)
            )

        with ThreadPoolExecutor(max_workers=6) as pool:
            concurrent = list(pool.map(admit, range(6)))
        concurrent_registry = ControlledRuntimeQueueRegistry(
            concurrent_context["database_path"],
            allowed_root=concurrent_root,
        )

        checks = (
            ("authentic Stage 6.13 authority verified", first.upstream_verified),
            ("one queue admission performed", first.queue_admission_count == 1),
            ("one durable queue record created", first.queue_record_created_count == 1),
            ("queue record exists", record is not None),
            ("35-layer canonical chain", record is not None and len(record.canonical_chain) == 35),
            ("33 upstream layers preserved", record is not None and tuple(record.canonical_chain[:33]) == tuple(context["stage613_claim"].canonical_chain)),
            ("layer 34 admission request", record is not None and record.canonical_chain[33] == context["request"].request_fingerprint),
            ("layer 35 queue record", record is not None and record.canonical_chain[34] == record.queue_record_fingerprint),
            ("queue admission performed", record is not None and record.queue_admission_performed),
            ("queue record created", record is not None and record.queue_record_created),
            ("queue record not consumed", record is not None and not record.queue_record_consumed),
            ("Runtime not scheduled", record is not None and not record.runtime_execution_scheduled),
            ("execution not started", record is not None and not record.execution_started),
            ("durable commit and readback", first.persistence_committed and first.durable_readback_verified),
            ("official verification", verification is not None and verification.valid),
            ("identical replay closed", replay.replay_detected and replay.queue_record is None),
            ("one durable row", registry.count_records() == 1),
            ("six-way exactly one success", sum(result.queue_record is not None for result in concurrent) == 1),
            ("six-way five replays", sum(result.replay_detected for result in concurrent) == 5),
            ("six-way one durable row", concurrent_registry.count_records() == 1),
            ("schedules zero", first.runtime_schedule_count == 0),
            ("scheduler access zero", first.scheduler_count == 0),
            ("task job worker creation zero", (first.task_created_count, first.job_created_count, first.worker_created_count) == (0, 0, 0)),
            ("Runtime execution zero", first.runtime_execution_count == 0),
            ("Provider network translation zero", (first.provider_execution_count, first.network_execution_count, first.translation_execution_count) == (0, 0, 0)),
            ("output resume cache mutation zero", (first.output_write_count, first.resume_write_count, first.cache_write_count) == (0, 0, 0)),
        )
    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
