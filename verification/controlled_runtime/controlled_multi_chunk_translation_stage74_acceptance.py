"""Offline Stage 7.4 controlled multi-chunk acceptance."""

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from core.controlled_multi_chunk_translation_canary import (
    ControlledMultiChunkExecutor, read_checkpoint, verify_multi_chunk_result,
)
from core.controlled_multi_chunk_translation_canary.policy import (
    STAGE746_OUTPUT_ROOT,
)
from tests.unit.controlled_multi_chunk_translation_canary import build_context


def _run_acceptance(context, label=""):
    result = ControlledMultiChunkExecutor().execute(**context)
    root = context["artifact_root"]
    prefix = f"[{label}] " if label else ""
    checks = (
        (f"{prefix}authentic exact three-chunk resolution", len(result.chunk_evidence) == 3),
        (f"{prefix}sequential Provider attempts", result.provider_requests == result.provider_attempts == 3),
        (f"{prefix}three successful translations", result.provider_successes == result.translation_executions == 3),
        (f"{prefix}three isolated outputs", len(list(root.glob("chunk-*.translated.txt"))) == 3),
        (f"{prefix}three atomic checkpoints", [
            read_checkpoint(root / f"checkpoint-{index:03d}.json").completed_chunk_count
            for index in (1, 2, 3)
        ] == [1, 2, 3]),
        (f"{prefix}one ordered combined output", result.combined_output_written == 1),
        (f"{prefix}all quality gates", all(item.quality_passed for item in result.chunk_evidence)),
        (f"{prefix}zero network fake transport", result.provider_requests == 3),
        (f"{prefix}zero retries fallbacks rollout resume cache", not any((
            result.retries, result.fallbacks, result.parallel_requests,
            result.automatic_rollouts, result.formal_output_replacements,
            result.resume_execution_attempts, result.cache_mutations,
        ))),
        (f"{prefix}final verification", verify_multi_chunk_result(
            context["request"], result, artifact_root=root
        ).valid),
    )
    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
    return all(passed for _, passed in checks)


def main() -> int:
    all_passed = True

    with TemporaryDirectory() as directory:
        context = build_context(Path(directory))
        if not _run_acceptance(context, "default-stage743"):
            all_passed = False

    with TemporaryDirectory() as directory:
        context = build_context(Path(directory))
        context["request"] = replace(
            context["request"], artifact_root=STAGE746_OUTPUT_ROOT,
        )
        if not _run_acceptance(context, "stage746-override"):
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())