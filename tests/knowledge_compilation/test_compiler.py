"""
Knowledge Compilation Engine - Tests for Compiler
"""

from __future__ import annotations

import pytest

from core.knowledge_compilation import (
    KnowledgeCompiler,
    CompilationConfig,
    create_compiler,
    EmptyPackageError,
    InvalidEntityStateError,
    CompilationError,
)
from core.knowledge_compilation.models import APPROVED_STATES


def make_entity(entity_type: str, entity_id: str, review_state: str, **kwargs) -> dict:
    """建立測試用實體。"""
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "name": f"Test {entity_type} {entity_id}",
        "schema_version": "1.0",
        "version": 1,
        "confidence": 0.9,
        "metadata": {
            "review_status": review_state,
        },
        **kwargs,
    }


def make_approved_entity(entity_type: str, entity_id: str, **kwargs) -> dict:
    return make_entity(entity_type, entity_id, "APPROVED", **kwargs)


def make_auto_approved_entity(entity_type: str, entity_id: str, **kwargs) -> dict:
    return make_entity(entity_type, entity_id, "AUTO_APPROVED", **kwargs)


def make_pending_entity(entity_type: str, entity_id: str, **kwargs) -> dict:
    return make_entity(entity_type, entity_id, "PENDING", **kwargs)


def make_rejected_entity(entity_type: str, entity_id: str, **kwargs) -> dict:
    return make_entity(entity_type, entity_id, "REJECTED", **kwargs)


class TestKnowledgeCompiler:
    """KnowledgeCompiler 測試。"""
    
    def test_compile_empty_package_raises(self):
        """編譯空包應拋出 EmptyPackageError。"""
        compiler = create_compiler()
        compiler.set_entity_loader(lambda: {})
        
        with pytest.raises(EmptyPackageError):
            compiler.compile()
    
    def test_compile_approved_entities(self):
        """編譯已核准實體應成功。"""
        entities = {
            "character": [
                make_approved_entity("character", "char-001"),
                make_auto_approved_entity("character", "char-002"),
            ],
            "glossary": [
                make_approved_entity("glossary", "gloss-001"),
            ],
        }
        
        compiler = create_compiler()
        package = compiler.compile_entities(entities)
        
        assert package.package_id == "ntpe_knowledge"
        assert package.package_version == "1.0.0"
        assert package.get_entity_count("character") == 2
        assert package.get_entity_count("glossary") == 1
        assert package.total_entity_count() == 3
        assert package.checksum
        assert package.created_at
        assert package.manifest.total_entity_count() == 3
    
    def test_reject_pending_entity_strict_mode(self):
        """嚴格模式下 PENDING 實體應拋出異常。"""
        entities = {
            "character": [
                make_pending_entity("character", "char-001"),
            ],
        }
        
        compiler = create_compiler()
        compiler.disable_runtime_guard()
        
        with pytest.raises(InvalidEntityStateError) as exc_info:
            compiler.compile_entities(entities)
        
        assert exc_info.value.details["current_state"] == "PENDING"
        assert "APPROVED" in exc_info.value.details["allowed_states"]
        assert "AUTO_APPROVED" in exc_info.value.details["allowed_states"]

    def test_reject_human_review_required_strict_mode(self):
        """嚴格模式下 HUMAN_REVIEW_REQUIRED 實體應拋出異常。"""
        entities = {
            "character": [
                make_entity("character", "char-001", "HUMAN_REVIEW_REQUIRED"),
            ],
        }
        
        compiler = create_compiler()
        compiler.disable_runtime_guard()
        
        with pytest.raises(InvalidEntityStateError) as exc_info:
            compiler.compile_entities(entities)
        
        assert exc_info.value.details["current_state"] == "HUMAN_REVIEW_REQUIRED"
    
    def test_non_strict_mode_skips_invalid(self):
        """非嚴格模式下跳過無效狀態實體。"""
        config = CompilationConfig(strict_mode=False)
        compiler = KnowledgeCompiler(config=config)
        compiler.disable_runtime_guard()
        
        entities = {
            "character": [
                make_approved_entity("character", "char-001"),
                make_pending_entity("character", "char-002"),
                make_entity("character", "char-003", "HUMAN_REVIEW_REQUIRED"),
            ],
        }
        
        package = compiler.compile_entities(entities)
        
        # 只有 APPROVED 的被包含
        assert package.get_entity_count("character") == 1
        stats = package.metadata.get("compilation_stats", {})
        assert stats.get("approved_entities") == 1
        assert stats.get("skipped_entities") == 2

    def test_deterministic_ordering(self):
        """相同輸入應產生相同順序的實體。"""
        entities = {
            "character": [
                make_approved_entity("character", "char-003"),
                make_approved_entity("character", "char-001"),
                make_approved_entity("character", "char-002"),
            ],
        }
        
        compiler = create_compiler()
        compiler.disable_runtime_guard()
        
        package1 = compiler.compile_entities(entities)
        package2 = compiler.compile_entities(entities)
        
        # 實體順序應相同（按 entity_id 排序）
        chars1 = package1.entities["character"]
        chars2 = package2.entities["character"]
        
        assert [c["entity_id"] for c in chars1] == [c["entity_id"] for c in chars2]
        assert [c["entity_id"] for c in chars1] == ["char-001", "char-002", "char-003"]
    
    def test_same_input_same_checksum(self):
        """相同輸入應產生相同 checksum。"""
        entities = {
            "character": [
                make_approved_entity("character", "char-001"),
                make_approved_entity("character", "char-002"),
            ],
            "glossary": [
                make_approved_entity("glossary", "gloss-001"),
            ],
        }
        
        compiler = create_compiler()
        compiler.disable_runtime_guard()
        
        package1 = compiler.compile_entities(entities)
        package2 = compiler.compile_entities(entities)
        
        assert package1.checksum == package2.checksum
    
    def test_different_entity_different_checksum(self):
        """不同實體應產生不同 checksum。"""
        entities1 = {
            "character": [make_approved_entity("character", "char-001")],
        }
        entities2 = {
            "character": [make_approved_entity("character", "char-002")],
        }
        
        compiler = create_compiler()
        compiler.disable_runtime_guard()
        
        package1 = compiler.compile_entities(entities1)
        package2 = compiler.compile_entities(entities2)
        
        assert package1.checksum != package2.checksum
    
    def test_manifest_generation(self):
        """Manifest 應正確生成。"""
        entities = {
            "character": [
                make_approved_entity("character", "char-001"),
                make_approved_entity("character", "char-002"),
            ],
            "glossary": [
                make_approved_entity("glossary", "gloss-001"),
            ],
        }
        
        compiler = create_compiler()
        compiler.disable_runtime_guard()
        
        package = compiler.compile_entities(entities)
        
        manifest = package.manifest
        assert manifest.package_id == "ntpe_knowledge"
        assert manifest.package_version == "1.0.0"
        assert manifest.entity_counts["character"] == 2
        assert manifest.entity_counts["glossary"] == 1
        assert "character" in manifest.schema_versions
        assert "glossary" in manifest.schema_versions
        assert len(manifest.entity_refs) == 3
        
        # entity_refs 應按 entity_type -> entity_id -> version 排序
        ref_types = [r.entity_type for r in manifest.entity_refs]
        assert ref_types == ["character", "character", "glossary"]
    
    def test_schema_versions_in_package(self):
        """套件應包含 schema_versions。"""
        entities = {
            "character": [make_approved_entity("character", "char-001")],
            "scene": [make_approved_entity("scene", "scene-001")],
            "narrative": [make_approved_entity("narrative", "narr-001")],
            "style": [make_approved_entity("style", "style-001")],
        }
        
        compiler = create_compiler()
        compiler.disable_runtime_guard()
        
        package = compiler.compile_entities(entities)
        
        assert "character" in package.schema_versions
        assert "scene" in package.schema_versions
        assert "narrative" in package.schema_versions
        assert "style" in package.schema_versions
        assert package.schema_versions["character"] == "1.0"
    
    def test_no_entity_loader_raises(self):
        """未設定 entity_loader 應拋出錯誤。"""
        compiler = create_compiler()
        # 不設定 entity_loader
        
        with pytest.raises(CompilationError, match="未設定實體載入器"):
            compiler.compile()
    
    def test_approved_states_constant(self):
        """APPROVED_STATES 應包含正確的狀態。"""
        assert "APPROVED" in APPROVED_STATES
        assert "AUTO_APPROVED" in APPROVED_STATES
        assert "PENDING" not in APPROVED_STATES
        assert "HUMAN_REVIEW_REQUIRED" not in APPROVED_STATES
        assert "REJECTED" not in APPROVED_STATES
        assert "SUPERSEDED" not in APPROVED_STATES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])