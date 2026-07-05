from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional


SECRET_FIELDS = {"api_key", "token", "secret", "password", "authorization", "x-api-key"}


def mask_secret(value: Optional[str], visible: int = 4) -> Optional[str]:
    """Return a log-safe representation of a credential value."""
    if value is None:
        return None
    text = str(value)
    if not text:
        return ""
    if len(text) <= visible:
        return "*" * len(text)
    return f"{'*' * max(0, len(text) - visible)}{text[-visible:]}"


def mask_mapping(values: Mapping[str, Any]) -> Dict[str, Any]:
    masked: Dict[str, Any] = {}
    for key, value in values.items():
        lower = key.lower()
        if any(secret in lower for secret in SECRET_FIELDS):
            masked[key] = mask_secret(str(value) if value is not None else None)
        elif isinstance(value, Mapping):
            masked[key] = mask_mapping(value)
        else:
            masked[key] = value
    return masked


@dataclass(frozen=True)
class ProviderCredential:
    provider: str
    api_key: Optional[str] = None
    env_var: Optional[str] = None
    token: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def resolve_api_key(self, environ: Optional[Mapping[str, str]] = None) -> Optional[str]:
        source = environ if environ is not None else os.environ
        if self.api_key:
            return self.api_key
        if self.env_var:
            return source.get(self.env_var)
        return None

    def is_configured(self, environ: Optional[Mapping[str, str]] = None, *, local_provider: bool = False) -> bool:
        if local_provider:
            return True
        return bool(self.resolve_api_key(environ) or self.token)

    def validate(self, environ: Optional[Mapping[str, str]] = None, *, local_provider: bool = False) -> Dict[str, Any]:
        configured = self.is_configured(environ, local_provider=local_provider)
        missing = [] if configured else [self.env_var or "api_key"]
        return {
            "provider": self.provider,
            "configured": configured,
            "env_var": self.env_var,
            "missing": missing,
            "masked": self.masked(environ),
        }

    def masked(self, environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
        resolved = self.resolve_api_key(environ)
        return {
            "provider": self.provider,
            "api_key": mask_secret(resolved),
            "env_var": self.env_var,
            "token": mask_secret(self.token),
            "metadata": mask_mapping(self.metadata),
        }


class ProviderCredentialRegistry:
    """Small in-memory credential registry with environment variable support."""

    def __init__(self, credentials: Optional[Mapping[str, ProviderCredential]] = None):
        self._credentials: Dict[str, ProviderCredential] = dict(credentials or {})

    def register(self, credential: ProviderCredential) -> ProviderCredential:
        self._credentials[credential.provider] = credential
        return credential

    def get(self, provider: str) -> ProviderCredential:
        return self._credentials.get(provider, ProviderCredential(provider=provider))

    def resolve_api_key(self, provider: str, environ: Optional[Mapping[str, str]] = None) -> Optional[str]:
        return self.get(provider).resolve_api_key(environ)

    def validate(self, provider: str, environ: Optional[Mapping[str, str]] = None, *, local_provider: bool = False) -> Dict[str, Any]:
        return self.get(provider).validate(environ, local_provider=local_provider)

    def validate_all(self, local_providers: Optional[set[str]] = None, environ: Optional[Mapping[str, str]] = None) -> Dict[str, Dict[str, Any]]:
        local = local_providers or set()
        return {
            name: credential.validate(environ, local_provider=name in local)
            for name, credential in self._credentials.items()
        }

    def masked(self, environ: Optional[Mapping[str, str]] = None) -> Dict[str, Dict[str, Any]]:
        return {name: credential.masked(environ) for name, credential in self._credentials.items()}

    def list(self) -> list[str]:
        return list(self._credentials.keys())
