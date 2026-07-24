"""Atomic Stage 6.11 consumer."""
from core.controlled_runtime_queue_admission_authorization import *
from .errors import *
from .models import *
from .policy import SUCCESS_STATUS
from .registry import ControlledRuntimeQueueAdmissionAuthorizationConsumptionRegistry
from .verification import verify_controlled_runtime_queue_admission_authorization_consumption
class ControlledRuntimeQueueAdmissionAuthorizationConsumer:
    def consume(self,request,*,stage610_decision,stage610_request,stage610_result,stage610_verification_context,database_path,allowed_root):
        if not isinstance(request,ControlledRuntimeQueueAdmissionAuthorizationConsumptionRequest): raise TypeError("request type")
        upstream=verify_controlled_runtime_queue_admission_authorization(stage610_decision,request=stage610_request,**stage610_verification_context)
        bindings=all((
            request.authorization_id==stage610_decision.authorization_id,
            request.decision_fingerprint==stage610_decision.decision_fingerprint,
            request.authorization_request_id==stage610_request.authorization_request_id,
            request.authorization_request_fingerprint==stage610_request.request_fingerprint,
            request.stage69_claim_fingerprint==stage610_decision.stage69_claim_fingerprint,
            request.scheduling_envelope_fingerprint==stage610_decision.scheduling_envelope_fingerprint,
            request.stage67_claim_fingerprint==stage610_decision.stage67_claim_fingerprint,
            request.stage66_decision_fingerprint==stage610_decision.stage66_decision_fingerprint,
            request.runtime_boundary_id==stage610_decision.runtime_boundary_id,
            request.selected_adapter_index==stage610_decision.selected_adapter_index,
            request.capability_state_fingerprint==stage610_decision.capability_state_fingerprint,
        ))
        if not upstream.valid or not stage610_result.authorized or stage610_result.decision!=stage610_decision or tuple(request.upstream_chain)!=tuple(stage610_decision.canonical_chain) or not bindings:
            return self._result(request,None,"rejected",("UPSTREAM_VERIFICATION_FAILED",))
        claim=ControlledRuntimeQueueAdmissionAuthorizationConsumptionClaim(
            consumption_request_id=request.consumption_request_id,consumption_request_fingerprint=request.request_fingerprint,
            **{n:getattr(request,n) for n in ("authorization_id","decision_fingerprint","authorization_request_id","authorization_request_fingerprint","stage69_consumption_claim_id","stage69_claim_fingerprint","scheduling_envelope_id","scheduling_envelope_fingerprint","stage67_consumption_claim_id","stage67_claim_fingerprint","stage66_scheduling_authorization_id","stage66_decision_fingerprint","runtime_boundary_id","runtime_boundary_kind","selected_adapter_index","capability_state_fingerprint","unit_scope")},
            scheduling_authorization_consumed=True,scheduling_envelope_prepared=True,scheduling_envelope_consumed=True,scheduling_envelope_reusable=False,queue_admission_authorized=True,queue_admission_authorization_consumed=True,queue_admission_authorization_reusable=False,queue_admission_record_prepared=False,queue_admission_record_consumed=False,queue_record_created=False,runtime_execution_scheduled=False,execution_started=False,persistent_registry_written=True,canonical_chain=tuple(request.upstream_chain)+(request.request_fingerprint,))
        registry=ControlledRuntimeQueueAdmissionAuthorizationConsumptionRegistry(database_path,allowed_root=allowed_root)
        try:stored=registry.claim(request,claim)
        except QueueAdmissionAuthorizationAlreadyConsumedError:return self._result(request,None,"already_consumed",("ALREADY_CONSUMED",),replay=True)
        except QueueAdmissionAuthorizationConsumptionError:return self._result(request,None,"registry_error",("REGISTRY_ERROR",))
        verification=verify_controlled_runtime_queue_admission_authorization_consumption(stored,request=request,stage610_decision=stage610_decision,stage610_request=stage610_request,stage610_result=stage610_result,stage610_verification_context=stage610_verification_context,persisted_payload_json=stored.to_json(),persistence_committed=True)
        if not verification.valid:return self._result(request,None,"verification_failed",verification.reason_codes)
        return self._result(request,stored,SUCCESS_STATUS,(),success=True)
    @staticmethod
    def _result(request,claim,status,reasons,success=False,replay=False):
        return ControlledRuntimeQueueAdmissionAuthorizationConsumptionResult(request,claim,success,success,success,success,replay,success,success,status,tuple(reasons),1 if success else 0)
