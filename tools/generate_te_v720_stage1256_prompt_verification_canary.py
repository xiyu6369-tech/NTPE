from __future__ import annotations

from pathlib import Path
from core.prompt_contract_verification_canary import CanaryConfig, execute_verification_canary

ROOT = Path(__file__).resolve().parents[1]

def build_offline_preflight_artifacts() -> dict[str, object]:
    return execute_verification_canary(CanaryConfig("offline-only", ""), root=ROOT)

if __name__ == "__main__":
    print(build_offline_preflight_artifacts())
