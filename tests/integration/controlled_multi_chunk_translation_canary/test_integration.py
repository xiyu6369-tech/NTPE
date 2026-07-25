from core.controlled_multi_chunk_translation_canary import (
    ControlledMultiChunkExecutor, read_checkpoint, verify_multi_chunk_result,
)
from tests.unit.controlled_multi_chunk_translation_canary import build_context


def test_authentic_three_chunk_zero_network_integration(tmp_path):
    context = build_context(tmp_path)
    result = ControlledMultiChunkExecutor().execute(**context)
    assert result.provider_requests == result.provider_attempts == 3
    assert result.provider_successes == result.translation_executions == 3
    assert result.retries == result.fallbacks == 0
    assert len(result.chunk_evidence) == 3
    assert all(item.quality_passed for item in result.chunk_evidence)
    assert [
        read_checkpoint(context["artifact_root"] / f"checkpoint-{index:03d}.json").completed_chunk_count
        for index in (1, 2, 3)
    ] == [1, 2, 3]
    assert verify_multi_chunk_result(
        context["request"], result,
        artifact_root=context["artifact_root"],
        raise_on_error=True,
    ).valid
