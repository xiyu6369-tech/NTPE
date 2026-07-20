from __future__ import annotations
import os
from pathlib import Path
from core.prompt_contract_verification_canary import AUTHORIZATION_TOKEN, CanaryConfig, execute_verification_canary

if __name__ == "__main__":
    # The token is deliberately opt-in and never written to artifacts or logs.
    config = CanaryConfig(authorization_id=os.environ.get("NTPE_STAGE1256_AUTHORIZATION_ID", ""), authorization_token=os.environ.get("NTPE_STAGE1256_AUTHORIZATION_TOKEN", ""))
    raise SystemExit(0 if execute_verification_canary(config, root=Path(__file__).resolve().parents[1])["request_count"] <= 2 else 1)
