"""
Knowledge Compilation Engine - Tests for Manifest
"""

from __future__ import annotations

import pytest

from core.knowledge_compilation import (
    ManifestGenerator,
    ManifestValidator,
    CompilationManifest,
    EntityRef,
)
from core.knowledge_compilation.errors import ManifestGenerationError


def make_entity(entity_type: str, entity_id: str, **kwargs) -> dict:
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "name": f"Test {entity_type} {entity_id}",
        "schema_version": "1.0",
        "version": 1,
        "confidence": 0.9,
        "metadata": {"review_status": "APPROVED"},
        **kwargs,
    }


class TestManifestGenerator:
    """ManifestGenerator 測試。"""
    
    def test_manifest_generation(self):
        """Manifest 應正確生成。"""
        entities = {
            "character": [
                make_entity("character", "char-001"),
                make_entity("character", "char-002"),
            ],
            "glossary": [
                make_entity("glossary", "gloss-001"),
            ],
        }
        
        generator = ManifestGenerator(
            package_id="test_package",
            package_version="1.0.0",
            compiler_version="1.0.0",
        )
        
        manifest = generator.generate(entities)
        
        assert manifest.package_id == "test_package"
        assert manifest.package_version == "1.0.0"
        assert manifest.entity_counts["character"] == 2
        assert manifest.entity_counts["glossary"] == 1
        assert manifest.schema_versions["character"] == "1.0"
        assert manifest.schema_versions["glossary"] == "1.0"
        assert len(manifest.entity_refs) == 3
        assert manifest.created_at
    
    def test_entity_refs_sorted(self):
        """entity_refs 應按 entity_type -> entity_id -> version 排序。"""
        entities = {
            "character": [
                make_entity("character", "char-003"),
                make_entity("character", "char-001"),
            ],
            "glossary": [
                make_entity("glossary", "gloss-001"),
            ],
        }
        
        generator = ManifestGenerator()
        manifest = generator.generate(entities)
        
        ref_ids = [(r.entity_type, r.entity_id) for r in manifest.entity_refs]
        assert ref_ids == [
            ("character", "char-001"),
            ("character", "char-003"),
            ("glossary", "gloss-001"),
        ]
    
    def test_schema_version_output(self):
        """schema_versions 應正確輸出。"""
        entities = {
            "character": [make_entity("character", "char-001")],
            "scene": [make_entity("scene", "scene-001")],
            "narrative": [make_entity("narrative", "narr-001")],
            "style": [make_entity("style", "style-001")],
        }
        
        generator = ManifestGenerator()
        manifest = generator.generate(entities)
        
        assert set(manifest.schema_versions.keys()) == {"character", "scene", "narrative", "style"}
        for v in manifest.schema_versions.values():
            assert v == "1.0"

    def test_entity_counting(self):
        """實體計數應正確。"""
        entities = {
            "character": [make_entity("character", f"char-{i:03d}") for i in range(5)],
            "glossary": [make_entity("glossary", f"gloss-{i:03d}") for i in range(10)],
            "scene": [make_entity("scene", f"scene-{i:03d}") for i in range(3)],
        }
        
        generator = ManifestGenerator()
        manifest = generator.generate(entities)
        
        assert manifest.entity_counts["character"] == 5
        assert manifest.entity_counts["glossary"] == 10
        assert manifest.entity_counts["scene"] == 3
        assert manifest.total_entity_count() == 18
    
    def test_empty_entities(self):
        """空實體集合應生成空 manifest。"""
        entities = {}
        
        generator = ManifestGenerator()
        manifest = generator.generate(entities)
        
        assert manifest.entity_counts == {}
        assert manifest.schema_versions == {}
        assert manifest.entity_refs == []
        assert manifest.total_entity_count() == 0
    
    def test_get_entity_types(self):
        """get_entity_types 應返回排序後的類型列表。"""
        entities = {
            "style": [make_entity("style", "style-001")],
            "character": [make_entity("character", "char-001")],
            "narrative": [make_entity("narrative", "narr-001")],
        }
        
        generator = ManifestGenerator()
        manifest = generator.generate(entities)
        
        assert manifest.get_entity_types() == ["character", "narrative", "style"]


class TestManifestValidator:
    """ManifestValidator 測試。"""
    
    def test_validate_valid_manifest(self):
        """有效 manifest 應通過驗證。"""
        entities = {
            "character": [make_entity("character", "char-001")],
        }
        
        generator = ManifestGenerator()
        manifest = generator.generate(entities)
        
        errors = ManifestValidator.validate(manifest)
        assert errors == []
    
    def test_validate_missing_package_id(self):
        """缺少 package_id 應報錯。"""
        manifest = CompilationManifest(
            package_id="",
            package_version="1.0.0",
            schema_versions={"character": "1.0"},
            entity_counts={"character": 1},
            entity_refs=[EntityRef("char-001", "character", "Test", 1, "1.0")],
            created_at="2024-01-01T00:00:00+00:00",
        )
        
        errors = ManifestValidator.validate(manifest)
        assert any("package_id" in e for e in errors)
    
    def test_validate_missing_entity_counts(self):
        """缺少 entity_counts 應報錯。"""
        manifest = CompilationManifest(
            package_id="test",
            package_version="1.0.0",
            schema_versions={"character": "1.0"},
            entity_counts={},
            entity_refs=[EntityRef("char-001", "character", "Test", 1, "1.0")],
            created_at="2024-01-01T00:00:00+00:00",
        )
        
        errors = ManifestValidator.validate(manifest)
        assert any("entity_counts" in e for e in errors)
    
    def test_validate_count_mismatch(self):
        """entity_counts 與 entity_refs 不一致應報錯。"""
        manifest = CompilationManifest(
            package_id="test",
            package_version="1.0.0",
            schema_versions={"character": "1.0"},
            entity_counts={"character": 5},
            entity_refs=[EntityRef("char-001", "character", "Test", 1, "1.0")],
            created_at="2024-01-01T00:00:00+00:00",
        )
        
        errors = ManifestValidator.validate(manifest)
        assert any("不一致" in e for e in errors)
    
    def test_validate_unsorted_refs(self):
        """未排序的 entity_refs 應報錯。"""
        manifest = CompilationManifest(
            package_id="test",
            package_version="1.0.0",
            schema_versions={"character": "1.0"},
            entity_counts={"character": 2},
            entity_refs=[
                EntityRef("char-003", "character", "Test", 1, "1.0"),
                EntityRef("char-001", "character", "Test", 1, "1.0"),
            ],
            created_at="2024-01-01T00:00:00+00:00",
        )
        
        errors = ManifestValidator.validate(manifest)
        assert any("排序" in e for e in errors)
    
    def test_assert_valid_raises(self):
        """assert_valid 應在無效時拋出異常。"""
        manifest = CompilationManifest(
            package_id="",
            package_version="1.0.0",
            schema_versions={},
            entity_counts={},
            entity_refs=[],
            created_at="",
        )
        
        with pytest.raises(ManifestGenerationError):
            ManifestValidator.assert_valid(manifest)
    
    def test_to_dict_roundtrip(self):
        """to_dict/from_dict 往返應保持一致。"""
        entities = {
            "character": [make_entity("character", "char-001")],
            "glossary": [make_entity("glossary", "gloss-001")],
        }
        
        generator = ManifestGenerator()
        manifest = generator.generate(entities)
        
        data = manifest.to_dict()
        restored = CompilationManifest.from_dict(data)
        
        assert restored.package_id == manifest.package_id
        assert restored.entity_counts == manifest.entity_counts
        assert restored.schema_versions == manifest.schema_versions
        assert len(restored.entity_refs) == len(manifest.entity_refs)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])