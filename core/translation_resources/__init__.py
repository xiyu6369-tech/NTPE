from __future__ import annotations

from .resource_manager import TranslationResource, TranslationResourceManager
from .prompt_resource import build_prompt_resource
from .glossary_resource import build_glossary_resource
from .character_memory_resource import build_character_memory_resource
from .context_resource import build_context_resource
from .provider_resource import build_provider_resource
from .formatter_resource import build_formatter_resource
from .qa_resource import build_qa_resource

__all__ = [
    "TranslationResource",
    "TranslationResourceManager",
    "build_prompt_resource",
    "build_glossary_resource",
    "build_character_memory_resource",
    "build_context_resource",
    "build_provider_resource",
    "build_formatter_resource",
    "build_qa_resource",
]
