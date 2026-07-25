from core.adaptive_context_single_real_invocation import FakeSingleInvocationTransport
from core.controlled_multi_chunk_translation_canary import (
    ControlledMultiChunkExecutor, ControlledMultiChunkQualityError,
    read_checkpoint, verify_multi_chunk_result,
)
import pytest
from tests.unit.controlled_multi_chunk_translation_canary import (
    FAKE_OUTPUTS, build_context,
)


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

def test_chunk2_dialogue_failure_stops_before_chunk3_integration(tmp_path):
    bad_dialogue = FAKE_OUTPUTS[1].replace("「", "“").replace("」", "”")
    outputs = (FAKE_OUTPUTS[0], bad_dialogue, FAKE_OUTPUTS[2])
    context = build_context(tmp_path, outputs=outputs)
    starts = []
    context["transport_factory"] = lambda index: (
        starts.append(index)
        or FakeSingleInvocationTransport(outputs=(outputs[index - 1],))
    )
    with pytest.raises(ControlledMultiChunkQualityError):
        ControlledMultiChunkExecutor().execute(**context)
    root = context["artifact_root"]
    assert starts == [1, 2]
    assert len(list(root.glob("chunk-*.translated.txt"))) == 1
    assert len(list(root.glob("checkpoint-*.json"))) == 1
    assert not (root / "combined.translated.txt").exists()
