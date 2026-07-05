from __future__ import annotations
from pathlib import Path
from .resource_manager import TranslationResource

def build_glossary_resource(root: Path, name: str = "default") -> TranslationResource:
    return TranslationResource(name=name, kind="glossary", path=str(root / "glossary.txt"), metadata={"role": "term_lock"})
