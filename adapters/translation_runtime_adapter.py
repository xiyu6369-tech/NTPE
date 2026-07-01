"""NTPE Foundation-06.0 Translation Runtime Adapter."""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.translation.runtime_contract import (
    TranslationRuntimeContractAdapter,
    create_translation_manifest,
    validate_translation_manifest,
)


class TranslationRuntimeAdapter(TranslationRuntimeContractAdapter):
    """Stable public adapter for Translation Runtime Contract integration."""

    def __init__(self, manifest: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(manifest or create_translation_manifest(adapter="translation-runtime-adapter"))


def create_translation_runtime_adapter(**metadata: Any) -> TranslationRuntimeAdapter:
    return TranslationRuntimeAdapter(create_translation_manifest(**metadata))


def validate_translation_runtime_adapter(adapter: TranslationRuntimeAdapter) -> bool:
    return isinstance(adapter, TranslationRuntimeAdapter) and validate_translation_manifest(adapter.manifest())
