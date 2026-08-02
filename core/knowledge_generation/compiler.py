"""
Compiler Interface for Knowledge Extraction SDK (RM-5.7.2)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable

from .models import (
    KnowledgeEntity,
    CompilationResult,
    KnowledgeManifest,
)


@dataclass
class CompilerConfig:
    domain: str
    output_format: str = "dict"
    include_metadata: bool = True
    include_relationships: bool = True
    custom_transforms: Dict[str, Callable] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
class KnowledgeCompiler(ABC):
    def __init__(self, config: CompilerConfig):
        self.config = config
        self.domain = config.domain
    
    @abstractmethod
    def compile(self, entities: List[KnowledgeEntity]) -> CompilationResult:
        pass
    
    def _create_base_result(self, entities: List[KnowledgeEntity]) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "version": "1.0",
            "entity_count": len(entities),
            "entities": [e.to_dict() for e in entities] if self.config.include_metadata else [],
        }
    
    def _apply_custom_transforms(self, data: Dict[str, Any]) -> Dict[str, Any]:
        for key, transform in self.config.custom_transforms.items():
            if key in data:
                data[key] = transform(data[key])
        return data
def compile_character(entities: List[KnowledgeEntity]) -> CompilationResult:
    from .models import CompilationResult
    compiled = {"characters": {}, "alias_index": {}, "relationship_graph": {}, "locked_terms": []}
    for entity in entities:
        char_data = entity.to_dict()
        char_id = entity.entity_id
        compiled["characters"][char_id] = char_data
        name = entity.name
        if name:
            compiled["alias_index"][name] = char_id
        for ref_type, ref_ids in entity.references.items():
            if ref_type not in compiled["relationship_graph"]:
                compiled["relationship_graph"][ref_type] = {}
            compiled["relationship_graph"][ref_type][char_id] = ref_ids
        if entity.attributes.get("locked", False):
            compiled["locked_terms"].append({"entity_id": char_id, "name": name, "translation": entity.attributes.get("translation", "")})
    return CompilationResult.success_result(compiled, len(entities))


def compile_glossary(entities: List[KnowledgeEntity]) -> CompilationResult:
    from .models import CompilationResult
    compiled = {"terms": {}, "categories": {}, "locked_terms": {}, "frequency_index": {}}
    for entity in entities:
        term_data = entity.to_dict()
        term = entity.attributes.get("term", entity.name)
        translation = entity.attributes.get("translation", "")
        compiled["terms"][term] = {"translation": translation, "category": entity.attributes.get("category", ""), "locked": entity.attributes.get("locked", False), "frequency": entity.attributes.get("frequency", 0), "entity_id": entity.entity_id}
        cat = entity.attributes.get("category", "uncategorized")
        if cat not in compiled["categories"]:
            compiled["categories"][cat] = []
        compiled["categories"][cat].append(term)
        if entity.attributes.get("locked", False):
            compiled["locked_terms"][term] = translation
        freq = entity.attributes.get("frequency", 0)
        if freq not in compiled["frequency_index"]:
            compiled["frequency_index"][freq] = []
        compiled["frequency_index"][freq].append(term)
    return CompilationResult.success_result(compiled, len(entities))
def compile_scene(entities: List[KnowledgeEntity]) -> CompilationResult:
    from .models import CompilationResult
    compiled = {"scenes": {}, "chapter_index": {}, "character_presence": {}, "location_index": {}}
    for entity in entities:
        scene_data = entity.to_dict()
        scene_id = entity.entity_id
        compiled["scenes"][scene_id] = scene_data
        chapter = entity.attributes.get("chapter", 0)
        if chapter not in compiled["chapter_index"]:
            compiled["chapter_index"][chapter] = []
        compiled["chapter_index"][chapter].append(scene_id)
        for char_id in entity.attributes.get("characters_present", []):
            if char_id not in compiled["character_presence"]:
                compiled["character_presence"][char_id] = []
            compiled["character_presence"][char_id].append(scene_id)
        location = entity.attributes.get("location", "")
        if location:
            if location not in compiled["location_index"]:
                compiled["location_index"][location] = []
            compiled["location_index"][location].append(scene_id)
    return CompilationResult.success_result(compiled, len(entities))


def compile_narrative(entities: List[KnowledgeEntity]) -> CompilationResult:
    from .models import CompilationResult
    compiled = {"arcs": {}, "chapter_ranges": {}, "character_involvement": {}, "theme_index": {}, "status_index": {}}
    for entity in entities:
        arc_data = entity.to_dict()
        arc_id = entity.entity_id
        compiled["arcs"][arc_id] = arc_data
        start = entity.attributes.get("start_chapter", 0)
        end = entity.attributes.get("end_chapter", 0)
        compiled["chapter_ranges"][arc_id] = (start, end)
        for char_id in entity.attributes.get("involved_characters", []):
            if char_id not in compiled["character_involvement"]:
                compiled["character_involvement"][char_id] = []
            compiled["character_involvement"][char_id].append(arc_id)
        for theme in entity.attributes.get("themes", []):
            if theme not in compiled["theme_index"]:
                compiled["theme_index"][theme] = []
            compiled["theme_index"][theme].append(arc_id)
        status = entity.attributes.get("status", "development")
        if status not in compiled["status_index"]:
            compiled["status_index"][status] = []
        compiled["status_index"][status].append(arc_id)
    return CompilationResult.success_result(compiled, len(entities))
def compile_style(entities: List[KnowledgeEntity]) -> CompilationResult:
    from .models import CompilationResult
    compiled = {"styles": {}, "category_index": {}, "priority_rules": [], "scope_index": {}}
    for entity in entities:
        style_data = entity.to_dict()
        style_id = entity.entity_id
        compiled["styles"][style_id] = style_data
        cat = entity.attributes.get("category", "other")
        if cat not in compiled["category_index"]:
            compiled["category_index"][cat] = []
        compiled["category_index"][cat].append(style_id)
        priority = entity.attributes.get("priority", 50)
        compiled["priority_rules"].append({"style_id": style_id, "priority": priority, "rules": entity.attributes.get("rules", {}), "applies_to": entity.attributes.get("applies_to", "global")})
        scope = entity.attributes.get("applies_to", "global")
        if scope not in compiled["scope_index"]:
            compiled["scope_index"][scope] = []
        compiled["scope_index"][scope].append(style_id)
    compiled["priority_rules"].sort(key=lambda x: -x["priority"])
    return CompilationResult.success_result(compiled, len(entities))


COMPILERS = {
    "character": compile_character,
    "glossary": compile_glossary,
    "scene": compile_scene,
    "narrative": compile_narrative,
    "style": compile_style,
}


def get_compiler(domain: str) -> Optional[Callable]:
    return COMPILERS.get(domain.lower())


def register_compiler(domain: str, compiler: Callable) -> None:
    COMPILERS[domain.lower()] = compiler
