"""Offline Stage 7.4 controlled multi-chunk acceptance."""

from pathlib import Path
from tempfile import TemporaryDirectory

from core.controlled_multi_chunk_translation_canary import (
    ControlledMultiChunkExecutor, read_checkpoint, verify_multi_chunk_result,
)
from tests.unit.controlled_multi_chunk_translation_canary import build_context


def main() -> int:
    with TemporaryDirectory() as directory:
        context = build_context(Path(directory))
        result = ControlledMultiChunkExecutor().execute(**context)
        root = context["artifact_root"]
        checks = (
            ("authentic exact three-chunk resolution", len(result.chunk_evidence) == 3),
            ("sequential Provider attempts", result.provider_requests == result.provider_attempts == 3),
            ("three successful translations", result.provider_successes == result.translation_executions == 3),
            ("three isolated outputs", len(list(root.glob("chunk-*.translated.txt"))) == 3),
            ("three atomic checkpoints", [
                read_checkpoint(root / f"checkpoint-{index:03d}.json").completed_chunk_count
                for index in (1, 2, 3)
            ] == [1, 2, 3]),
            ("one ordered combined output", result.combined_output_written == 1),
            ("all quality gates", all(item.quality_passed for item in result.chunk_evidence)),
            ("zero network fake transport", result.provider_requests == 3),
            ("zero retries fallbacks rollout resume cache", not any((
                result.retries, result.fallbacks, result.parallel_requests,
                result.automatic_rollouts, result.formal_output_replacements,
                result.resume_execution_attempts, result.cache_mutations,
            ))),
            ("final verification", verify_multi_chunk_result(
                context["request"], result, artifact_root=root
            ).valid),
        )
        for label, passed in checks:
            print(f"{'PASS' if passed else 'FAIL'}: {label}")
        return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
