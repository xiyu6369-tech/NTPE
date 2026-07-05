from __future__ import annotations
from pathlib import Path
from .resource_manager import TranslationResource

def build_character_memory_resource(root: Path, name: str = "default") -> TranslationResource:
    return TranslationResource(name=name, kind="character_memory", path=str(root / "character_memory.json"), metadata={"role": "name_consistency"})
