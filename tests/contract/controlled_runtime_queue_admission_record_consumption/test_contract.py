import inspect
from pathlib import Path

import core.controlled_runtime_queue_admission_record_consumption as public
from core.controlled_runtime_queue_admission_record_consumption.policy import (
    ADMISSION_CLASS,
    BOUNDARY_KIND,
    CLAIM_SCHEMA_NAME,
    CONSUMPTION_INTENT,
    PRIORITY_CLASS,
    REASON_CODES,
    REGISTRY_SCHEMA_NAME,
    REQUEST_SCHEMA_NAME,
    RESULT_SCHEMA_NAME,
    SUCCESS_STATUS,
    VERIFICATION_SCHEMA_NAME,
    ControlledRuntimeQueueAdmissionRecordConsumptionPolicy,
)


def test_exact_public_api():
    assert public.__all__ == [
        "ControlledRuntimeQueueAdmissionRecordConsumptionRequest",
        "ControlledRuntimeQueueAdmissionRecordConsumptionClaim",
        "ControlledRuntimeQueueAdmissionRecordConsumptionResult",
        "ControlledRuntimeQueueAdmissionRecordConsumptionVerificationResult",
        "ControlledRuntimeQueueAdmissionRecordConsumptionPolicy",
        "ControlledRuntimeQueueAdmissionRecordConsumptionRegistry",
        "ControlledRuntimeQueueAdmissionRecordConsumer",
        "verify_controlled_runtime_queue_admission_record_consumption",
        "QueueAdmissionRecordConsumptionError",
        "QueueAdmissionRecordConsumptionPathError",
        "QueueAdmissionRecordConsumptionSchemaError",
        "QueueAdmissionRecordConsumptionIntegrityError",
        "QueueAdmissionRecordAlreadyConsumedError",
        "QueueAdmissionRecordConsumptionConflictError",
        "QueueAdmissionRecordConsumptionCommitError",
        "QueueAdmissionRecordConsumptionVerificationError",
    ]


def test_exact_schemas_policy_and_reason_codes():
    assert REQUEST_SCHEMA_NAME == (
        "ntpe.controlled_runtime_queue_admission_record_consumption_request"
    )
    assert CLAIM_SCHEMA_NAME == (
        "ntpe.controlled_runtime_queue_admission_record_consumption_claim"
    )
    assert RESULT_SCHEMA_NAME == (
        "ntpe.controlled_runtime_queue_admission_record_consumption_result"
    )
    assert VERIFICATION_SCHEMA_NAME == (
        "ntpe.controlled_runtime_queue_admission_record_consumption_verification_result"
    )
    assert REGISTRY_SCHEMA_NAME == (
        "ntpe.controlled_runtime_queue_admission_record_consumption_registry"
    )
    assert BOUNDARY_KIND == "controlled_offline_acceptance_boundary"
    assert CONSUMPTION_INTENT == (
        "consume_exactly_one_authentic_prepared_queue_admission_record"
    )
    assert SUCCESS_STATUS == "queue_admission_record_consumed_not_admitted"
    assert ADMISSION_CLASS == "controlled_runtime_single_unit"
    assert PRIORITY_CLASS == "controlled_default"
    assert len(REASON_CODES) == 24
    assert len(set(REASON_CODES)) == len(REASON_CODES)
    policy = ControlledRuntimeQueueAdmissionRecordConsumptionPolicy()
    assert (policy.upstream_chain_layers, policy.complete_chain_layers) == (31, 33)


def test_sqlite_is_confined_to_registry_and_active_runtime_is_absent():
    root = Path(inspect.getfile(public)).parent
    sources = {
        path.name: path.read_text(encoding="utf-8").lower()
        for path in root.glob("*.py")
    }
    assert "import sqlite3" in sources["registry.py"]
    for name, source in sources.items():
        if name != "registry.py":
            assert "import sqlite" not in source
    combined = "\n".join(sources.values())
    for token in (
        "import requests",
        "import httpx",
        "import subprocess",
        "import asyncio",
        "threadpoolexecutor",
        "provider.execute",
        "translator.translate",
        "scheduler.schedule",
    ):
        assert token not in combined


def test_production_uses_authentic_stage612_api_and_official_verifier():
    root = Path(inspect.getfile(public)).parent
    consumer = (root / "consumer.py").read_text(encoding="utf-8")
    verifier = (root / "verification.py").read_text(encoding="utf-8")
    expected = (
        "from core.controlled_runtime_queue_admission_record import ("
    )
    assert expected in consumer
    assert expected in verifier
    assert "verify_controlled_runtime_queue_admission_record(" in consumer
    assert "verify_controlled_runtime_queue_admission_record(" in verifier
