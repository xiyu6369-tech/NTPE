from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.prompt_contract_verification_canary.candidate_structural_canary import (
    Stage1258Config,
    execute_stage1258,
)


def main() -> int:
    config = Stage1258Config(
        authorization_id=os.environ.get("NTPE_STAGE1258_AUTHORIZATION_ID", ""),
        authorization_token=os.environ.get("NTPE_STAGE1258_AUTHORIZATION_TOKEN", ""),
        preparation_commit=os.environ.get("NTPE_STAGE1258_PREPARATION_COMMIT", ""),
    )
    summary = execute_stage1258(config, root=ROOT)
    return 0 if summary.get("provider_requests", 0) <= 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
