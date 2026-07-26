import hashlib

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


def test_narration_only_valid_output_does_not_false_fail_integration(tmp_path):
    context = build_context(tmp_path)
    result = ControlledMultiChunkExecutor().execute(**context)
    assert result.chunk_evidence[0].dialogue_punctuation_passed is True
    assert result.chunk_evidence[2].dialogue_punctuation_passed is True


def test_assessed_output_bytes_equal_persisted_bytes_integration(
    tmp_path, monkeypatch,
):
    assessed = []
    original = ControlledMultiChunkExecutor._quality_assessment

    def recording_assessment(source, translated):
        assessed.append(translated.encode("utf-8"))
        return original(source, translated)

    monkeypatch.setattr(
        ControlledMultiChunkExecutor,
        "_quality_assessment",
        staticmethod(recording_assessment),
    )
    context = build_context(tmp_path)
    result = ControlledMultiChunkExecutor().execute(**context)
    persisted = [
        (
            context["artifact_root"] / evidence.output_artifact_path
        ).read_bytes()
        for evidence in result.chunk_evidence
    ]
    assert assessed == persisted
    assert [hashlib.sha256(value).hexdigest() for value in assessed] == [
        evidence.output_fingerprint for evidence in result.chunk_evidence
    ]
