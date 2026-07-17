from pathlib import Path

from core.lcr_production_shadow_hook.single_chunk_dual_pass_executor import execute_single_chunk_dual_pass_review
from tests.unit.test_lcr_single_chunk_dual_pass_executor import ENABLED, FakeProvider, auth_for, target
from tests.unit.test_lcr_single_chunk_execution_authorization import NOW


def test_authorized_single_chunk_review_end_to_end_keeps_formal_adapters_unchanged(tmp_path):
    sentinels = {}
    for name in ("output", "resume", "cache", "character_store", "context_store"):
        path = tmp_path / f"{name}.sentinel"; path.write_text(f"unchanged-{name}", encoding="utf-8"); sentinels[path] = path.read_bytes()
    item = target(); provider = FakeProvider()
    result = execute_single_chunk_dual_pass_review(authorization=auth_for(item), target=item, planning="dual_pass_candidate",
        provider=provider, artifact_directory=str(tmp_path / "isolated-review"), now=NOW, provider_id="fake-provider",
        model_id="fake-model", feature_flags=ENABLED)
    assert result.outcome == "verified_candidate" and len(provider.calls) == 2
    assert result.provider_requests == 2 and result.network_requests == 0 and Path(result.artifact_path).parent == (tmp_path / "isolated-review").resolve()
    assert all(path.read_bytes() == before for path, before in sentinels.items())
    assert result.formal_translation_replaced is False and result.active_production_authorized is False
