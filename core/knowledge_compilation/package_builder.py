"""
Knowledge Compilation Engine - Package Builder

建構輸出套件檔案：
- artifacts/knowledge_packages/v1/
    ├── characters.json
    ├── glossary.json
    ├── scenes.json
    ├── narrative.json
    ├── style.json
    └── manifest.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import CompilationPackage, CompilationManifest, KNOWN_ENTITY_TYPES
from .checksum import ChecksumCalculator, DEFAULT_CALCULATOR
from .errors import PackageBuildError


class PackageBuilder:
    """
    套件建構器。
    
    將 CompilationPackage 輸出為決定性的檔案結構。
    """
    
    def __init__(
        self,
        output_root: str | Path = "artifacts/knowledge_packages",
        calculator: ChecksumCalculator | None = None,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> None:
        self._output_root = Path(output_root)
        self._calculator = calculator or DEFAULT_CALCULATOR
        self._indent = indent
        self._ensure_ascii = ensure_ascii
    
    @property
    def output_root(self) -> Path:
        return self._output_root
    
    def build(self, package: CompilationPackage, version_dir: str = "v1") -> Path:
        """
        建構並寫入套件檔案。
        
        Args:
            package: 編譯套件
            version_dir: 版本目錄名稱（如 "v1"）
            
        Returns:
            輸出目錄路徑
        """
        output_dir = self._output_root / version_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 寫入各實體類型檔案
        for entity_type in KNOWN_ENTITY_TYPES:
            if entity_type not in package.entities:
                continue
            
            entities = package.entities[entity_type]
            if not entities:
                continue
            
            # 決定性排序：entity_id -> version
            sorted_entities = sorted(entities, key=lambda e: (e.get("entity_id", ""), e.get("version", 1)))
            
            # Handle irregular plurals
            plural_map = {
                "glossary": "glossaries",
            }
            plural = plural_map.get(entity_type, f"{entity_type}s")
            file_path = output_dir / f"{plural}.json"
            self._write_json_file(file_path, sorted_entities)
        
        # 寫入 manifest.json
        manifest_path = output_dir / "manifest.json"
        self._write_json_file(manifest_path, package.manifest.to_dict())
        
        # 寫入 package.json（完整套件）
        package_path = output_dir / "package.json"
        self._write_json_file(package_path, package.to_dict())
        
        return output_dir
    
    def build_manifest_only(self, manifest: CompilationManifest, version_dir: str = "v1") -> Path:
        """僅建構 manifest 檔案。"""
        output_dir = self._output_root / version_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        manifest_path = output_dir / "manifest.json"
        self._write_json_file(manifest_path, manifest.to_dict())
        
        return output_dir
    
    def _write_json_file(self, path: Path, data: Any) -> None:
        """寫入 JSON 檔案（決定性格式）。"""
        try:
            json_str = json.dumps(
                data,
                indent=self._indent,
                ensure_ascii=self._ensure_ascii,
                sort_keys=True,
            )
            # Windows 兼容：使用 UTF-8 無 BOM
            path.write_text(json_str, encoding="utf-8", newline="\n")
        except Exception as e:
            raise PackageBuildError(f"寫入檔案失敗：{path}", {"path": str(path), "error": str(e)})
    def verify_package(self, package: CompilationPackage) -> bool:
        """驗證套件的 checksum。"""
        return package.verify_checksum(self._calculator)
    
    def load_package(self, package_dir: str | Path) -> CompilationPackage:
        """
        從目錄載入套件（運行時唯讀）。
        
        Args:
            package_dir: 套件目錄路徑
            
        Returns:
            CompilationPackage 實例
        """
        package_path = Path(package_dir) / "package.json"
        if not package_path.exists():
            raise PackageBuildError(f"套件檔案不存在：{package_path}")
        
        try:
            data = json.loads(package_path.read_text(encoding="utf-8"))
            return CompilationPackage.from_dict(data)
        except Exception as e:
            raise PackageBuildError(f"載入套件失敗：{package_path}", {"error": str(e)})
    
    def load_manifest(self, package_dir: str | Path) -> CompilationManifest:
        """載入 manifest。"""
        manifest_path = Path(package_dir) / "manifest.json"
        if not manifest_path.exists():
            raise PackageBuildError(f"Manifest 檔案不存在：{manifest_path}")
        
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            return CompilationManifest.from_dict(data)
        except Exception as e:
            raise PackageBuildError(f"載入 Manifest 失敗：{manifest_path}", {"error": str(e)})
    
    def load_entities(self, package_dir: str | Path, entity_type: str) -> List[Dict[str, Any]]:
        """載入特定類型的實體。"""
        # Handle irregular plurals
        plural_map = {
            "glossary": "glossaries",
        }
        plural = plural_map.get(entity_type, f"{entity_type}s")
        file_path = Path(package_dir) / f"{plural}.json"
        if not file_path.exists():
            return []
        
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception as e:
            raise PackageBuildError(f"載入實體失敗：{file_path}", {"error": str(e)})


class PackageReader:
    """
    運行時唯讀套件讀取器。
    
    這是運行時邊界允許使用的介面。
    編譯器（KnowledgeCompiler）屬於建構時，禁止在運行時調用。
    """
    
    def __init__(self, package_dir: str | Path) -> None:
        self._package_dir = Path(package_dir)
        self._builder = PackageBuilder()
        self._package: CompilationPackage | None = None
        self._manifest: CompilationManifest | None = None
    
    @property
    def package_dir(self) -> Path:
        return self._package_dir
    
    @property
    def package(self) -> CompilationPackage:
        """載入完整套件（延遲載入）。"""
        if self._package is None:
            self._package = self._builder.load_package(self._package_dir)
        return self._package
    
    @property
    def manifest(self) -> CompilationManifest:
        """載入 manifest（延遲載入）。"""
        if self._manifest is None:
            self._manifest = self._builder.load_manifest(self._package_dir)
        return self._manifest
    
    def get_entities(self, entity_type: str) -> List[Dict[str, Any]]:
        """獲取特定類型的所有實體。"""
        return self._builder.load_entities(self._package_dir, entity_type)
    
    def get_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any] | None:
        """獲取單一實體。"""
        entities = self.get_entities(entity_type)
        for entity in entities:
            if entity.get("entity_id") == entity_id:
                return entity
        return None
    
    def get_all_entities(self) -> List[Dict[str, Any]]:
        """獲取所有實體。"""
        return self.package.get_all_entities()
    
    def get_entity_types(self) -> List[str]:
        """獲取包含的實體類型。"""
        return self.package.get_entity_types()
    
    def verify_integrity(self) -> bool:
        """驗證套件完整性。"""
        return self._builder.verify_package(self.package)


# 便利函數
def create_package_reader(package_dir: str | Path) -> PackageReader:
    """建立套件讀取器。"""
    return PackageReader(package_dir)