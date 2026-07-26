"""Explicitly authorized Stage 7.4 three-request real Provider canary."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from dataclasses import replace
from tempfile import TemporaryDirectory

from core.controlled_multi_chunk_translation_canary import (
    ControlledMultiChunkExecutor, resolve_multi_chunk_source,
)
from core.controlled_multi_chunk_translation_canary.policy import (
    ATTEMPT_CAP, ArtifactRootValidationError, CONNECT_TIMEOUT_SECONDS,
    OUTPUT_ROOT, PROFILE, PROVIDER, PROVIDER_MODEL, READ_TIMEOUT_SECONDS,
    REAL_CANARY_GATE_ENV, REQUEST_CAP, SOURCE_FINGERPRINT, SOURCE_FIXTURE_ID,
    TARGET_LANGUAGE, select_artifact_root,
)
from core.controlled_translation_runtime_integration.diagnostics import (
    Stage73NvidiaDiagnosticTransport,
)
from tests.unit.controlled_multi_chunk_translation_canary import build_context


def main(
    argv=None,
    *,
    repository_root=None,
    transport_factory_override=None,
    environ=None,
    execution_mode="real",
) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorize-real-provider", action="store_true")
    parser.add_argument("--artifact-root")
    args = parser.parse_args(argv)
    environment = os.environ if environ is None else environ
    repository = (
        Path(__file__).resolve().parents[2]
        if repository_root is None else Path(repository_root)
    ).resolve()
    clean_root_required = args.artifact_root is not None
    try:
        selection = select_artifact_root(
            repository,
            args.artifact_root,
            clean_root_required=clean_root_required,
        )
    except ArtifactRootValidationError as error:
        print(f"FAIL: ArtifactRootValidationError: {error}")
        print("network_calls: 0")
        print("provider_attempts_started: 0")
        return 1

    with TemporaryDirectory() as directory:
        context = build_context(Path(directory))
        context["request"] = replace(
            context["request"], artifact_root=selection.repository_relative,
        )
        resolved = resolve_multi_chunk_source(
            context["dispatch_package"], root=repository
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
            f"{environment.get('NTPE_API_CONNECT_TIMEOUT', 'unset')}/"
            f"{environment.get('NTPE_CURRENT_API_TIMEOUT', 'unset')}"
        )
        print(f"default_artifact_root: {OUTPUT_ROOT}")
        print(f"artifact_root: {selection.repository_relative}")
        print(f"artifact_root_canonical: {selection.absolute_path}")
        print("artifact_root_validation: PASS")
        print(f"clean_root_required: {str(clean_root_required).lower()}")
        print(f"clean_root_empty: {str(selection.root_empty).lower()}")
        print(
            "credential_present: "
            + str(bool(environment.get("NVIDIA_API_KEY"))).lower()
        )
        print("no_secret_confirmation: true")
        if (
            not args.authorize_real_provider
            or environment.get(REAL_CANARY_GATE_ENV) != "1"
        ):
            print("SKIPPED: Stage 7.4 real Provider canary not explicitly authorized")
            return 0
        transports = []
        def transport_factory(index):
            transport = (
                Stage73NvidiaDiagnosticTransport()
                if transport_factory_override is None
                else transport_factory_override(index)
            )
            transports.append(transport)
            return transport
        context.update(
            repository_root=repository,
            artifact_root=selection.absolute_path,
            execution_mode=execution_mode,
            transport_factory=transport_factory,
            environ=environment,
            strict_artifact_root=True,
            clean_artifact_root=clean_root_required,
        )
        try:
            result = ControlledMultiChunkExecutor().execute(**context)
        except Exception as error:
            print(f"FAIL: {type(error).__name__}: {error}")
            print(f"network_calls: {sum(item.network_requests for item in transports)}")
            print(f"provider_attempts_started: {len(transports)}")
            return 1
    evidence_path = selection.absolute_path / "stage74-final-evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    print(f"network_calls: {sum(item.network_requests for item in transports)}")
    print(f"provider_requests: {result.provider_requests}")
    print(f"provider_attempts: {result.provider_attempts}")
    print(f"provider_successes: {result.provider_successes}")
    print(f"translation_executions: {result.translation_executions}")
    print(f"chunks_started/completed: {result.chunks_started}/{result.chunks_completed}")
    print(f"chunk_outputs: {result.chunk_outputs_written}")
    print(f"checkpoints: {result.checkpoints_written}")
    print(
        "combined_output: "
        f"{Path(selection.repository_relative) / result.combined_output_path}"
    )
    print(f"combined_fingerprint: {result.combined_output_fingerprint}")
    print(
        f"evidence: {Path(selection.repository_relative) / evidence_path.name}"
    )
    print(f"evidence_fingerprint: {evidence['verification_fingerprint']}")
    print("retries/fallbacks: 0/0")
    print("PASS: Stage 7.4 controlled real multi-chunk Provider canary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
