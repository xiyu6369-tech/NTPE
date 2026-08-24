from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from core.adaptive_context_provider_benchmark_session import (
    ControlledProviderBenchmarkSession, ControlledSessionConfig, ProviderAttemptPlan,
    write_session_report,
)
from core.adaptive_context_provider_evidence import ProviderRequestIdentity
from core.production_runtime.manifest import get_te_v7_stage_path

from .config import ControlledCliConfig
from .mock_provider import DeterministicMockProvider
from .parser import build_parser


def _controlled_report_path(value: str) -> Path:
    target = Path(value).resolve()
    root = Path.cwd().resolve()
    allowed = (root / ".ntpe_test_sandbox", get_te_v7_stage_path(root, "te_v7_stage103"))
    if target.suffix.lower() != ".json" or not any(target == base or base in target.parents for base in allowed):
        raise ValueError("controlled-cli-report-path-outside-stage-boundary")
    return target


def _attempts(args: argparse.Namespace, config: ControlledCliConfig) -> tuple[ProviderAttemptPlan, ...]:
    rows: list[ProviderAttemptPlan] = []
    raw_attempts = tuple(args.attempt or ())
    if not raw_attempts:
        return (ProviderAttemptPlan(
            1, config.model, config.timeout_seconds, False,
            config.estimated_input_tokens, config.estimated_output_tokens,
        ),)
    for index, value in enumerate(raw_attempts, 1):
        parts = str(value).split("|")
        if len(parts) != 3 or parts[2].lower() not in {"0", "1", "false", "true"}:
            raise ValueError("controlled-cli-attempt-format-invalid")
        try: timeout = int(parts[1])
        except ValueError as exc: raise ValueError("controlled-cli-attempt-timeout-invalid") from exc
        rows.append(ProviderAttemptPlan(
            index, parts[0], timeout, parts[2].lower() in {"1", "true"},
            config.estimated_input_tokens, config.estimated_output_tokens,
        ))
    return tuple(rows)


def run_harness(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    config = ControlledCliConfig(
        enabled=bool(args.enable_controlled_session), pair_id=args.pair_id, run_kind=args.run_kind,
        set_name=args.set_name, chunk_index=args.chunk_index, source_hash=args.source_hash,
        chunk_hash=args.chunk_hash, model=args.model, timeout_seconds=args.timeout_seconds,
        estimated_input_tokens=args.estimated_input_tokens, estimated_output_tokens=args.estimated_output_tokens,
        minimum_output_tokens=args.minimum_output_tokens, report=args.report, resumed=bool(args.resume),
    )
    blockers = config.validate()
    if blockers:
        print(f"controlled_provider_session_error: {','.join(blockers)}")
        return 2
    try:
        plans = _attempts(args, config)
    except ValueError as exc:
        print(f"controlled_provider_session_error: {exc}")
        return 2
    outcomes = tuple(args.mock_outcome or ("success",))
    if len(outcomes) not in {1, len(plans)}:
        print("controlled_provider_session_error: mock-outcome-count-mismatch")
        return 2
    if len(outcomes) == 1 and len(plans) > 1:
        outcomes = outcomes * len(plans)
    output_tokens = tuple(args.mock_output_tokens or (config.estimated_output_tokens,))
    if len(output_tokens) not in {1, len(plans)} or any(value < 0 for value in output_tokens):
        print("controlled_provider_session_error: mock-output-token-count-invalid")
        return 2
    if len(output_tokens) == 1 and len(plans) > 1:
        output_tokens = output_tokens * len(plans)
    try:
        report_path = _controlled_report_path(config.report)
    except ValueError as exc:
        print(f"controlled_provider_session_error: {exc}")
        return 2
    provider = DeterministicMockProvider(outcomes, output_tokens)
    session = ControlledProviderBenchmarkSession(ControlledSessionConfig(
        enabled=True, pair_id=config.pair_id, run_kind=config.run_kind,
        execution_mode="mock", real_provider_execution=False, single_chunk_only=True,
    ))
    identity = ProviderRequestIdentity(
        pair_id=config.pair_id, run_kind=config.run_kind, set_name=config.set_name,
        chunk_index=config.chunk_index, source_hash=config.source_hash, chunk_hash=config.chunk_hash,
        model=plans[0].model, attempt=1, resumed=config.resumed,
        minimum_output_tokens=config.minimum_output_tokens,
    )
    result = session.run(
        identity=identity,
        payload={"session_metadata": {"set_name": config.set_name, "chunk_index": config.chunk_index}},
        plans=plans, provider=provider,
    )
    path = write_session_report(result, report_path)
    print(f"controlled_provider_session_report: {path}")
    print(f"controlled_provider_session_state: {result.summary.state}")
    print(f"controlled_provider_session_evidence: {result.evidence.status}")
    print("controlled_provider_session_readiness_evaluated: false")
    return 0 if result.summary.state in {"completed", "excluded"} else 1
