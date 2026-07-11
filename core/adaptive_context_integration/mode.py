from __future__ import annotations

import os
from typing import Mapping

VALID_MODES = ('disabled', 'shadow', 'active')
ENV_NAME = 'NTPE_TE_V7_ACE_MODE'

def resolve_mode(value: str | None = None, *, environ: Mapping[str, str] | None = None) -> tuple[str, tuple[str, ...]]:
    raw = value if value is not None else (environ or os.environ).get(ENV_NAME, 'disabled')
    normalized = str(raw or '').strip().lower()
    if normalized in VALID_MODES:
        return normalized, ()
    return 'disabled', (f'invalid-mode:{normalized or "blank"}',)
