from __future__ import annotations
from pathlib import Path
from .resource_manager import TranslationResource

def build_context_resource(root: Path, name: str = "default") -> TranslationResource:
    return TranslationResource(name=name, kind="context", metadata={"role": "context_window"})
