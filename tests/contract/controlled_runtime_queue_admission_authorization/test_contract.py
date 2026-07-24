import inspect
from pathlib import Path

import core.controlled_runtime_queue_admission_authorization as public
from core.controlled_runtime_queue_admission_authorization.policy import *


def test_exact_public_api_and_schemas():
    assert public.__all__ == [
        "ControlledRuntimeQueueAdmissionAuthorizationRequest",
        "ControlledRuntimeQueueAdmissionAuthorizationDecision",
        "ControlledRuntimeQueueAdmissionAuthorizationResult",
        "ControlledRuntimeQueueAdmissionAuthorizationVerificationResult",
        "ControlledRuntimeQueueAdmissionAuthorizationPolicy",
        "ControlledRuntimeQueueAdmissionAuthorizer",
        "verify_controlled_runtime_queue_admission_authorization",
        "QueueAdmissionAuthorizationError",
        "QueueAdmissionAuthorizationRequestError",
        "QueueAdmissionAuthorizationUpstreamError",
        "QueueAdmissionAuthorizationVerificationError",
    ]
    assert REQUEST_SCHEMA_NAME == "ntpe.controlled_runtime_queue_admission_authorization_request"
    assert DECISION_SCHEMA_NAME == "ntpe.controlled_runtime_queue_admission_authorization_decision"
    assert RESULT_SCHEMA_NAME == "ntpe.controlled_runtime_queue_admission_authorization_result"


def test_production_has_no_durable_or_active_runtime_dependencies():
    root = Path(inspect.getfile(public)).parent
    source = "\n".join(path.read_text(encoding="utf-8").lower() for path in root.glob("*.py"))
    for token in (
        "import sqlite3", "atomic_scheduling_consumption.registry",
        "scheduling_envelope_consumption.registry", "import subprocess",
        "import asyncio", "threadpoolexecutor", "runtime executor",
    ):
        assert token not in source
