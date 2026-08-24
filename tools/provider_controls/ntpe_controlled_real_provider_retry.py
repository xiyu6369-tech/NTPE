from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path

from core.adaptive_context_controlled_provider_retry import (
    ControlledProviderRetryConfig,
    ControlledProviderRetryRunner,
)
from core.production_runtime.manifest import (
    get_te_v7_artifact_path,
    get_te_v7_stage_path,
    TE_V7_STAGE10101_CONTROLLED_RETRY,
    TE_V7_STAGE10101_TRANSLATION_REVIEW,
)

ROOT = Path(__file__).resolve().parents[3]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare or run one controlled Stage 10.10.1 retry.")
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--enable-boundary", action="store_true")
    parser.add_argument("--enable-real-provider", action="store_true")
    parser.add_argument("--authorization-id", default="")
    parser.add_argument("--execution-mode", choices=("fake", "real"), default="fake")
    parser.add_argument("--invocation-id", default="stage10101-controlled-retry-001")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument(
        "--artifact-path",
        default=str(get_te_v7_artifact_path(ROOT, "te_v7_stage10101", TE_V7_STAGE10101_CONTROLLED_RETRY)),
    )
    parser.add_argument(
        "--review-path",
        default=str(get_te_v7_artifact_path(ROOT, "te_v7_stage10101", TE_V7_STAGE10101_TRANSLATION_REVIEW)),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    token = getpass.getpass("Execution authorization: ") if args.enable else ""
    config = ControlledProviderRetryConfig(
        enabled=args.enable,
        boundary_enabled=args.enable_boundary,
        real_provider_enabled=args.enable_real_provider,
        authorization_id=args.authorization_id,
        execution_authorization_token=token,
        execution_mode=args.execution_mode,
        invocation_id=args.invocation_id,
        artifact_path=args.artifact_path,
        review_path=args.review_path,
    )
    runner = ControlledProviderRetryRunner()
    result = (
        runner.prepare(config, root=ROOT, environ=os.environ)
        if args.prepare_only
        else runner.run(config, root=ROOT, environ=os.environ)
    )
    print(json.dumps(result.artifact.to_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if not result.blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())