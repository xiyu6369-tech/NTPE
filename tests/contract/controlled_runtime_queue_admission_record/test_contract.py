import inspect
from pathlib import Path

import core.controlled_runtime_queue_admission_record as public
from core.controlled_runtime_queue_admission_record.policy import *


def test_exact_public_api_and_schemas():
    assert public.__all__ == [
        "ControlledRuntimeQueueAdmissionRecordRequest",
        "ControlledRuntimeQueueAdmissionRecord",
        "ControlledRuntimeQueueAdmissionRecordResult",
        "ControlledRuntimeQueueAdmissionRecordVerificationResult",
        "ControlledRuntimeQueueAdmissionRecordPolicy",
        "ControlledRuntimeQueueAdmissionRecordBuilder",
        "verify_controlled_runtime_queue_admission_record",
        "QueueAdmissionRecordPreparationError",
        "QueueAdmissionRecordPreparationIntegrityError",
        "QueueAdmissionRecordPreparationSchemaError",
        "QueueAdmissionRecordPreparationVerificationError",
    ]
    assert REQUEST_SCHEMA_NAME == "ntpe.controlled_runtime_queue_admission_record_request"
    assert RECORD_SCHEMA_NAME == "ntpe.controlled_runtime_queue_admission_record"
    assert RESULT_SCHEMA_NAME == "ntpe.controlled_runtime_queue_admission_record_result"
    assert VERIFICATION_SCHEMA_NAME == (
        "ntpe.controlled_runtime_queue_admission_record_verification_result"
    )
    assert PREPARATION_INTENT == "prepare_exactly_one_immutable_queue_admission_record"
    assert SUCCESS_STATUS == "queue_admission_record_prepared_not_admitted"
    assert ADMISSION_CLASS == "controlled_runtime_single_unit"
    assert PRIORITY_CLASS == "controlled_default"


def test_reason_codes_integrity():
    assert len(REASON_CODES) == 20
    assert len(set(REASON_CODES)) == len(REASON_CODES)


def test_production_has_no_durable_or_active_runtime_dependencies():
    root = Path(inspect.getfile(public)).parent
    source = "\n".join(
        path.read_text(encoding="utf-8").lower() for path in root.glob("*.py")
    )
    for token in (
        "import sqlite3", "import sqlite",
        "scheduling_envelope_consumption.registry",
        "queue_admission_authorization_consumption.registry",
        "import subprocess", "import asyncio",
        "threadpoolexecutor", "runtime executor",
    ):
        assert token not in source
