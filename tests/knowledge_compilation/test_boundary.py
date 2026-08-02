"""
Knowledge Compilation Engine - Tests for Runtime Boundary

驗證：
- 編譯器屬於建構時，禁止在翻譯運行時調用
- 運行時只能使用 PackageReader 讀取凍結套件
"""

from __future__ import annotations

import os
import pytest

from core.knowledge_compilation import (
    KnowledgeCompiler,
    CompilationConfig,
    create_compiler,
    RuntimeInvocationError,
    PackageReader,
    create_package_reader,
)


def make_approved_entity(entity_type: str, entity_id: str) -> dict:
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "name": f"Test {entity_type} {entity_id}",
        "schema_version": "1.0",
        "version": 1,
        "confidence": 0.9,
        "metadata": {"review_status": "APPROVED"},
    }


class TestRuntimeBoundary:
    """運行時邊界測試。"""
    
    def test_compiler_raises_in_runtime_mode(self):
        """在 NTPE_RUNTIME_MODE=translation 時，編譯器應拋出 RuntimeInvocationError。"""
        # 設置運行時環境變量
        os.environ["NTPE_RUNTIME_MODE"] = "translation"
        
        try:
            compiler = create_compiler()
            compiler.disable_runtime_guard()  # 禁用 guard 以測試環境變量檢查
            # 重新啟用 guard 來測試環境變量檢查
            compiler._runtime_guard_enabled = True
            
            entities = {"character": [make_approved_entity("character", "char-001")]}
            
            with pytest.raises(RuntimeInvocationError) as exc_info:
                compiler.compile_entities(entities)
            
            assert "翻譯運行時環境" in str(exc_info.value)
            assert "PackageReader" in str(exc_info.value)
        finally:
            # 清理環境變量
            del os.environ["NTPE_RUNTIME_MODE"]
    
    def test_compiler_works_without_runtime_mode(self):
        """未設置運行時模式時，編譯器應正常工作。"""
        compiler = create_compiler()
        compiler.disable_runtime_guard()
        
        entities = {"character": [make_approved_entity("character", "char-001")]}
        
        package = compiler.compile_entities(entities)
        
        assert package.package_id == "ntpe_knowledge"
        assert package.get_entity_count("character") == 1
    
    def test_package_reader_works_in_runtime_mode(self):
        """PackageReader 在運行時模式下應正常工作。"""
        import tempfile
        from pathlib import Path
        
        # 先建構套件
        with tempfile.TemporaryDirectory() as tmpdir:
            compiler = create_compiler(output_root=tmpdir)
            compiler.disable_runtime_guard()
            
            entities = {"character": [make_approved_entity("character", "char-001")]}
            compiler.compile_entities(entities)
            
            # 設置運行時模式
            os.environ["NTPE_RUNTIME_MODE"] = "translation"
            
            try:
                reader = create_package_reader(Path(tmpdir) / "v1")
                
                # 應該能正常讀取
                package = reader.package
                assert package.package_id == "ntpe_knowledge"
                
                manifest = reader.manifest
                assert manifest.entity_counts["character"] == 1
                
                entities = reader.get_entities("character")
                assert len(entities) == 1
                
                # 驗證完整性
                assert reader.verify_integrity()
            finally:
                del os.environ["NTPE_RUNTIME_MODE"]
    
    def test_runtime_guard_can_be_disabled_for_testing(self):
        """測試時可禁用運行時防護。"""
        os.environ["NTPE_RUNTIME_MODE"] = "translation"
        
        try:
            compiler = create_compiler()
            compiler.disable_runtime_guard()  # 禁用防護
            
            entities = {"character": [make_approved_entity("character", "char-001")]}
            package = compiler.compile_entities(entities)  # 應該不拋出異常
            
            assert package.package_id == "ntpe_knowledge"
        finally:
            del os.environ["NTPE_RUNTIME_MODE"]
    
    def test_compile_method_also_guarded(self):
        """compile() 方法也應受到防護。"""
        os.environ["NTPE_RUNTIME_MODE"] = "translation"
        
        try:
            compiler = create_compiler()
            # 不禁用 guard
            
            def loader():
                return {"character": [make_approved_entity("character", "char-001")]}
            
            compiler.set_entity_loader(loader)
            
            with pytest.raises(RuntimeInvocationError):
                compiler.compile()
        finally:
            del os.environ["NTPE_RUNTIME_MODE"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])