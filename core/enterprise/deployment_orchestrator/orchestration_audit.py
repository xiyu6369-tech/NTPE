from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass(frozen=True)
class EnterpriseOrchestrationAudit:
    stage: str
    profile: str
    environment: str
    target: str
    orchestration_hash: str
    ready: bool
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "profile": self.profile,
            "environment": self.environment,
            "target": self.target,
            "orchestration_hash": self.orchestration_hash,
            "ready": self.ready,
            "created_at": self.created_at,
        }


def build_orchestration_audit(result: Dict[str, Any]) -> EnterpriseOrchestrationAudit:
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    orchestration = dict(result.get("orchestration", {}))
    return EnterpriseOrchestrationAudit(
        stage="Stage-18.5",
        profile=str(orchestration.get("profile", "unknown")),
        environment=str(orchestration.get("environment", "unknown")),
        target=str(orchestration.get("target", "unknown")),
        orchestration_hash=digest,
        ready=bool(result.get("success", False)),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
