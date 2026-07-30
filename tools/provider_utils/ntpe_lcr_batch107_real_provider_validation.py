from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from core.lcr_production_shadow_hook.batch107_real_provider_validation import (
    PACKAGE_RELATIVE_PATH,
    execute_batch107,
    load_authorization,
    load_execution_package,
)


ROOT = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare-check or explicitly execute the bounded LCR Batch 10.7 real-provider validation."
    )
    parser.add_argument("--package", default=PACKAGE_RELATIVE_PATH.as_posix())
    parser.add_argument("--authorization", default="")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-execution-id", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    package = load_execution_package(args.package, root=ROOT)
    if not args.execute:
        print(json.dumps({
            "status": "awaiting_user_authorization",
            "execution_id": package["execution_id"],
            "real_provider_execution_authorized": False,
            "provider_requests": 0,
            "network_requests": 0,
        }, ensure_ascii=False, sort_keys=True))
        return 0
    if not args.authorization:
        print(json.dumps({"status": "blocked", "reason": "authorization_path_required"}, sort_keys=True))
        return 2
    authorization = load_authorization(args.authorization)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = execute_batch107(
        package, authorization=authorization, root=ROOT, now=now,
        confirm_execution_id=args.confirm_execution_id, environ=os.environ,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if result.status == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
