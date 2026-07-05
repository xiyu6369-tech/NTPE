from __future__ import annotations
from pathlib import Path
from .resource_manager import TranslationResource

def build_provider_resource(root: Path, name: str = "default") -> TranslationResource:
    return TranslationResource(name=name, kind="provider", metadata={"role": "ai_provider", "adapter": "runtime_provider"})
