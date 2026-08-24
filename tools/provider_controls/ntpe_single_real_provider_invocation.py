from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path

from core.adaptive_context_real_provider_preflight import PreflightAttemptPlan
from core.adaptive_context_single_real_invocation import (
    SingleRealInvocationConfig,
    SingleRealInvocationRunner,
)
from core.production_runtime.manifest import (
    get_te_v7_artifact_path,
    get_te_v7_stage_path,
    TE_V7_STAGE1010_SINGLE_REAL_INVOCATION,
    TE_V7_STAGE1010_TRANSLATION_REVIEW,
)

ROOT = Path(__file__).resolve().parents[3]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one controlled Stage 10.10 invocation.")
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--enable-boundary", action="store_true")
    parser.add_argument("--enable-real-provider", action="store_true")
    parser.add_argument("--authorization-id", default="")
    parser.add_argument("--execution-mode", choices=("fake", "real"), default="fake")
    parser.add_argument("--session-id", default="stage1010-single-session")
    parser.add_argument(
        "--artifact-path",
        default=str(get_te_v7_artifact_path(ROOT, "te_v7_stage1010", TE_V7_STAGE1010_SINGLE_REAL_INVOCATION)),
    )
    parser.add_argument(
        "--review-path",
        default=str(get_te_v7_artifact_path(ROOT, "te_v7_stage1010", TE_V7_STAGE1010_TRANSLATION_REVIEW)),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    token = getpass.getpass("Execution authorization: ") if args.enable else ""
    config = SingleRealInvocationConfig(
        enabled=args.enable,
        boundary_enabled=args.enable_boundary,
        real_provider_enabled=args.enable_real_provider,
        authorization_id=args.authorization_id,
        execution_authorization_token=token,
        execution_mode=args.execution_mode,
        session_id=args.session_id,
        attempt_plan=(PreflightAttemptPlan(1, "meta/llama-3.3-70b-instruct", 30, False),),
        artifact_path=args.artifact_path,
        review_path=args.review_path,
    )
    result = SingleRealInvocationRunner().run(
        config, root=ROOT, environ=os.environ,
    )
    print(json.dumps(result.artifact.to_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if not result.blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())