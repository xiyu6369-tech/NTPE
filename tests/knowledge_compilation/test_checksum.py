"""
Knowledge Compilation Engine - Tests for Checksum
"""

from __future__ import annotations

import pytest

from core.knowledge_compilation import (
    ChecksumCalculator,
    DEFAULT_CALCULATOR,
    KnowledgeCompiler,
    create_compiler,
    CompilationPackage,
)


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


def make_approved_entity(entity_type: str, entity_id: str, **kwargs) -> dict:
    return make_entity(entity_type, entity_id, **kwargs)


class TestChecksumCalculator:
    """ChecksumCalculator 測試。"""
    
    def test_same_input_same_hash(self):
        """相同輸入應產生相同雜湊。"""
        entities = {
            "character": [
                make_approved_entity("character", "char-001"),
                make_approved_entity("character", "char-002"),
            ],
            "glossary": [
                make_approved_entity("glossary", "gloss-001"),
            ],
        }
        
        calculator = ChecksumCalculator()
        hash1 = calculator.calculate_from_entities(entities)
        hash2 = calculator.calculate_from_entities(entities)
        
        assert hash1 == hash2
        assert len(hash1) == 64
    
    def test_different_entity_different_hash(self):
        """不同實體應產生不同雜湊。"""
        entities1 = {
            "character": [make_approved_entity("character", "char-001")],
        }
        entities2 = {
            "character": [make_approved_entity("character", "char-002")],
        }
        
        calculator = ChecksumCalculator()
        hash1 = calculator.calculate_from_entities(entities1)
        hash2 = calculator.calculate_from_entities(entities2)
        
        assert hash1 != hash2
    
    def test_different_order_same_hash(self):
        """不同順序的相同實體應產生相同雜湊（決定性）。"""
        entities1 = {
            "character": [
                make_approved_entity("character", "char-003"),
                make_approved_entity("character", "char-001"),
                make_approved_entity("character", "char-002"),
            ],
        }
        entities2 = {
            "character": [
                make_approved_entity("character", "char-001"),
                make_approved_entity("character", "char-002"),
                make_approved_entity("character", "char-003"),
            ],
        }
        
        calculator = ChecksumCalculator()
        hash1 = calculator.calculate_from_entities(entities1)
        hash2 = calculator.calculate_from_entities(entities2)
        
        assert hash1 == hash2

    def test_add_entity_changes_hash(self):
        """新增實體應改變雜湊。"""
        entities1 = {
            "character": [make_approved_entity("character", "char-001")],
        }
        entities2 = {
            "character": [
                make_approved_entity("character", "char-001"),
                make_approved_entity("character", "char-002"),
            ],
        }
        
        calculator = ChecksumCalculator()
        hash1 = calculator.calculate_from_entities(entities1)
        hash2 = calculator.calculate_from_entities(entities2)
        
        assert hash1 != hash2
    
    def test_different_entity_type_changes_hash(self):
        """不同實體類型應產生不同雜湊。"""
        entities1 = {
            "character": [make_approved_entity("character", "char-001")],
        }
        entities2 = {
            "glossary": [make_approved_entity("glossary", "char-001")],
        }
        
        calculator = ChecksumCalculator()
        hash1 = calculator.calculate_from_entities(entities1)
        hash2 = calculator.calculate_from_entities(entities2)
        
        assert hash1 != hash2
    
    def test_version_change_changes_hash(self):
        """版本變更應改變雜湊。"""
        entities1 = {
            "character": [make_approved_entity("character", "char-001", version=1)],
        }
        entities2 = {
            "character": [make_approved_entity("character", "char-001", version=2)],
        }
        
        calculator = ChecksumCalculator()
        hash1 = calculator.calculate_from_entities(entities1)
        hash2 = calculator.calculate_from_entities(entities2)
        
        assert hash1 != hash2
    
    def test_calculate_package_checksum(self):
        """計算套件 checksum。"""
        entities = {
            "character": [
                make_approved_entity("character", "char-001"),
                make_approved_entity("character", "char-002"),
            ],
        }
        
        compiler = create_compiler()
        compiler.disable_runtime_guard()
        package = compiler.compile_entities(entities)
        
        calculator = ChecksumCalculator()
        calculated = calculator.calculate(package)
        
        assert calculated == package.checksum
        assert package.verify_checksum(calculator)
    
    def test_package_verify_checksum(self):
        """套件驗證 checksum。"""
        entities = {
            "character": [make_approved_entity("character", "char-001")],
        }
        
        compiler = create_compiler()
        compiler.disable_runtime_guard()
        package = compiler.compile_entities(entities)
        
        # 正確的 checksum
        assert package.verify_checksum(DEFAULT_CALCULATOR)
        
        # 錯誤的 checksum
        tampered = CompilationPackage(
            package_id=package.package_id,
            package_version=package.package_version,
            schema_versions=package.schema_versions,
            entities=package.entities,
            manifest=package.manifest,
            checksum="0" * 64,
            created_at=package.created_at,
            compiler_version=package.compiler_version,
            metadata=package.metadata,
        )
        assert not tampered.verify_checksum(DEFAULT_CALCULATOR)
    
    def test_hash_string(self):
        """字串雜湊測試。"""
        hash1 = ChecksumCalculator.hash_string("test")
        hash2 = ChecksumCalculator.hash_string("test")
        hash3 = ChecksumCalculator.hash_string("different")
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64
    
    def test_hash_bytes(self):
        """位元組雜湊測試。"""
        hash1 = ChecksumCalculator.hash_bytes(b"test")
        hash2 = ChecksumCalculator.hash_bytes(b"test")
        
        assert hash1 == hash2
        assert len(hash1) == 64
    
    def test_invalid_algorithm(self):
        """無效演算法應拋出錯誤。"""
        with pytest.raises(ValueError, match="不支援的演算法"):
            ChecksumCalculator("md5")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])