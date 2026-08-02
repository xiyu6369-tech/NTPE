"""
Knowledge Generation Extractors (RM-5.7.2)

Factory functions for creating domain-specific knowledge extractors.
"""

from tools.knowledge_generation.character_extractor import create_character_extractor
from tools.knowledge_generation.glossary_extractor import create_glossary_extractor
from tools.knowledge_generation.scene_extractor import create_scene_extractor
from tools.knowledge_generation.narrative_extractor import create_narrative_extractor
from tools.knowledge_generation.style_extractor import create_style_extractor

__all__ = [
    "create_character_extractor",
    "create_glossary_extractor", 
    "create_scene_extractor",
    "create_narrative_extractor",
    "create_style_extractor",
]