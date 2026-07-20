from __future__ import annotations
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from core.prompt_verification_canary_stage1257 import AUTHORIZATION_TOKEN, Stage1257Config, execute_stage1257
if __name__ == "__main__":
    config = Stage1257Config(os.environ.get("NTPE_STAGE1257_AUTHORIZATION_ID", ""), os.environ.get("NTPE_STAGE1257_AUTHORIZATION_TOKEN", ""))
    raise SystemExit(0 if execute_stage1257(config, root=ROOT)["request_count"] <= 2 else 1)
