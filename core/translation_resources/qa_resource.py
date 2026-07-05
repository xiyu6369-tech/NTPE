from __future__ import annotations
from pathlib import Path
from .resource_manager import TranslationResource

def build_qa_resource(root: Path, name: str = "default") -> TranslationResource:
    return TranslationResource(name=name, kind="qa", metadata={"role": "runtime_qa"})
