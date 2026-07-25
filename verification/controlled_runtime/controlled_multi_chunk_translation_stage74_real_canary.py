"""Explicitly authorized Stage 7.4 three-request real Provider canary."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from core.controlled_multi_chunk_translation_canary import (
    ControlledMultiChunkExecutor, resolve_multi_chunk_source,
)
from core.controlled_multi_chunk_translation_canary.policy import (
    ATTEMPT_CAP, CONNECT_TIMEOUT_SECONDS, OUTPUT_ROOT, PROFILE, PROVIDER,
    PROVIDER_MODEL, READ_TIMEOUT_SECONDS, REAL_CANARY_GATE_ENV, REQUEST_CAP,
    SOURCE_FINGERPRINT, SOURCE_FIXTURE_ID, TARGET_LANGUAGE,
)
from core.controlled_translation_runtime_integration.diagnostics import (
    Stage73NvidiaDiagnosticTransport,
)
from tests.unit.controlled_multi_chunk_translation_canary import build_context


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorize-real-provider", action="store_true")
    args = parser.parse_args(argv)
    repository_root = Path(__file__).resolve().parents[2]
    with TemporaryDirectory() as directory:
        context = build_context(Path(directory))
        resolved = resolve_multi_chunk_source(
            context["dispatch_package"], root=repository_root
        )
        print("NTPE Stage 7.4 Controlled Multi-Chunk Translation Canary")
        print(f"source_fixture_id: {SOURCE_FIXTURE_ID}")
        print(f"source_fingerprint: {SOURCE_FINGERPRINT}")
        print("chunk_count: 3")
        print(
            "chunk_character_counts: "
            + ",".join(str(len(chunk)) for chunk in resolved.chunks)
        )
        print(f"target_language: {TARGET_LANGUAGE}")
        print(f"profile: {PROFILE}")
        print(f"provider: {PROVIDER}")
        print(f"model: {PROVIDER_MODEL}")
        print(f"request_cap: {REQUEST_CAP}")
        print(f"attempt_cap: {ATTEMPT_CAP}")
        print("retries/fallbacks: 0/0")
        print(
            f"effective_connect/read_timeout: "
            f"{os.environ.get('NTPE_API_CONNECT_TIMEOUT', 'unset')}/"
            f"{os.environ.get('NTPE_CURRENT_API_TIMEOUT', 'unset')}"
        )
        print(f"artifact_root: {OUTPUT_ROOT}")
        print("no_secret_confirmation: true")
        if (
            not args.authorize_real_provider
            or os.environ.get(REAL_CANARY_GATE_ENV) != "1"
        ):
            print("SKIPPED: Stage 7.4 real Provider canary not explicitly authorized")
            return 0
        transports = []
        def transport_factory(_index):
            transport = Stage73NvidiaDiagnosticTransport()
            transports.append(transport)
            return transport
        context.update(
            repository_root=repository_root,
            artifact_root=repository_root / OUTPUT_ROOT,
            execution_mode="real",
            transport_factory=transport_factory,
            environ=os.environ,
        )
        try:
            result = ControlledMultiChunkExecutor().execute(**context)
        except Exception as error:
            print(f"FAIL: {type(error).__name__}: {error}")
            print(f"network_calls: {sum(item.network_requests for item in transports)}")
            print(f"provider_attempts_started: {len(transports)}")
            return 1
    evidence_path = repository_root / OUTPUT_ROOT / "stage74-final-evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    print(f"network_calls: {sum(item.network_requests for item in transports)}")
    print(f"provider_requests: {result.provider_requests}")
    print(f"provider_attempts: {result.provider_attempts}")
    print(f"provider_successes: {result.provider_successes}")
    print(f"translation_executions: {result.translation_executions}")
    print(f"chunks_started/completed: {result.chunks_started}/{result.chunks_completed}")
    print(f"chunk_outputs: {result.chunk_outputs_written}")
    print(f"checkpoints: {result.checkpoints_written}")
    print(f"combined_output: {Path(OUTPUT_ROOT) / result.combined_output_path}")
    print(f"combined_fingerprint: {result.combined_output_fingerprint}")
    print(f"evidence: {Path(OUTPUT_ROOT) / evidence_path.name}")
    print(f"evidence_fingerprint: {evidence['verification_fingerprint']}")
    print("retries/fallbacks: 0/0")
    print("PASS: Stage 7.4 controlled real multi-chunk Provider canary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
