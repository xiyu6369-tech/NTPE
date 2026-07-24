"""Immutable deterministic Stage 6.11 models."""
from dataclasses import dataclass,field
from .policy import *
from .serialization import canonical_json,canonical_sha256,values
_HEX=frozenset("0123456789abcdef")
def _text(n,v):
    if not isinstance(v,str) or not v.strip(): raise ValueError(f"{n} must be non-empty")
def _fp(n,v):
    if not isinstance(v,str) or len(v)!=64 or any(c not in _HEX for c in v): raise ValueError(f"{n} must be SHA-256")
def _id(prefix,payload): return f"{prefix}-{canonical_sha256(payload)[:32]}"

@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionAuthorizationConsumptionRequest:
    authorization_id:str
    decision_fingerprint:str
    authorization_request_id:str
    authorization_request_fingerprint:str
    stage69_consumption_claim_id:str
    stage69_claim_fingerprint:str
    scheduling_envelope_id:str
    scheduling_envelope_fingerprint:str
    stage67_consumption_claim_id:str
    stage67_claim_fingerprint:str
    stage66_scheduling_authorization_id:str
    stage66_decision_fingerprint:str
    runtime_boundary_id:str
    runtime_boundary_kind:str
    selected_adapter_index:int
    capability_state_fingerprint:str
    unit_scope:int
    upstream_chain:tuple[str,...]
    consumption_intent:str=CONSUMPTION_INTENT
    schema_name:str=REQUEST_SCHEMA_NAME
    schema_version:str=REQUEST_SCHEMA_VERSION
    consumption_request_id:str=field(default="",init=False)
    request_fingerprint:str=field(default="",init=False)
    def __post_init__(self):
        if (self.schema_name,self.schema_version)!=(REQUEST_SCHEMA_NAME,REQUEST_SCHEMA_VERSION): raise ValueError("invalid request schema")
        for n in ("authorization_id","authorization_request_id","stage69_consumption_claim_id","scheduling_envelope_id","stage67_consumption_claim_id","stage66_scheduling_authorization_id","runtime_boundary_id"): _text(n,getattr(self,n))
        for n in ("decision_fingerprint","authorization_request_fingerprint","stage69_claim_fingerprint","scheduling_envelope_fingerprint","stage67_claim_fingerprint","stage66_decision_fingerprint","capability_state_fingerprint"): _fp(n,getattr(self,n))
        if self.runtime_boundary_kind!=BOUNDARY_KIND: raise ValueError("invalid boundary kind")
        if type(self.selected_adapter_index) is not int or self.selected_adapter_index<0: raise TypeError("adapter index must be int")
        if type(self.unit_scope) is not int: raise TypeError("unit_scope must be int")
        if self.unit_scope!=1: raise ValueError("unit_scope must be 1")
        if self.consumption_intent!=CONSUMPTION_INTENT: raise ValueError("invalid consumption intent")
        if not isinstance(self.upstream_chain,tuple) or len(self.upstream_chain)!=27: raise ValueError("upstream chain must have 27 layers")
        for i,v in enumerate(self.upstream_chain): _fp(f"chain[{i}]",v)
        ident=_id("stage611-request",values(self,("consumption_request_id","request_fingerprint")))
        object.__setattr__(self,"consumption_request_id",ident)
        object.__setattr__(self,"request_fingerprint",canonical_sha256(values(self,("request_fingerprint",))))
    def to_json(self): return canonical_json(values(self))

@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionAuthorizationConsumptionClaim:
    consumption_request_id:str
    consumption_request_fingerprint:str
    authorization_id:str
    decision_fingerprint:str
    authorization_request_id:str
    authorization_request_fingerprint:str
    stage69_consumption_claim_id:str
    stage69_claim_fingerprint:str
    scheduling_envelope_id:str
    scheduling_envelope_fingerprint:str
    stage67_consumption_claim_id:str
    stage67_claim_fingerprint:str
    stage66_scheduling_authorization_id:str
    stage66_decision_fingerprint:str
    runtime_boundary_id:str
    runtime_boundary_kind:str
    selected_adapter_index:int
    capability_state_fingerprint:str
    unit_scope:int
    scheduling_authorization_consumed:bool
    scheduling_envelope_prepared:bool
    scheduling_envelope_consumed:bool
    scheduling_envelope_reusable:bool
    queue_admission_authorized:bool
    queue_admission_authorization_consumed:bool
    queue_admission_authorization_reusable:bool
    queue_admission_record_prepared:bool
    queue_admission_record_consumed:bool
    queue_record_created:bool
    runtime_execution_scheduled:bool
    execution_started:bool
    persistent_registry_written:bool
    canonical_chain:tuple[str,...]
    claim_state:str=SUCCESS_STATUS
    schema_name:str=CLAIM_SCHEMA_NAME
    schema_version:str=CLAIM_SCHEMA_VERSION
    consumption_claim_id:str=field(default="",init=False)
    claim_fingerprint:str=field(default="",init=False)
    def __post_init__(self):
        if (self.schema_name,self.schema_version)!=(CLAIM_SCHEMA_NAME,CLAIM_SCHEMA_VERSION): raise ValueError("invalid claim schema")
        expected={"scheduling_authorization_consumed":True,"scheduling_envelope_prepared":True,"scheduling_envelope_consumed":True,"scheduling_envelope_reusable":False,"queue_admission_authorized":True,"queue_admission_authorization_consumed":True,"queue_admission_authorization_reusable":False,"queue_admission_record_prepared":False,"queue_admission_record_consumed":False,"queue_record_created":False,"runtime_execution_scheduled":False,"execution_started":False,"persistent_registry_written":True}
        for n,e in expected.items():
            if type(getattr(self,n)) is not bool or getattr(self,n) is not e: raise ValueError(f"{n} invariant")
        if self.claim_state!=SUCCESS_STATUS or type(self.unit_scope) is not int or self.unit_scope!=1: raise ValueError("claim invariant")
        if not isinstance(self.canonical_chain,tuple) or len(self.canonical_chain) not in (28,29): raise ValueError("claim chain must have 28/29 layers")
        pre=self.canonical_chain[:28]
        ident=_id("stage611-claim",self._payload(pre,""))
        object.__setattr__(self,"consumption_claim_id",ident)
        fp=canonical_sha256(self._payload(pre,ident))
        object.__setattr__(self,"claim_fingerprint",fp)
        object.__setattr__(self,"canonical_chain",pre+(fp,))
    def _payload(self,chain,ident):
        p=values(self,("consumption_claim_id","claim_fingerprint","canonical_chain"));p["consumption_claim_id"]=ident;p["canonical_chain"]=list(chain);return p
    def to_json(self): return canonical_json(values(self))

@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionAuthorizationConsumptionVerificationResult:
    valid:bool; schema_verified:bool; identity_verified:bool; fingerprint_verified:bool; upstream_verified:bool; binding_verified:bool; chain_verified:bool; state_verified:bool; persistence_verified:bool; canonical_payload_verified:bool; reason_codes:tuple[str,...]
    schema_name:str=VERIFICATION_SCHEMA_NAME; schema_version:str=VERIFICATION_SCHEMA_VERSION

@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionAuthorizationConsumptionResult:
    request:ControlledRuntimeQueueAdmissionAuthorizationConsumptionRequest
    claim:ControlledRuntimeQueueAdmissionAuthorizationConsumptionClaim|None
    verification_succeeded:bool
    upstream_verified:bool
    durable_claim_created:bool
    exactly_one_authorization_consumed:bool
    replay_detected:bool
    persistence_committed:bool
    durable_readback_verified:bool
    status:str
    reason_codes:tuple[str,...]
    authorization_consumption_count:int
    queue_admission_count:int=0
    queue_record_prepared_count:int=0
    queue_record_created_count:int=0
    scheduler_count:int=0
    runtime_execution_count:int=0
    provider_execution_count:int=0
    network_execution_count:int=0
    translation_execution_count:int=0
    schema_name:str=RESULT_SCHEMA_NAME
    schema_version:str=RESULT_SCHEMA_VERSION
