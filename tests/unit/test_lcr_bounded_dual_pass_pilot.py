from core.lcr_production_shadow_hook.bounded_dual_pass_pilot import prepare_bounded_dual_pass_pilot
from core.lcr_production_shadow_hook.pilot_authorization import PilotAuthorization
class Plan: eligibility='dual_pass_candidate'
def auth(**k):
 d=dict(authorization_id='a',authorized_by='human',authorized_at='2026-07-18T00:00:00Z',expires_at='2026-07-19T00:00:00Z',target_document_id='d',target_chunk_id='c',source_hash='a'*64,provider_id='p',model_id='m',explicit_execution_authorization=True);d.update(k);return PilotAuthorization(**d)
def test_preparation_package_is_metadata_only_and_never_executes():
 r=prepare_bounded_dual_pass_pilot(planning=Plan(),authorization=auth(),document_id='d',chunk_id='c',source_hash='a'*64,provider_id='p',model_id='m',now='2026-07-18T01:00:00Z',rollback_baseline_hash='b'*64)
 assert r.status=='prepared' and r.provider_requests==r.network_requests==0
 assert not any(x in repr(r.package).lower() for x in ('source_text','prompt','translation','secret'))
 assert r.package['output_replacement_allowed'] is r.package['resume_write_allowed'] is r.package['cache_write_allowed'] is False
def test_bypass_authorization_is_blocked_without_side_effects():
 r=prepare_bounded_dual_pass_pilot(planning=Plan(),authorization=auth(output_replacement_allowed=True,resume_write_allowed=True,cache_write_allowed=True,provider_execution=True),document_id='d',chunk_id='c',source_hash='a'*64,provider_id='p',model_id='m',now='2026-07-18T01:00:00Z',rollback_baseline_hash='b'*64)
 assert r.status=='blocked' and r.provider_requests==r.network_requests==0 and not r.output_modified and not r.resume_modified and not r.cache_modified
def test_prepare_gate_and_package_immutability():
 base=dict(planning=Plan(),document_id='d',chunk_id='c',source_hash='a'*64,provider_id='p',model_id='m',now='2026-07-18T01:00:00Z',rollback_baseline_hash='b'*64)
 for change in ({'authorization':None},{'authorization':auth(),'target_count':0},{'authorization':auth(),'target_count':2},{'authorization':auth(),'rollback_baseline_hash':''}):
  args=dict(base);args.update(change);assert prepare_bounded_dual_pass_pilot(**args).status=='blocked'
 class Bad: eligibility='single_pass_sufficient'
 assert prepare_bounded_dual_pass_pilot(**{**base,'planning':Bad(),'authorization':auth()}).status=='blocked'
 one=prepare_bounded_dual_pass_pilot(**{**base,'authorization':auth()});two=prepare_bounded_dual_pass_pilot(**{**base,'authorization':auth()})
 assert dict(one.package)==dict(two.package)
 import pytest
 with pytest.raises(TypeError): one.package['x']=1
