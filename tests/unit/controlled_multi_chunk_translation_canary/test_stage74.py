from dataclasses import FrozenInstanceError, replace
import hashlib
import json

import pytest

from core.adaptive_context_single_real_invocation import FakeSingleInvocationTransport
from core.controlled_multi_chunk_translation_canary import (
    ControlledMultiChunkAuthorityError, ControlledMultiChunkCheckpointError,
    ControlledMultiChunkExecutor, ControlledMultiChunkOutputError,
    ControlledMultiChunkProviderError, ControlledMultiChunkQualityError,
    ControlledMultiChunkVerificationError, read_checkpoint,
    resolve_multi_chunk_source, verify_chunk_quality_assessment,
    verify_multi_chunk_result,
)
from core.controlled_multi_chunk_translation_canary.verification import (
    assess_dialogue_punctuation,
)
from core.translation_runtime import format_translation_output
from core.controlled_multi_chunk_translation_canary.policy import (
    CHUNK_FINGERPRINTS, SOURCE_FINGERPRINT,
)
from tests.unit.controlled_multi_chunk_translation_canary import (
    FAKE_OUTPUTS, build_context,
)


def test_immutable_models_schemas_and_deterministic_identities(tmp_path):
    context = build_context(tmp_path)
    request = context["request"]
    resolved = resolve_multi_chunk_source(
        context["dispatch_package"], root=context["repository_root"]
    )
    assert request.schema == "ntpe.controlled_multi_chunk_translation_request"
    assert request.version == "1.0"
    assert request.request_id == replace(request).request_id
    assert request.request_fingerprint == replace(request).request_fingerprint
    assert tuple(plan.schema for plan in resolved.plans) == (
        "ntpe.controlled_translation_chunk_plan",
    ) * 3
    with pytest.raises(FrozenInstanceError):
        request.chunk_count = 4
    with pytest.raises(FrozenInstanceError):
        resolved.plans[0].index = 2


def test_exact_authentic_three_chunk_plan_and_bindings(tmp_path):
    context = build_context(tmp_path)
    resolved = resolve_multi_chunk_source(
        context["dispatch_package"], root=context["repository_root"]
    )
    plans = resolved.plans
    assert len(plans) == 3
    assert [plan.index for plan in plans] == [1, 2, 3]
    assert [(p.source_start, p.source_end) for p in plans] == [
        (0, 575), (577, 1117), (1119, 1633),
    ]
    assert [p.source_character_count for p in plans] == [575, 540, 514]
    assert tuple(p.chunk_fingerprint for p in plans) == CHUNK_FINGERPRINTS
    assert all(p.source_fingerprint == SOURCE_FINGERPRINT for p in plans)
    assert plans[0].previous_chunk_id == "" and plans[0].next_chunk_id == plans[1].chunk_id
    assert plans[1].previous_chunk_id == plans[0].chunk_id
    assert plans[1].next_chunk_id == plans[2].chunk_id
    assert plans[2].previous_chunk_id == plans[1].chunk_id and plans[2].next_chunk_id == ""


@pytest.mark.parametrize("field,value", [
    ("chunk_count", 2),
    ("provider_request_cap", 4),
    ("provider_attempt_cap", 4),
    ("read_timeout_seconds", 60),
])
def test_request_policy_mismatch_rejected(tmp_path, field, value):
    request = build_context(tmp_path)["request"]
    with pytest.raises(ValueError):
        replace(request, **{field: value})


def test_reordered_or_duplicated_request_rejected_at_authority_boundary(tmp_path):
    context = build_context(tmp_path)
    request = context["request"]
    context["request"] = replace(
        request,
        chunk_ids=tuple(reversed(request.chunk_ids)),
        chunk_fingerprints=tuple(reversed(request.chunk_fingerprints)),
    )
    with pytest.raises(ControlledMultiChunkAuthorityError):
        ControlledMultiChunkExecutor().execute(**context)
    with pytest.raises(ValueError):
        replace(
            request,
            chunk_ids=(request.chunk_ids[0],) * 3,
            chunk_fingerprints=(request.chunk_fingerprints[0],) * 3,
        )


def test_authentic_stage72_authority_required(tmp_path):
    context = build_context(tmp_path)
    context["stage72_verification"] = object()
    with pytest.raises(ControlledMultiChunkAuthorityError):
        ControlledMultiChunkExecutor().execute(**context)


def test_success_is_sequential_and_writes_exact_artifacts(tmp_path):
    context = build_context(tmp_path)
    starts = []
    context["transport_factory"] = lambda index: (
        starts.append(index)
        or FakeSingleInvocationTransport(outputs=(FAKE_OUTPUTS[index - 1],))
    )
    result = ControlledMultiChunkExecutor().execute(**context)
    root = context["artifact_root"]
    assert starts == [1, 2, 3]
    assert result.chunks_started == result.chunks_completed == 3
    assert result.provider_requests == result.provider_attempts == result.provider_successes == 3
    assert result.translation_executions == result.chunk_outputs_written == 3
    assert result.checkpoints_written == 3 and result.combined_output_written == 1
    assert len(list(root.glob("chunk-*.translated.txt"))) == 3
    assert len(list(root.glob("checkpoint-*.json"))) == 3
    assert (root / "combined.translated.txt").is_file()
    assert (root / "stage74-final-evidence.json").is_file()
    assert all((result.retries, result.fallbacks, result.parallel_requests)) is False


@pytest.mark.parametrize("failed_index,completed", [(1, 0), (2, 1), (3, 2)])
def test_failed_chunk_stops_later_chunks_and_retains_only_completed(
    tmp_path, failed_index, completed,
):
    context = build_context(tmp_path)
    starts = []
    def factory(index):
        starts.append(index)
        if index == failed_index:
            return FakeSingleInvocationTransport(outcomes=("failure",))
        return FakeSingleInvocationTransport(outputs=(FAKE_OUTPUTS[index - 1],))
    context["transport_factory"] = factory
    with pytest.raises(ControlledMultiChunkProviderError):
        ControlledMultiChunkExecutor().execute(**context)
    assert starts == list(range(1, failed_index + 1))
    assert len(list(context["artifact_root"].glob("chunk-*.translated.txt"))) == completed
    assert len(list(context["artifact_root"].glob("checkpoint-*.json"))) == completed
    assert not (context["artifact_root"] / "combined.translated.txt").exists()


def test_checkpoint_atomic_readback_and_tamper_rejection(tmp_path):
    context = build_context(tmp_path)
    ControlledMultiChunkExecutor().execute(**context)
    checkpoint_path = context["artifact_root"] / "checkpoint-002.json"
    checkpoint = read_checkpoint(checkpoint_path)
    assert checkpoint.completed_chunk_count == 2
    assert checkpoint.resume_execution_attempts == 0
    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    payload["completed_chunk_count"] = 3
    checkpoint_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ControlledMultiChunkCheckpointError):
        read_checkpoint(checkpoint_path)


def test_quality_and_fixed_name_failure_closes_before_output(tmp_path):
    context = build_context(tmp_path, outputs=("這是一段足夠長但沒有固定姓名的繁體中文內容。" * 8,) + FAKE_OUTPUTS[1:])
    with pytest.raises(ControlledMultiChunkQualityError):
        ControlledMultiChunkExecutor().execute(**context)
    assert not list(context["artifact_root"].glob("chunk-*.translated.txt"))


def test_combined_order_fingerprint_and_raise_on_error(tmp_path):
    context = build_context(tmp_path)
    result = ControlledMultiChunkExecutor().execute(**context)
    root = context["artifact_root"]
    chunks = [path.read_text(encoding="utf-8") for path in sorted(root.glob("chunk-*.translated.txt"))]
    assert (root / "combined.translated.txt").read_text(encoding="utf-8") == "\n\n".join(chunks)
    assert verify_multi_chunk_result(
        context["request"], result, artifact_root=root, raise_on_error=True
    ).valid
    (root / "combined.translated.txt").write_text("\n\n".join(reversed(chunks)), encoding="utf-8")
    with pytest.raises(ControlledMultiChunkVerificationError):
        verify_multi_chunk_result(
            context["request"], result, artifact_root=root, raise_on_error=True
        )


def test_formal_output_and_overwrite_are_protected(tmp_path):
    context = build_context(tmp_path)
    context["artifact_root"] = tmp_path / "output"
    with pytest.raises(ControlledMultiChunkOutputError):
        ControlledMultiChunkExecutor().execute(**context)
    context = build_context(tmp_path / "again")
    ControlledMultiChunkExecutor().execute(**context)
    second = build_context(tmp_path / "second")
    second["artifact_root"] = context["artifact_root"]
    with pytest.raises(ControlledMultiChunkOutputError):
        ControlledMultiChunkExecutor().execute(**second)

def test_observed_chunk2_dialogue_failure_stops_before_chunk3(tmp_path):
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
    assert (root / "chunk-002.quality-diagnostic.json").is_file()
    assert not (root / "chunk-002.translated.txt").exists()
    assert not (root / "combined.translated.txt").exists()


@pytest.mark.parametrize(
    "gate,candidate",
    [
        ("fixed_names_passed", "這是一段完整流暢的繁體中文小說譯文。" * 20),
        ("traditional_chinese_signal", "Complete English literary output. " * 30),
        ("hangul_residual_passed", "정태의는 한국어 문장으로 남아 있다. " * 20),

        ("no_source_echo", "__SOURCE_ECHO__"),
        (
            "no_duplicate_loop",
            "鄭泰義望向遠方的海面，心中仍有許多疑問。\n\n" * 8,
        ),
    ],
)
def test_each_mandatory_gate_failure_stops_without_success_artifacts(
    tmp_path, gate, candidate,
):
    context = build_context(tmp_path)
    resolved = resolve_multi_chunk_source(
        context["dispatch_package"], root=context["repository_root"]
    )
    if candidate == "__SOURCE_ECHO__":
        candidate = resolved.chunks[0]
    assessment, _ = ControlledMultiChunkExecutor._quality_assessment(
        resolved.chunks[0], candidate
    )
    assert getattr(assessment, gate) is False
    starts = []
    context["transport_factory"] = lambda index: (
        starts.append(index)
        or FakeSingleInvocationTransport(outputs=(candidate,))
    )
    with pytest.raises(ControlledMultiChunkQualityError):
        ControlledMultiChunkExecutor().execute(**context)
    root = context["artifact_root"]
    assert starts == [1]
    assert not list(root.glob("chunk-*.translated.txt"))
    assert not list(root.glob("checkpoint-*.json"))
    assert not (root / "combined.translated.txt").exists()


def test_truthy_verifier_object_and_missing_fields_are_rejected(tmp_path, monkeypatch):
    class Truthy:
        def __bool__(self):
            return True

    import core.controlled_multi_chunk_translation_canary.executor as executor_module

    monkeypatch.setattr(
        executor_module, "verify_chunk_quality_assessment", lambda _value: Truthy()
    )
    context = build_context(tmp_path)
    with pytest.raises(ControlledMultiChunkQualityError):
        ControlledMultiChunkExecutor().execute(**context)
    assert not list(context["artifact_root"].glob("chunk-*.translated.txt"))
    with pytest.raises(ControlledMultiChunkVerificationError):
        verify_chunk_quality_assessment({"quality_passed": True})


def test_checkpoint_readback_failure_blocks_next_chunk(tmp_path, monkeypatch):
    import core.controlled_multi_chunk_translation_canary.executor as executor_module

    starts = []
    context = build_context(tmp_path)
    context["transport_factory"] = lambda index: (
        starts.append(index)
        or FakeSingleInvocationTransport(outputs=(FAKE_OUTPUTS[index - 1],))
    )
    def fail_checkpoint(*_args, **_kwargs):
        raise ControlledMultiChunkCheckpointError("read-back failed")
    monkeypatch.setattr(executor_module, "write_checkpoint_atomic", fail_checkpoint)
    with pytest.raises(ControlledMultiChunkCheckpointError):
        ControlledMultiChunkExecutor().execute(**context)
    assert starts == [1]
    assert (context["artifact_root"] / "chunk-001.translated.txt").is_file()
    assert not list(context["artifact_root"].glob("checkpoint-*.json"))
    assert not (context["artifact_root"] / "combined.translated.txt").exists()

def test_corruption_failure_stops_without_output_or_checkpoint(tmp_path, monkeypatch):
    starts = []
    context = build_context(tmp_path)
    original = ControlledMultiChunkExecutor._quality_assessment
    def blocked_assessment(source, translated):
        assessment, metrics = original(source, translated)
        assessment = replace(
            assessment, no_corruption=False, quality_passed=False
        )
        metrics["corruption_detected"] = True
        return assessment, metrics
    monkeypatch.setattr(
        ControlledMultiChunkExecutor,
        "_quality_assessment",
        staticmethod(blocked_assessment),
    )
    context["transport_factory"] = lambda index: (
        starts.append(index)
        or FakeSingleInvocationTransport(outputs=(FAKE_OUTPUTS[index - 1],))
    )
    with pytest.raises(ControlledMultiChunkQualityError):
        ControlledMultiChunkExecutor().execute(**context)
    assert starts == [1]
    assert not list(context["artifact_root"].glob("chunk-*.translated.txt"))
    assert not list(context["artifact_root"].glob("checkpoint-*.json"))


def test_valid_corner_dialogue_and_multiple_spans_pass():
    source = "“첫째.” 그는 말했다. “둘째.”"
    single = assess_dialogue_punctuation(source, "「第一句。」他說。")
    multiple = assess_dialogue_punctuation(
        source, "「第一句。」他停了一下。「第二句！」"
    )
    assert single["passed"] is True
    assert multiple["passed"] is True
    assert multiple["completed_dialogue_spans"] == 2


def test_narration_only_does_not_false_fail():
    result = assess_dialogue_punctuation(
        "그는 조용히 바다를 바라보았다.",
        "他安靜地望著海面，心裡沒有任何疑問。",
    )
    assert result["source_has_dialogue"] is False
    assert result["passed"] is True


@pytest.mark.parametrize(
    "candidate,reason",
    [
        ('"人物正在說話。"', "ascii-spoken-quotes-forbidden"),
        ("“人物正在說話。”", "curly-spoken-quotes-forbidden"),
        ("‘人物正在說話。’", "korean-nested-quotes-forbidden"),
    ],
)
def test_incompatible_spoken_quote_styles_fail(candidate, reason):
    result = assess_dialogue_punctuation("“대화다.”", candidate)
    assert result["passed"] is False
    assert reason in result["reason_codes"]


@pytest.mark.parametrize(
    "candidate,reason",
    [
        ("「沒有結束。", "unmatched-opening-corner-quote"),
        ("沒有開始。」", "unmatched-closing-corner-quote"),
        ("「外層『內層。」』", "malformed-nested-dialogue"),
        ("「缺少句末標點」", "dialogue-closing-punctuation-missing"),
    ],
)
def test_unmatched_nested_and_missing_closing_punctuation_fail(candidate, reason):
    result = assess_dialogue_punctuation("“대화다.”", candidate)
    assert result["passed"] is False
    assert reason in result["reason_codes"]


def test_exact_stage742_chunk2_failure_pattern_is_reproduced(tmp_path):
    context = build_context(tmp_path)
    resolved = resolve_multi_chunk_source(
        context["dispatch_package"], root=context["repository_root"]
    )
    observed_pattern = FAKE_OUTPUTS[1].replace("「", "“").replace("」", "”")
    result = assess_dialogue_punctuation(resolved.chunks[1], observed_pattern)
    assert result["quote_type_counts"] == {
        "ascii_double_quote_count": 0,
        "curly_open_double_quote_count": 2,
        "curly_close_double_quote_count": 2,
        "curly_open_single_quote_count": 0,
        "curly_close_single_quote_count": 0,
        "corner_open_count": 0,
        "corner_close_count": 0,
        "nested_corner_open_count": 0,
        "nested_corner_close_count": 0,
        "korean_style_quote_count": 4,
    }
    assert result["passed"] is False


def test_authentic_formatter_precedes_assessment_and_persistence(tmp_path):
    raw_outputs = list(FAKE_OUTPUTS)
    raw_outputs[1] = raw_outputs[1].replace("「", '"').replace("」", '"')
    context = build_context(tmp_path, outputs=tuple(raw_outputs))
    result = ControlledMultiChunkExecutor().execute(**context)
    persisted = (
        context["artifact_root"] / "chunk-002.translated.txt"
    ).read_text(encoding="utf-8")
    assert '"' not in persisted
    assert persisted.count("「") == persisted.count("」") == 2
    assert result.chunk_evidence[1].dialogue_punctuation_passed is True


def test_assessed_bytes_persisted_bytes_and_fingerprints_are_identical(tmp_path):
    context = build_context(tmp_path)
    result = ControlledMultiChunkExecutor().execute(**context)
    for output, evidence in zip(FAKE_OUTPUTS, result.chunk_evidence):
        assessed = format_translation_output(output).encode("utf-8")
        persisted = (
            context["artifact_root"] / evidence.output_artifact_path
        ).read_bytes()
        assert persisted == assessed
        assert hashlib.sha256(assessed).hexdigest() == evidence.output_fingerprint


def test_stage743_prompt_constraint_reaches_authentic_payload(tmp_path):
    transports = []

    class RecordingTransport(FakeSingleInvocationTransport):
        def invoke(self, payload, plan, *, provider_url, api_key):
            self.payload = payload
            return super().invoke(
                payload, plan, provider_url=provider_url, api_key=api_key
            )

    def factory(index):
        transport = RecordingTransport(outputs=(FAKE_OUTPUTS[index - 1],))
        transports.append(transport)
        return transport

    context = build_context(tmp_path)
    context["transport_factory"] = factory
    ControlledMultiChunkExecutor().execute(**context)
    for transport in transports:
        user_prompt = transport.payload["prompt"]["user_prompt"]
        assert "人物說出口的對話一律使用成對的「」" in user_prompt
        assert "禁止用 ASCII 雙引號或彎雙引號" in user_prompt


def test_punctuation_failure_diagnostic_is_invalid_only_and_redacted(tmp_path):
    bad = FAKE_OUTPUTS[1].replace("「", "“").replace("」", "”")
    context = build_context(tmp_path, outputs=(FAKE_OUTPUTS[0], bad, FAKE_OUTPUTS[2]))
    with pytest.raises(ControlledMultiChunkQualityError):
        ControlledMultiChunkExecutor().execute(**context)
    root = context["artifact_root"]
    diagnostic = json.loads(
        (root / "chunk-002.quality-diagnostic.json").read_text(encoding="utf-8")
    )
    invalid_candidate = root / "chunk-002.invalid-candidate.txt"
    assert invalid_candidate.read_text(encoding="utf-8") == bad
    assert diagnostic["version"] == "1.1"
    assert diagnostic["quote_type_counts"]["curly_open_double_quote_count"] == 2
    assert diagnostic["candidate_persisted_as_success"] is False
    assert diagnostic["checkpoint_authority"] is False
    assert diagnostic["no_secret_confirmation"] is True
    assert diagnostic["formatter_after_fingerprint"] == hashlib.sha256(
        bad.encode("utf-8")
    ).hexdigest()
    assert not (root / "chunk-002.translated.txt").exists()
    assert not (root / "checkpoint-002.json").exists()


def test_no_new_blind_global_quote_replacement():
    curly = "敘述中的彎引號“不是可自動修復的對話”。"
    measurement = '身高標記為 6"，此處不是成對對話引號。'
    assert format_translation_output(curly) == curly
    assert '6"' in format_translation_output(measurement)
