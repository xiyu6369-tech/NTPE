from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass

from core.adaptive_context_runtime_shadow import clear_shadow_records

ACE_MODE_ENV = "NTPE_TE_V7_ACE_MODE"
ACE_AUDIT_ENV = "NTPE_TE_V7_ACE_SHADOW_AUDIT"


@dataclass(frozen=True)
class ShadowValidationEnvironment:
    previous_mode: str | None
    previous_audit: str | None


@contextmanager
def production_shadow_session(*, audit_path: str | None = None):
    previous = ShadowValidationEnvironment(
        previous_mode=os.environ.get(ACE_MODE_ENV),
        previous_audit=os.environ.get(ACE_AUDIT_ENV),
    )
    clear_shadow_records()
    os.environ[ACE_MODE_ENV] = "shadow"
    if audit_path:
        os.environ[ACE_AUDIT_ENV] = audit_path
    else:
        os.environ.pop(ACE_AUDIT_ENV, None)
    try:
        yield previous
    finally:
        if previous.previous_mode is None:
            os.environ.pop(ACE_MODE_ENV, None)
        else:
            os.environ[ACE_MODE_ENV] = previous.previous_mode
        if previous.previous_audit is None:
            os.environ.pop(ACE_AUDIT_ENV, None)
        else:
            os.environ[ACE_AUDIT_ENV] = previous.previous_audit
