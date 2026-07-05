from __future__ import annotations
from pathlib import Path
from .resource_manager import TranslationResource

def build_formatter_resource(root: Path, name: str = "default") -> TranslationResource:
    return TranslationResource(name=name, kind="formatter", metadata={"role": "taiwan_formatter"})
