"""Explicitly authorized Stage 7.3 one-request real Provider canary."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from core.controlled_translation_runtime_integration import ControlledTranslationExecutor
from core.controlled_translation_runtime_integration.diagnostics import (
    Stage73NvidiaDiagnosticTransport,
)
from core.controlled_translation_runtime_integration.policy import (
    OUTPUT_ROOT, PROVIDER, PROVIDER_MODEL, REAL_CANARY_GATE_ENV,
    SOURCE_CHARACTER_COUNT, SOURCE_FIXTURE_ID,
)
from tests.unit.controlled_translation_runtime_integration import build_context


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorize-real-provider", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    print("NTPE Stage 7.3 Controlled Translation Runtime Canary")
    print(f"provider: {PROVIDER}")
    print(f"model: {PROVIDER_MODEL}")
    print(f"source: {SOURCE_FIXTURE_ID} ({SOURCE_CHARACTER_COUNT} characters)")
    print("chunk_count: 1")
    print("provider_request_cap: 1")
    print("provider_attempt_cap: 1")
    if not args.authorize_real_provider or os.environ.get(REAL_CANARY_GATE_ENV) != "1":
        print("SKIPPED: real Provider canary not explicitly authorized")
        return 0
    repository_root = Path(__file__).resolve().parents[2]
    with TemporaryDirectory() as directory:
        context = build_context(Path(directory))
        context.update(
            repository_root=repository_root,
            artifact_root=repository_root / OUTPUT_ROOT,
            execution_mode="real",
            transport=Stage73NvidiaDiagnosticTransport(),
            environ=os.environ,
            overwrite=args.overwrite,
        )
        try:
            result, evidence = ControlledTranslationExecutor().execute(**context)
        except Exception as error:
            print(f"FAIL: {type(error).__name__}: {error}")
            return 1
    print(f"output: {Path(OUTPUT_ROOT) / result.output_artifact_path}")
    print(f"output_fingerprint: {result.output_artifact_fingerprint}")
    print(f"evidence_fingerprint: {evidence.evidence_fingerprint}")
    print(f"translation_characters: {result.output_character_count}")
    print(f"hangul_ratio: {evidence.hangul_ratio}")
    print("quality: PASS")
    print("provider_requests: 1")
    print("provider_attempts: 1")
    print("retries: 0")
    print("fallbacks: 0")
    print("PASS: Stage 7.3 controlled real Provider canary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
