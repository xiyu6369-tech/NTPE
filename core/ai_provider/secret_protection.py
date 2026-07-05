from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from .credentials import mask_mapping, mask_secret

SECRET_VALUE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"nvapi-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"or-[A-Za-z0-9_\-]{12,}"),
]

SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|x-api-key)\s*[:=]\s*([\"\']?)([^\s,}\"\']{8,})([\"\']?)"
)


def fingerprint_secret(value: Optional[str]) -> Optional[str]:
    """Return a stable non-reversible secret fingerprint for audits."""
    if value is None:
        return None
    text = str(value)
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def redact_text(text: str, replacement: str = "[NTPE_SECRET]") -> str:
    """Redact provider secrets from arbitrary log text."""
    redacted = str(text)
    for pattern in SECRET_VALUE_PATTERNS:
        redacted = pattern.sub(replacement, redacted)

    def _replace_assignment(match: re.Match[str]) -> str:
        key = match.group(1)
        return f"{key}={replacement}"

    return SECRET_ASSIGNMENT_PATTERN.sub(_replace_assignment, redacted)


def redact_mapping(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Mask secret-like fields and redact secret-looking strings recursively."""
    masked = mask_mapping(payload)
    return _redact_any(masked)


def _redact_any(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _redact_any(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_any(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_any(item) for item in value)
    if isinstance(value, str):
        return redact_text(value)
    return value


@dataclass(frozen=True)
class SecretAuditFinding:
    path: str
    line: int
    kind: str
    preview: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "line": self.line,
            "kind": self.kind,
            "preview": self.preview,
        }


@dataclass
class SecretProtectionPolicy:
    allow_plaintext_in_memory: bool = True
    allow_plaintext_in_logs: bool = False
    fail_on_plaintext_secret: bool = True
    allowed_env_prefixes: tuple[str, ...] = ("NTPE_", "NVIDIA_", "OPENAI_", "GEMINI_", "ANTHROPIC_", "OPENROUTER_", "OLLAMA_")
    protected_field_names: tuple[str, ...] = ("api_key", "token", "secret", "password", "authorization", "x-api-key")

    def redact_text(self, text: str) -> str:
        return redact_text(text)

    def redact_mapping(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        return redact_mapping(payload)

    def validate_env_name(self, env_var: Optional[str]) -> bool:
        if not env_var:
            return False
        return any(env_var.startswith(prefix) for prefix in self.allowed_env_prefixes)

    def manifest(self) -> Dict[str, Any]:
        return {
            "component": "provider_secret_protection_policy",
            "allow_plaintext_in_memory": self.allow_plaintext_in_memory,
            "allow_plaintext_in_logs": self.allow_plaintext_in_logs,
            "fail_on_plaintext_secret": self.fail_on_plaintext_secret,
            "allowed_env_prefixes": list(self.allowed_env_prefixes),
            "protected_field_names": list(self.protected_field_names),
        }


@dataclass
class SecretProtectionRuntime:
    policy: SecretProtectionPolicy = field(default_factory=SecretProtectionPolicy)

    def safe_log(self, message: str) -> str:
        return self.policy.redact_text(message)

    def safe_payload(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        return self.policy.redact_mapping(payload)

    def credential_report(self, provider: str, api_key: Optional[str] = None, env_var: Optional[str] = None) -> Dict[str, Any]:
        resolved = api_key or (os.environ.get(env_var) if env_var else None)
        return {
            "provider": provider,
            "configured": bool(resolved),
            "env_var": env_var,
            "env_var_allowed": self.policy.validate_env_name(env_var),
            "masked": mask_secret(resolved),
            "fingerprint": fingerprint_secret(resolved),
        }

    def scan_text(self, text: str, path: str = "<memory>") -> list[SecretAuditFinding]:
        findings: list[SecretAuditFinding] = []
        for idx, line in enumerate(str(text).splitlines() or [str(text)], start=1):
            for pattern in SECRET_VALUE_PATTERNS:
                if pattern.search(line):
                    findings.append(SecretAuditFinding(path=path, line=idx, kind="secret_value", preview=redact_text(line)))
                    break
            if SECRET_ASSIGNMENT_PATTERN.search(line):
                findings.append(SecretAuditFinding(path=path, line=idx, kind="secret_assignment", preview=redact_text(line)))
        return findings

    def scan_files(self, root: str | Path, suffixes: Iterable[str] = (".py", ".json", ".yaml", ".yml", ".env", ".txt", ".md")) -> list[SecretAuditFinding]:
        base = Path(root)
        if not base.exists():
            return []
        suffix_set = set(suffixes)
        files = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in suffix_set]
        findings: list[SecretAuditFinding] = []
        for file_path in files:
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            findings.extend(self.scan_text(text, path=str(file_path)))
        return findings

    def manifest(self) -> Dict[str, Any]:
        return {
            "stage": "NTPE 1.2 Professional Stage-14.6",
            "component": "provider_secret_protection_runtime",
            "policy": self.policy.manifest(),
        }
