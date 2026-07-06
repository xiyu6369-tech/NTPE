from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass(frozen=True)
class EnterpriseRuntimeAudit:
    stage: str
    profile: str
    environment: str
    target: str
    runtime_hash: str
    ready: bool
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "profile": self.profile,
            "environment": self.environment,
            "target": self.target,
            "runtime_hash": self.runtime_hash,
            "ready": self.ready,
            "created_at": self.created_at,
        }


def build_runtime_audit(result: Dict[str, Any]) -> EnterpriseRuntimeAudit:
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    context = dict(result.get("context", {}))
    return EnterpriseRuntimeAudit(
        stage="Stage-18.4",
        profile=str(context.get("profile", "unknown")),
        environment=str(context.get("environment", "unknown")),
        target=str(context.get("target", "unknown")),
        runtime_hash=digest,
        ready=bool(result.get("success", False)),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
