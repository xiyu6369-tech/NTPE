"""
Knowledge Compilation Engine - Tests for Package Builder
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from core.knowledge_compilation import (
    PackageBuilder,
    PackageReader,
    create_package_reader,
    KnowledgeCompiler,
    create_compiler,
    CompilationPackage,
    CompilationManifest,
)
from core.knowledge_compilation.models import EntityRef
from core.knowledge_compilation.errors import PackageBuildError


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


class TestPackageBuilder:
    """PackageBuilder 測試。"""
    
    def test_build_output_files(self):
        """建構應輸出正確的檔案。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {
                "character": [
                    make_approved_entity("character", "char-001"),
                    make_approved_entity("character", "char-002"),
                ],
                "glossary": [
                    make_approved_entity("glossary", "gloss-001"),
                ],
            }
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            package = compiler.compile_entities(entities)
            
            output_dir = Path(tmpdir) / "v1"
            assert output_dir.exists()
            
            char_file = output_dir / "characters.json"
            assert char_file.exists()
            char_data = json.loads(char_file.read_text(encoding="utf-8"))
            assert len(char_data) == 2
            
            gloss_file = output_dir / "glossaries.json"
            assert gloss_file.exists()
            gloss_data = json.loads(gloss_file.read_text(encoding="utf-8"))
            assert len(gloss_data) == 1
            
            manifest_file = output_dir / "manifest.json"
            assert manifest_file.exists()
            manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
            assert manifest_data["package_id"] == "ntpe_knowledge"
            assert manifest_data["entity_counts"]["character"] == 2
            
            package_file = output_dir / "package.json"
            assert package_file.exists()
            package_data = json.loads(package_file.read_text(encoding="utf-8"))
            assert package_data["package_id"] == "ntpe_knowledge"
    
    def test_deterministic_order_in_files(self):
        """輸出檔案中的實體順序應確定性。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {
                "character": [
                    make_approved_entity("character", "char-003"),
                    make_approved_entity("character", "char-001"),
                    make_approved_entity("character", "char-002"),
                ],
            }
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            compiler.compile_entities(entities)
            
            char_file = Path(tmpdir) / "v1" / "characters.json"
            char_data = json.loads(char_file.read_text(encoding="utf-8"))
            
            ids = [e["entity_id"] for e in char_data]
            assert ids == ["char-001", "char-002", "char-003"]
    
    def test_build_manifest_only(self):
        """僅建構 manifest。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from core.knowledge_compilation import ManifestGenerator
            
            entities = {
                "character": [make_approved_entity("character", "char-001")],
            }
            
            generator = ManifestGenerator()
            manifest = generator.generate(entities)
            
            builder = PackageBuilder(output_root=tmpdir)
            output_dir = builder.build_manifest_only(manifest)
            
            manifest_file = output_dir / "manifest.json"
            assert manifest_file.exists()
            
            char_file = output_dir / "characters.json"
            assert not char_file.exists()

    def test_load_package(self):
        """載入完整套件。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {
                "character": [
                    make_approved_entity("character", "char-001"),
                    make_approved_entity("character", "char-002"),
                ],
            }
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            package = compiler.compile_entities(entities)
            
            builder = PackageBuilder(output_root=tmpdir)
            loaded = builder.load_package(Path(tmpdir) / "v1")
            
            assert loaded.package_id == package.package_id
            assert loaded.checksum == package.checksum
            assert loaded.get_entity_count("character") == 2
    
    def test_load_manifest(self):
        """載入 manifest。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {
                "character": [make_approved_entity("character", "char-001")],
            }
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            compiler.compile_entities(entities)
            
            builder = PackageBuilder(output_root=tmpdir)
            manifest = builder.load_manifest(Path(tmpdir) / "v1")
            
            assert manifest.package_id == "ntpe_knowledge"
            assert manifest.entity_counts["character"] == 1

    def test_load_entities(self):
        """載入特定類型實體。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {
                "character": [
                    make_approved_entity("character", "char-001"),
                    make_approved_entity("character", "char-002"),
                ],
                "glossary": [make_approved_entity("glossary", "gloss-001")],
            }
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            compiler.compile_entities(entities)
            
            builder = PackageBuilder(output_root=tmpdir)
            chars = builder.load_entities(Path(tmpdir) / "v1", "character")
            gloss = builder.load_entities(Path(tmpdir) / "v1", "glossary")
            
            assert len(chars) == 2
            assert len(gloss) == 1
    
    def test_load_nonexistent_entities(self):
        """載入不存在的實體類型應返回空列表。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {"character": [make_approved_entity("character", "char-001")]}
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            compiler.compile_entities(entities)
            
            builder = PackageBuilder(output_root=tmpdir)
            scenes = builder.load_entities(Path(tmpdir) / "v1", "scene")
            
            assert scenes == []
    
    def test_verify_package(self):
        """驗證套件完整性。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {"character": [make_approved_entity("character", "char-001")]}
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            package = compiler.compile_entities(entities)
            
            builder = PackageBuilder(output_root=tmpdir)
            assert builder.verify_package(package)

class TestPackageReader:
    """PackageReader 測試（運行時唯讀介面）。"""
    
    def test_read_package(self):
        """讀取完整套件。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {
                "character": [
                    make_approved_entity("character", "char-001"),
                    make_approved_entity("character", "char-002"),
                ],
            }
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            compiler.compile_entities(entities)
            
            reader = create_package_reader(Path(tmpdir) / "v1")
            package = reader.package
            
            assert package.package_id == "ntpe_knowledge"
            assert package.get_entity_count("character") == 2
    
    def test_read_manifest(self):
        """讀取 manifest。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {"character": [make_approved_entity("character", "char-001")]}
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            compiler.compile_entities(entities)
            
            reader = create_package_reader(Path(tmpdir) / "v1")
            manifest = reader.manifest
            
            assert manifest.entity_counts["character"] == 1
    
    def test_get_entities(self):
        """獲取特定類型實體。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {
                "character": [
                    make_approved_entity("character", "char-001"),
                    make_approved_entity("character", "char-002"),
                ],
            }
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            compiler.compile_entities(entities)
            
            reader = create_package_reader(Path(tmpdir) / "v1")
            chars = reader.get_entities("character")
            
            assert len(chars) == 2
            assert chars[0]["entity_id"] == "char-001"
    
    def test_get_entity(self):
        """獲取單一實體。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {"character": [make_approved_entity("character", "char-001")]}
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            compiler.compile_entities(entities)
            
            reader = create_package_reader(Path(tmpdir) / "v1")
            entity = reader.get_entity("character", "char-001")
            
            assert entity is not None
            assert entity["entity_id"] == "char-001"
            
            entity = reader.get_entity("character", "nonexistent")
            assert entity is None
    
    def test_get_all_entities(self):
        """獲取所有實體。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {
                "character": [make_approved_entity("character", "char-001")],
                "glossary": [make_approved_entity("glossary", "gloss-001")],
            }
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            compiler.compile_entities(entities)
            
            reader = create_package_reader(Path(tmpdir) / "v1")
            all_entities = reader.get_all_entities()
            
            assert len(all_entities) == 2
    
    def test_get_entity_types(self):
        """獲取實體類型列表。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {
                "character": [make_approved_entity("character", "char-001")],
                "glossary": [make_approved_entity("glossary", "gloss-001")],
            }
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            compiler.compile_entities(entities)
            
            reader = create_package_reader(Path(tmpdir) / "v1")
            types = reader.get_entity_types()
            
            assert set(types) == {"character", "glossary"}
    
    def test_verify_integrity(self):
        """驗證套件完整性。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = {"character": [make_approved_entity("character", "char-001")]}
            
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            compiler.compile_entities(entities)
            
            reader = create_package_reader(Path(tmpdir) / "v1")
            assert reader.verify_integrity()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])