from pathlib import Path
from tempfile import TemporaryDirectory

from core.controlled_translation_runtime_integration import ControlledTranslationExecutor
from tests.unit.controlled_translation_runtime_integration import build_context


def main():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        context = build_context(root)
        result, evidence = ControlledTranslationExecutor().execute(**context)
        checks = (
            ("authentic Stage 7.2 dispatch", result.request.dispatch_package_id == context["dispatch_package"].dispatch_package_id),
            ("one source and chunk", evidence.source_character_count == 455 and evidence.chunk_count == 1),
            ("one Provider request and attempt", result.provider_requests == result.provider_attempts == 1),
            ("one translation and output", result.translation_executions == result.controlled_outputs_written == 1),
            ("41-layer evidence chain", len(evidence.canonical_chain) == 41),
            ("quality passed", evidence.quality_passed),
            ("no retries or fallbacks", result.retries == result.fallbacks == 0),
            ("no rollout replacement resume cache", (
                result.automatic_rollouts, result.formal_output_replacements,
                result.resume_mutations, result.cache_mutations,
            ) == (0, 0, 0, 0)),
        )
        for label, passed in checks:
            print(f"{'PASS' if passed else 'FAIL'}: {label}")
        return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
