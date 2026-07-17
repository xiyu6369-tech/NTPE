from __future__ import annotations
import json
from tests.unit.test_lcr_character_memory_shadow import package
from tests.unit.test_lcr_dual_pass_semantic_shadow import ENABLED,metadata
import core.lcr_production_shadow_hook as lcr
def test_batch104_harness_preserves_production_result_and_never_generates_text():
    value=package("ko");before=json.dumps(value,sort_keys=True);out=lcr.run_read_only_lcr_shadow_hook(value,feature_flags=ENABLED,dual_pass_semantic_metadata=metadata())
    result=out.evidence.dual_pass_semantic
    assert out.status=="completed" and result.shadow_only and not result.active_integration
    assert not any((result.provider_executed,result.network_requests,result.new_translation_generated,result.draft_generated,result.polish_generated,result.translation_replaced,result.prompt_modified,result.resume_modified,result.output_modified,result.cache_modified))
    assert json.dumps(value,sort_keys=True)==before
