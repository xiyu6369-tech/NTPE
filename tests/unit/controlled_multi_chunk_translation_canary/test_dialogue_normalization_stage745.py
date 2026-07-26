import hashlib
from pathlib import Path
import socket

import pytest

from core.controlled_multi_chunk_translation_canary import (
    ControlledMultiChunkExecutor,
    normalize_stage74_dialogue_quotes,
    resolve_multi_chunk_source,
)
from core.translation_runtime import format_translation_output
from tests.unit.controlled_multi_chunk_translation_canary import (
    FAKE_OUTPUTS,
    build_context,
)


SOURCE_ONE = "“첫째.” 그가 말했다."
SOURCE_TWO = "“첫째.” 그가 말했다. “둘째.”"


def _normalize(source, candidate):
    return normalize_stage74_dialogue_quotes(source, candidate)


def test_balanced_chinese_dialogue_curly_quotes_convert_to_corner_quotes():
    result = _normalize(SOURCE_ONE, "他只答了一句“當然。”")
    assert result.normalized_text == "他只答了一句「當然。」"
    assert result.changed is result.eligible is True
    assert result.converted_pair_count == 1


def test_multiple_dialogue_pairs_convert_without_reordering_words():
    raw = "“第一句。”他平靜地說。“第二句！”"
    result = _normalize(SOURCE_TWO, raw)
    assert result.normalized_text == "「第一句。」他平靜地說。「第二句！」"
    assert result.converted_pair_count == 2
    assert result.normalized_text.translate(str.maketrans("「」", "“”")) == raw


def test_already_canonical_and_nested_corner_quotes_are_byte_identical():
    canonical = "他說：「外層『內層』仍然有效。」"
    result = _normalize(SOURCE_ONE, canonical)
    assert result.normalized_text.encode("utf-8") == canonical.encode("utf-8")
    assert result.changed is False
    assert result.raw_candidate_fingerprint == result.normalized_candidate_fingerprint


def test_normalization_is_idempotent():
    first = _normalize(SOURCE_ONE, "他只答了一句“當然。”")
    second = _normalize(SOURCE_ONE, first.normalized_text)
    assert second.normalized_text == first.normalized_text
    assert second.changed is False


def test_only_quote_glyphs_change_and_speaker_attribution_is_preserved():
    raw = "鄭泰義低聲回答：“當然。”接著仍站在原地。"
    result = _normalize(SOURCE_ONE, raw)
    assert result.normalized_text == "鄭泰義低聲回答：「當然。」接著仍站在原地。"
    assert result.normalized_text.replace("「", "").replace("」", "") == (
        raw.replace("“", "").replace("”", "")
    )
    assert "鄭泰義低聲回答：" in result.normalized_text
    assert result.normalized_text.endswith("接著仍站在原地。")


def test_english_curly_quotation_remains_unchanged():
    raw = "The editor retained “This remains English prose.” exactly."
    result = _normalize(SOURCE_ONE, raw)
    assert result.normalized_text == raw
    assert result.eligible is False
    assert "non-chinese-curly-content" in result.reason_codes


@pytest.mark.parametrize(
    "candidate,reason",
    [
        ("他說“尚未結束。", "unmatched-curly-opening-quote"),
        ("他說尚未開始。”", "unmatched-curly-closing-quote"),
        ("他說“混合結束。」", "mixed-dialogue-quote-systems"),
        ("他說「混合結束。”", "mixed-dialogue-quote-systems"),
        ("他說“外層“內層。”結尾。”", "ambiguous-nested-curly-quote"),
    ],
)
def test_unsafe_or_ambiguous_quotes_are_unchanged_and_fail_closed(
    candidate, reason,
):
    result = _normalize(SOURCE_TWO, candidate)
    assert result.normalized_text == candidate
    assert result.changed is False
    assert result.eligible is False
    assert reason in result.reason_codes


def test_apostrophe_measurement_and_code_like_content_are_not_blindly_changed():
    raw = "O'Brien 記下 6” 測量值，並保留 {\"quote\": “內容。”}。"
    result = _normalize(SOURCE_ONE, raw)
    assert result.normalized_text == raw
    assert result.eligible is False


def test_dialogue_quality_runs_on_valid_post_normalization_bytes(tmp_path):
    context = build_context(tmp_path)
    resolved = resolve_multi_chunk_source(
        context["dispatch_package"], root=context["repository_root"]
    )
    raw = FAKE_OUTPUTS[1].replace("「", "“").replace("」", "”")
    normalized = _normalize(resolved.chunks[1], raw)
    assessment, metrics = ControlledMultiChunkExecutor._quality_assessment(
        resolved.chunks[1], normalized.normalized_text
    )
    assert normalized.changed is True
    assert assessment.dialogue_punctuation_passed is True
    assert assessment.quality_passed is True
    assert metrics["dialogue_punctuation_passed"] is True


def test_dialogue_quality_still_rejects_unsafe_mixed_input(tmp_path):
    context = build_context(tmp_path)
    resolved = resolve_multi_chunk_source(
        context["dispatch_package"], root=context["repository_root"]
    )
    unsafe = FAKE_OUTPUTS[1].replace("「", "“", 1)
    normalized = _normalize(resolved.chunks[1], unsafe)
    assessment, _ = ControlledMultiChunkExecutor._quality_assessment(
        resolved.chunks[1], normalized.normalized_text
    )
    assert normalized.changed is False
    assert "mixed-dialogue-quote-systems" in normalized.reason_codes
    assert assessment.dialogue_punctuation_passed is False
    assert assessment.quality_passed is False


def test_executor_persists_exact_assessed_post_normalization_bytes(tmp_path, monkeypatch):
    raw_chunk2 = FAKE_OUTPUTS[1].replace("「", "“").replace("」", "”")
    assessed = []
    original = ControlledMultiChunkExecutor._quality_assessment

    def record(source, translated):
        assessed.append(translated.encode("utf-8"))
        return original(source, translated)

    monkeypatch.setattr(
        ControlledMultiChunkExecutor,
        "_quality_assessment",
        staticmethod(record),
    )
    context = build_context(
        tmp_path,
        outputs=(FAKE_OUTPUTS[0], raw_chunk2, FAKE_OUTPUTS[2]),
    )
    result = ControlledMultiChunkExecutor().execute(**context)
    evidence = result.chunk_evidence[1]
    persisted = (
        context["artifact_root"] / evidence.output_artifact_path
    ).read_bytes()
    assert assessed[1] == persisted
    assert hashlib.sha256(persisted).hexdigest() == evidence.output_fingerprint
    assert evidence.dialogue_normalized_fingerprint == evidence.output_fingerprint
    assert evidence.raw_provider_candidate_fingerprint == hashlib.sha256(
        raw_chunk2.encode("utf-8")
    ).hexdigest()
    assert evidence.authentic_formatter_fingerprint == (
        evidence.raw_provider_candidate_fingerprint
    )


def test_real_stage744_chunk2_diagnostic_reproduces_pass_offline(tmp_path):
    repository = Path(__file__).resolve().parents[3]
    artifact = repository / (
        "artifacts/controlled_multi_chunk_translation_stage744/"
        "chunk-002.invalid-candidate.txt"
    )
    assert artifact.is_file(), "retained Stage 7.4.4 evidence is required"
    before = artifact.read_bytes()
    assert hashlib.sha256(before).hexdigest() == (
        "a4283478235d3c976f558e6a767cbf70e8b0491115b1d481d4af6805284e9d0f"
    )
    context = build_context(tmp_path)
    resolved = resolve_multi_chunk_source(
        context["dispatch_package"], root=context["repository_root"]
    )
    raw = before.decode("utf-8")
    authentic = format_translation_output(raw)
    normalized = _normalize(resolved.chunks[1], authentic)
    assessment, _ = ControlledMultiChunkExecutor._quality_assessment(
        resolved.chunks[1], normalized.normalized_text
    )
    assert normalized.changed is True
    assert normalized.converted_pair_count == 2
    assert assessment.dialogue_punctuation_passed is True
