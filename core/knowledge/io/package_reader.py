"""Foundation-08.8 Knowledge package reader."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from ..contracts import KnowledgeItem, KnowledgeSnapshot
from .validation import KnowledgePackageValidator


class KnowledgePackageReader:
    """Read JSON or ZIP Knowledge packages."""

    version = "foundation-08.8"

    def __init__(self, validator: KnowledgePackageValidator | None = None):
        self.validator = validator or KnowledgePackageValidator()

    def read_dict(self, package: Dict[str, Any], validate: bool = True) -> Dict[str, Any]:
        payload = dict(package or {})
        if validate:
            self.validator.ensure_valid(payload)
        return payload

    def read_json(self, path: str | Path, validate: bool = True) -> Dict[str, Any]:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return self.read_dict(payload, validate=validate)

    def read_zip(self, path: str | Path, validate: bool = True) -> Dict[str, Any]:
        with zipfile.ZipFile(path, "r") as archive:
            payload = json.loads(archive.read("knowledge_package.json").decode("utf-8"))
        return self.read_dict(payload, validate=validate)

    def items(self, package: Dict[str, Any]) -> List[KnowledgeItem]:
        payload = self.read_dict(package)
        return [KnowledgeItem.from_dict(item) for item in payload.get("items", [])]

    def snapshots(self, package: Dict[str, Any]) -> List[KnowledgeSnapshot]:
        payload = self.read_dict(package)
        return [KnowledgeSnapshot.from_dict(snapshot) for snapshot in payload.get("snapshots", [])]


__all__ = ["KnowledgePackageReader"]
