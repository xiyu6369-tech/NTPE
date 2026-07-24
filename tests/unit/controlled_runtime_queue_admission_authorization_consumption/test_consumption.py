from dataclasses import FrozenInstanceError,replace
import sqlite3,pytest
from core.controlled_runtime_queue_admission_authorization_consumption import *
from core.controlled_runtime_queue_admission_authorization_consumption.policy import *
from core.controlled_runtime_queue_admission_authorization_consumption.registry import TABLE
from core.controlled_runtime_queue_admission_authorization_consumption.serialization import canonical_json
from tests.unit.controlled_runtime_queue_admission_authorization_consumption import build_context
def test_first_success_replay_and_29_layers(tmp_path):
    c=build_context(tmp_path);consumer=ControlledRuntimeQueueAdmissionAuthorizationConsumer();a=consumer.consume(**c);b=consumer.consume(**c)
    assert a.claim and len(a.claim.canonical_chain)==29 and a.exactly_one_authorization_consumed
    assert b.replay_detected and b.claim is None
    reg=ControlledRuntimeQueueAdmissionAuthorizationConsumptionRegistry(c["database_path"],allowed_root=tmp_path)
    assert reg.count_claims()==1 and reg.read(c["request"].consumption_request_id)==a.claim
    with pytest.raises(FrozenInstanceError):a.claim.queue_record_created=True
@pytest.mark.parametrize("scope",[True,False,0,-1,2,1.0,"1"])
def test_scope_strict(tmp_path,scope):
    with pytest.raises((TypeError,ValueError)):build_context(tmp_path,unit_scope=scope)
def test_intent_and_canonical_newlines(tmp_path):
    assert build_context(tmp_path)["request"].consumption_intent==CONSUMPTION_INTENT
    assert canonical_json({"字":"甲\r\n乙"})==canonical_json({"字":"甲\n乙"})
@pytest.mark.parametrize("field",["decision_fingerprint","authorization_request_fingerprint","stage69_claim_fingerprint","scheduling_envelope_fingerprint","stage67_claim_fingerprint","stage66_decision_fingerprint","runtime_boundary_id","capability_state_fingerprint"])
def test_tamper_denied(tmp_path,field):
    c=build_context(tmp_path);v=getattr(c["request"],field);object.__setattr__(c["request"],field,"0"*64 if len(v)==64 else v+"x")
    assert not ControlledRuntimeQueueAdmissionAuthorizationConsumer().consume(**c).claim
@pytest.mark.parametrize("kind",["missing","extra","duplicate","reordered"])
def test_chain_tamper(tmp_path,kind):
    c=build_context(tmp_path);x=list(c["request"].upstream_chain)
    if kind=="missing":x.pop()
    elif kind=="extra":x.append(x[-1])
    elif kind=="duplicate":x[1]=x[0]
    else:x[0],x[1]=x[1],x[0]
    if len(x)!=27:
        with pytest.raises(ValueError):replace(c["request"],upstream_chain=tuple(x))
    else:
        c["request"]=replace(c["request"],upstream_chain=tuple(x));assert not ControlledRuntimeQueueAdmissionAuthorizationConsumer().consume(**c).claim
def test_rollback(tmp_path,monkeypatch):
    c=build_context(tmp_path)
    def fail(point):
        if point=="after_insert":raise RuntimeError()
    injected=ControlledRuntimeQueueAdmissionAuthorizationConsumptionRegistry(c["database_path"],allowed_root=tmp_path,failure_injector=fail)
    original=ControlledRuntimeQueueAdmissionAuthorizationConsumptionRegistry.claim
    monkeypatch.setattr(ControlledRuntimeQueueAdmissionAuthorizationConsumptionRegistry,"claim",lambda self,r,q:original(injected,r,q))
    assert ControlledRuntimeQueueAdmissionAuthorizationConsumer().consume(**c).status=="registry_error"
    monkeypatch.setattr(ControlledRuntimeQueueAdmissionAuthorizationConsumptionRegistry,"claim",original)
    assert ControlledRuntimeQueueAdmissionAuthorizationConsumptionRegistry(c["database_path"],allowed_root=tmp_path).count_claims()==0
def test_paths_and_malformed_row(tmp_path):
    with pytest.raises(QueueAdmissionAuthorizationConsumptionPathError):ControlledRuntimeQueueAdmissionAuthorizationConsumptionRegistry("../x.db",allowed_root=tmp_path)
    with pytest.raises(TypeError):ControlledRuntimeQueueAdmissionAuthorizationConsumptionRegistry()
    c=build_context(tmp_path);r=ControlledRuntimeQueueAdmissionAuthorizationConsumer().consume(**c);assert r.claim
    con=sqlite3.connect(c["database_path"]);con.execute(f"UPDATE {TABLE} SET claim_payload_json='{{}}'");con.commit();con.close()
    with pytest.raises(QueueAdmissionAuthorizationConsumptionIntegrityError):ControlledRuntimeQueueAdmissionAuthorizationConsumptionRegistry(c["database_path"],allowed_root=tmp_path).read(c["request"].consumption_request_id)
