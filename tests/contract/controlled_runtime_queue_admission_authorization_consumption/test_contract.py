import core.controlled_runtime_queue_admission_authorization_consumption as m
from core.controlled_runtime_queue_admission_authorization_consumption.policy import *
def test_public_api_and_schemas():
    assert len(m.__all__)==16
    assert REQUEST_SCHEMA_NAME=="ntpe.controlled_runtime_queue_admission_authorization_consumption_request"
    assert CLAIM_SCHEMA_NAME=="ntpe.controlled_runtime_queue_admission_authorization_consumption_claim"
    assert RESULT_SCHEMA_NAME=="ntpe.controlled_runtime_queue_admission_authorization_consumption_result"
    assert CONSUMPTION_INTENT=="consume_exactly_one_queue_admission_authorization"
def test_reason_codes_and_no_queue_api():
    assert len(REASON_CODES)==12 and len(set(REASON_CODES))==12
    assert not any("QueueAdmission" in name and "Consumer" not in name and "Authorization" not in name for name in m.__all__)
