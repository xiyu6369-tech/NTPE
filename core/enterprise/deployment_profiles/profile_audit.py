from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass(frozen=True)
class DeploymentProfileAudit:
    stage: str
    profile: str
    target: str
    environment: str
    config_hash: str
    validated: bool
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "profile": self.profile,
            "target": self.target,
            "environment": self.environment,
            "config_hash": self.config_hash,
            "validated": self.validated,
            "created_at": self.created_at,
        }


def build_profile_audit(profile_name: str, resolved_config: Dict[str, Any], validated: bool = True) -> DeploymentProfileAudit:
    payload = json.dumps(resolved_config, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    enterprise = resolved_config.get("enterprise", {})
    return DeploymentProfileAudit(
        stage="Stage-18.3",
        profile=profile_name,
        target=str(enterprise.get("deployment_target", "unknown")),
        environment=str(enterprise.get("environment", "unknown")),
        config_hash=digest,
        validated=validated,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
