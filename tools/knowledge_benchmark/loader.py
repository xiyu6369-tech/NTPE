"""
Benchmark Corpus Loader (RM-5.8.3)

Loads the golden dataset benchmark corpus from the filesystem.
Validates benchmark case schema and manifest.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from core.knowledge_benchmark.errors import GoldenDatasetError


BENCHMARK_PREFIX_MAP: Dict[str, str] = {
    "CH": "character",
    "GL": "glossary",
    "SC": "scene",
    "NA": "narrative",
    "ST": "style",
}

EXTRACTOR_TO_PREFIX: Dict[str, str] = {v: k for k, v in BENCHMARK_PREFIX_MAP.items()}

DIFFICULTY_ORDER = ["easy", "medium", "hard"]


@dataclass
class LoadedCase:
    benchmark_id: str
    extractor: str
    difficulty: str
    source_text: str
    expected_entities: List[Dict[str, Any]]
    expected_confidence: str
    tags: List[str]
    notes: str


class BenchmarkCorpusLoader:
    """Loads benchmark cases from the golden corpus directory."""

    BENCHMARKS_ROOT = Path("benchmarks/golden")

    def __init__(self, root_path: Optional[Path] = None):
        self.root_path = Path(root_path) if root_path else Path(".")
        self.corpus_path = self.root_path / self.BENCHMARKS_ROOT

    def load_all(self) -> Dict[str, List[LoadedCase]]:
        cases: Dict[str, List[LoadedCase]] = {}
        for extractor in ["character", "glossary", "scene", "narrative", "style"]:
            cases[extractor] = self.load_extractor(extractor)
        return cases

    def load_extractor(self, extractor: str) -> List[LoadedCase]:
        prefix = EXTRACTOR_TO_PREFIX.get(extractor)
        if prefix is None:
            raise GoldenDatasetError(f"Unknown extractor: {extractor}")

        extractor_dir = self.corpus_path / extractor
        if not extractor_dir.is_dir():
            return []

        cases: List[LoadedCase] = []
        for difficulty in DIFFICULTY_ORDER:
            difficulty_dir = extractor_dir / difficulty
            if not difficulty_dir.is_dir():
                continue
            for json_file in sorted(difficulty_dir.glob("*.json")):
                case = self._load_case(json_file)
                cases.append(case)
        return cases

    def _load_case(self, path: Path) -> LoadedCase:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._validate_case(data, path)
        return LoadedCase(
            benchmark_id=data["benchmark_id"],
            extractor=data["extractor"],
            difficulty=data["difficulty"],
            source_text=data["source_text"],
            expected_entities=data["expected_entities"],
            expected_confidence=data["expected_confidence"],
            tags=data["tags"],
            notes=data["notes"],
        )

    def load_by_id(self, benchmark_id: str) -> Optional[LoadedCase]:
        parts = benchmark_id.split("-")
        if len(parts) < 3:
            return None
        prefix = parts[0]
        difficulty = parts[1].lower()
        extractor = BENCHMARK_PREFIX_MAP.get(prefix)
        if extractor is None:
            return None
        path = self.corpus_path / extractor / difficulty / f"{benchmark_id}.json"
        if not path.is_file():
            return None
        return self._load_case(path)

    def load_manifest(self) -> Dict[str, Any]:
        manifest_path = self.root_path / "benchmarks/spec/benchmark_manifest.json"
        if not manifest_path.is_file():
            return {}
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _validate_case(data: Dict[str, Any], path: Path) -> None:
        required = ["benchmark_id", "extractor", "difficulty", "source_text", "expected_entities", "expected_confidence", "tags", "notes"]
        missing = [key for key in required if key not in data]
        if missing:
            raise GoldenDatasetError(f"Missing required fields {missing} in {path}")
        if data["extractor"] not in ("character", "glossary", "scene", "narrative", "style"):
            raise GoldenDatasetError(f"Invalid extractor '{data['extractor']}' in {path}")
        if data["difficulty"] not in ("easy", "medium", "hard"):
            raise GoldenDatasetError(f"Invalid difficulty '{data['difficulty']}' in {path}")
        if data["expected_confidence"] not in ("high", "medium", "low"):
            raise GoldenDatasetError(f"Invalid confidence '{data['expected_confidence']}' in {path}")
        if not isinstance(data["expected_entities"], list) or len(data["expected_entities"]) == 0:
            raise GoldenDatasetError(f"expected_entities must be non-empty array in {path}")
        if not isinstance(data["tags"], list):
            raise GoldenDatasetError(f"tags must be array in {path}")
        if not isinstance(data["source_text"], str) or not data["source_text"].strip():
            raise GoldenDatasetError(f"source_text must be non-empty string in {path}")