from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.translation_quality_provider_canary import (
    AUTHORIZATION_TOKEN,
    CanaryExecutionConfig,
    execute_canary,
)
from core.translation_quality_provider_canary.framework import build_evidence_and_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute the bounded TE v7.2 Stage 12.5.2 Provider canary.")
    parser.add_argument("--authorization-id", required=True)
    parser.add_argument("--authorization-token", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = CanaryExecutionConfig(
        authorization_id=args.authorization_id,
        authorization_token=args.authorization_token,
    )
    result = execute_canary(config, root=root)
    if result.blockers:
        print("BLOCKED: " + ",".join(result.blockers))
        return 2
    build_evidence_and_manifest(root=root)
    print(f"{result.status}: requests={result.request_count}")
    return 0 if result.status == "execution_complete_awaiting_human_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
