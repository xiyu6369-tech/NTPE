from dataclasses import FrozenInstanceError, replace
import json

import pytest

from core.adaptive_context_single_real_invocation import FakeSingleInvocationTransport
from core.controlled_multi_chunk_translation_canary import (
    ControlledMultiChunkAuthorityError, ControlledMultiChunkCheckpointError,
    ControlledMultiChunkExecutor, ControlledMultiChunkOutputError,
    ControlledMultiChunkProviderError, ControlledMultiChunkQualityError,
    ControlledMultiChunkVerificationError, read_checkpoint,
    resolve_multi_chunk_source, verify_multi_chunk_result,
)
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
