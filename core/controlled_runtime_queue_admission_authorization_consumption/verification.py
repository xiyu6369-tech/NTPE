"""Stage 6.11 offline verification."""
from core.controlled_runtime_queue_admission_authorization import *
from .errors import QueueAdmissionAuthorizationConsumptionVerificationError
from .models import *
from .models import _id
from .policy import *
from .serialization import canonical_sha256,values
def verify_controlled_runtime_queue_admission_authorization_consumption(claim,*,request,stage610_decision,stage610_request,stage610_result,stage610_verification_context,persisted_payload_json=None,persistence_committed=False,raise_on_error=False):
    if not isinstance(claim,ControlledRuntimeQueueAdmissionAuthorizationConsumptionClaim): raise TypeError("claim type")
    if not isinstance(request,ControlledRuntimeQueueAdmissionAuthorizationConsumptionRequest): raise TypeError("request type")
    if not isinstance(stage610_decision,ControlledRuntimeQueueAdmissionAuthorizationDecision): raise TypeError("decision type")
    upstream=verify_controlled_runtime_queue_admission_authorization(stage610_decision,request=stage610_request,**stage610_verification_context)
    schema=(claim.schema_name,claim.schema_version)==(CLAIM_SCHEMA_NAME,CLAIM_SCHEMA_VERSION)
    rid=_id("stage611-request",values(request,("consumption_request_id","request_fingerprint")))
    rfp=canonical_sha256(values(request,("request_fingerprint",)))
    cid=_id("stage611-claim",claim._payload(claim.canonical_chain[:28],""))
    cfp=canonical_sha256(claim._payload(claim.canonical_chain[:28],claim.consumption_claim_id))
    identity=request.consumption_request_id==rid and claim.consumption_claim_id==cid
    fingerprint=request.request_fingerprint==rfp and claim.claim_fingerprint==cfp
    upstream_ok=upstream.valid and stage610_result.decision==stage610_decision and stage610_result.request==stage610_request and stage610_result.authorized and stage610_result.decision_count==1
    binding=all((request.authorization_id==stage610_decision.authorization_id,request.decision_fingerprint==stage610_decision.decision_fingerprint,request.authorization_request_id==stage610_request.authorization_request_id,request.stage69_claim_fingerprint==stage610_decision.stage69_claim_fingerprint,request.scheduling_envelope_fingerprint==stage610_decision.scheduling_envelope_fingerprint,request.stage67_claim_fingerprint==stage610_decision.stage67_claim_fingerprint,request.stage66_decision_fingerprint==stage610_decision.stage66_decision_fingerprint,request.runtime_boundary_id==stage610_decision.runtime_boundary_id,request.selected_adapter_index==stage610_decision.selected_adapter_index,request.capability_state_fingerprint==stage610_decision.capability_state_fingerprint))
    chain=len(claim.canonical_chain)==29 and tuple(request.upstream_chain)==tuple(stage610_decision.canonical_chain) and tuple(claim.canonical_chain[:27])==tuple(request.upstream_chain) and claim.canonical_chain[27]==request.request_fingerprint and claim.canonical_chain[28]==claim.claim_fingerprint
    state=all((stage610_decision.queue_admission_authorized,not stage610_decision.queue_admission_authorization_consumed,not stage610_decision.queue_record_created,not stage610_decision.runtime_execution_scheduled,not stage610_decision.execution_started,claim.queue_admission_authorized,claim.queue_admission_authorization_consumed,not claim.queue_admission_authorization_reusable,not claim.queue_admission_record_prepared,not claim.queue_admission_record_consumed,not claim.queue_record_created,not claim.runtime_execution_scheduled,not claim.execution_started))
    persist=persistence_committed is True;payload=persisted_payload_json==claim.to_json()
    checks=(("INVALID_SCHEMA",schema),("INVALID_IDENTITY",identity),("FINGERPRINT_MISMATCH",fingerprint),("UPSTREAM_VERIFICATION_FAILED",upstream_ok),("BINDING_MISMATCH",binding),("CHAIN_MISMATCH",chain),("UPSTREAM_STATE_MISMATCH",state),("PERSISTENCE_NOT_PROVEN",persist),("CANONICAL_PAYLOAD_MISMATCH",payload))
    reasons=tuple(c for c,v in checks if not v)
    result=ControlledRuntimeQueueAdmissionAuthorizationConsumptionVerificationResult(not reasons,schema,identity,fingerprint,upstream_ok,binding,chain,state,persist,payload,reasons)
    if raise_on_error and reasons: raise QueueAdmissionAuthorizationConsumptionVerificationError(",".join(reasons))
    return result
