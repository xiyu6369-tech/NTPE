from pathlib import Path
from tempfile import TemporaryDirectory

from core.controlled_runtime_queue_admission_record import (
    ControlledRuntimeQueueAdmissionRecordBuilder,
)
from tests.unit.controlled_runtime_queue_admission_record import build_context


def main() -> int:
    with TemporaryDirectory() as directory:
        context = build_context(Path(directory))
        left = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**context)
        right = ControlledRuntimeQueueAdmissionRecordBuilder().prepare(**context)
        record = left.record
        checks = (
            ("authentic Stage 6.11 verified", left.upstream_verified),
            ("one request", left.record_preparation_count == 1),
            ("one record", record is not None),
            ("31-layer chain", record is not None and len(record.canonical_chain) == 31),
            ("record prepared", record is not None and record.queue_admission_record_prepared),
            ("record not consumed", record is not None and not record.queue_admission_record_consumed),
            ("queue record not created", record is not None and not record.queue_record_created),
            ("no scheduling", record is not None and not record.runtime_execution_scheduled),
            ("no execution", record is not None and not record.execution_started),
            ("queue admission zero", left.queue_admission_count == 0),
            ("queue record created zero", left.queue_record_created_count == 0),
            ("queue record consumed zero", left.queue_record_consumed_count == 0),
            ("scheduler zero", left.scheduler_count == 0),
            ("runtime zero", left.runtime_execution_count == 0),
            ("provider/network/translation zero", (left.provider_execution_count, left.network_execution_count, left.translation_execution_count) == (0, 0, 0)),
            ("deterministic", left == right),
        )
    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
