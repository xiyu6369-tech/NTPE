from tests.unit.test_lcr_bounded_dual_pass_pilot import auth
from core.lcr_production_shadow_hook.pilot_authorization import validate_authorization
def test_expired_and_hash_mismatch_are_blocked():
 assert not validate_authorization(auth(expires_at='2026-07-17T00:00:00Z'),document_id='d',chunk_id='c',source_hash='a'*64,provider_id='p',model_id='m',now='2026-07-18T00:00:00Z')[0]
 assert not validate_authorization(auth(),document_id='d',chunk_id='c',source_hash='b'*64,provider_id='p',model_id='m',now='2026-07-18T00:00:00Z')[0]
def test_all_negative_authorization_branches_fail_closed():
 for change in ({'authorized_at':'bad'},{'authorized_at':'2026-07-20T00:00:00Z'},{'expires_at':'2026-07-18T00:00:00Z'},{'draft_request_limit':2},{'timeout_seconds':26},{'retry_limit':2},{'fallback_allowed':True},{'rollback_required':False},{'explicit_execution_authorization':False}):
  assert not validate_authorization(auth(**change),document_id='d',chunk_id='c',source_hash='a'*64,provider_id='p',model_id='m',now='2026-07-18T01:00:00Z')[0]
 for key,val in [('document_id','x'),('chunk_id','x'),('provider_id','x'),('model_id','x')]:
  args=dict(document_id='d',chunk_id='c',source_hash='a'*64,provider_id='p',model_id='m');args[key]=val
  assert not validate_authorization(auth(),now='2026-07-18T01:00:00Z',**args)[0]
