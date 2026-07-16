from __future__ import annotations

from typing import Any, Mapping

from .models import ProductionShadowInput
from .serialization import validate_safe_metadata


def create_shadow_input(**values: Any) -> ProductionShadowInput:
    validate_safe_metadata(values)
    item = ProductionShadowInput(**values)
    if item.chunk_index < 0 or not item.source_hash or len(item.source_hash) < 16:
        raise ValueError("invalid shadow identity")
    return item
