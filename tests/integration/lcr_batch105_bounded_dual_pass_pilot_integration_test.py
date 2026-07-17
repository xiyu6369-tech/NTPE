from tests.unit.test_lcr_bounded_dual_pass_pilot import Plan,auth
from core.lcr_production_shadow_hook.bounded_dual_pass_pilot import prepare_bounded_dual_pass_pilot
def test_preparation_mode_calls_no_sentinels_and_mutates_nothing(tmp_path):
 output=tmp_path/'output';resume=tmp_path/'resume';cache=tmp_path/'cache'
 r=prepare_bounded_dual_pass_pilot(planning=Plan(),authorization=auth(),document_id='d',chunk_id='c',source_hash='a'*64,provider_id='p',model_id='m',now='2026-07-18T01:00:00Z',rollback_baseline_hash='b'*64)
 assert r.status=='prepared' and not output.exists() and not resume.exists() and not cache.exists() and r.provider_requests==r.network_requests==0
 assert 'provider' not in prepare_bounded_dual_pass_pilot.__code__.co_names
