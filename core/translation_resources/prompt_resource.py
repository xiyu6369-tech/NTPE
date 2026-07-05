from __future__ import annotations
from pathlib import Path
from .resource_manager import TranslationResource

def build_prompt_resource(root: Path, name: str = "default") -> TranslationResource:
    return TranslationResource(name=name, kind="prompt", path=str(root / "prompt_packages"), metadata={"role": "prompt_builder"})
