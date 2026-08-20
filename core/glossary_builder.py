# =====================================================
# NTPE Glossary Builder v1.1.1
# 功能：
# 1. 讀取 analysis/*_glossary_auto.json
# 2. 合併所有卷數術語候選
# 3. 自動分類 abbreviation / code / english_term / unknown
# 4. 套用 glossary_override.json 手動術語表
# 5. 輸出 memory/glossary.json
# 6. 輸出 glossary_report.txt / glossary.csv
# 7. 整合 Character Resolver，輸出 memory/character_alias_index.json
# =====================================================

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Any

from core.character_resolver import CharacterResolver


ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = ROOT / "analysis"
MEMORY_DIR = ROOT / "memory"
LOG_DIR = ROOT / "logs"
OVERRIDE_FILE = ROOT / "glossary_override.json"
MIN_TOTAL_COUNT = 2


def ensure_dirs() -> None:
    for folder in [ANALYSIS_DIR, MEMORY_DIR, LOG_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    ensure_dirs()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line)
    log_file = LOG_DIR / "glossary_builder_log.txt"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def infer_book_name(path: Path) -> str:
    name = path.stem
    name = name.replace("_glossary_auto", "")
    name = name.replace("_normalized", "")
    return name


def list_glossary_files() -> list[Path]:
    ensure_dirs()
    return sorted(
        ANALYSIS_DIR.glob("*_glossary_auto.json"),
        key=lambda p: p.name.lower(),
    )


def load_override() -> dict:
    if not OVERRIDE_FILE.exists():
        log("未找到 glossary_override.json，將只使用自動術語候選")
        return {}

    try:
        data = load_json(OVERRIDE_FILE)
        if not isinstance(data, dict):
            log("glossary_override.json 格式不是 dict，已忽略")
            return {}
        return data
    except Exception as e:
        log(f"glossary_override.json 讀取失敗，已忽略：{e}")
        return {}


def normalize_term(term: str) -> str:
    term = str(term).strip()
    term = re.sub(r"\s+", " ", term)
    return term


def classify_term(term: str) -> str:
    if re.fullmatch(r"[A-Z]{2,}", term):
        return "abbreviation"

    if re.fullmatch(r"[A-Za-z]+[0-9]+[A-Za-z0-9\-]*", term):
        return "code"

    if re.fullmatch(r"[A-Za-z][A-Za-z\-]{3,}", term):
        if term[:1].isupper():
            return "proper_english_term"
        return "english_term"

    if re.search(r"[0-9]", term) and re.search(r"[A-Za-z]", term):
        return "code"

    if re.search(r"[가-힣]+\s+[가-힣]+", term):
        return "person_name"

    return "unknown"


def confidence_score(total_count: int, book_count: int, locked: bool) -> float:
    if locked:
        return 1.0

    score = 0.2

    if total_count >= 100:
        score += 0.45
    elif total_count >= 50:
        score += 0.35
    elif total_count >= 20:
        score += 0.25
    elif total_count >= 10:
        score += 0.15
    elif total_count >= 5:
        score += 0.08

    if book_count >= 6:
        score += 0.3
    elif book_count >= 4:
        score += 0.22
    elif book_count >= 2:
        score += 0.12

    return round(min(score, 0.95), 3)


def create_empty_item(term: str, status: str) -> dict:
    return {
        "source": term,
        "translation": "",
        "category": classify_term(term),
        "total_count": 0,
        "books": {},
        "book_count": 0,
        "locked": False,
        "status": status,
        "aliases": [],
        "notes": [],
        "confidence": 0.0,
        "created_by": "NTPE Glossary Builder v1.1.1",
    }


def merge_glossary(files: list[Path]) -> dict:
    merged = {}

    for path in files:
        book = infer_book_name(path)
        data = load_json(path)

        if not isinstance(data, dict):
            log(f"跳過格式異常：{path.name}")
            continue

        for term, item in data.items():
            term = normalize_term(term)
            if not term:
                continue

            count = 0
            if isinstance(item, dict):
                count = int(item.get("count", 0) or 0)
            elif isinstance(item, int):
                count = item

            if count <= 0:
                continue

            if term not in merged:
                merged[term] = create_empty_item(term, "auto")

            merged[term]["total_count"] += count
            merged[term]["books"][book] = merged[term]["books"].get(book, 0) + count

    for item in merged.values():
        item["book_count"] = len(item["books"])

    return merged


def apply_override(merged: dict, override: dict) -> dict:
    for term, ov in override.items():
        term = normalize_term(term)
        if not term:
            continue

        if term not in merged:
            merged[term] = create_empty_item(term, "manual_only")

        if isinstance(ov, str):
            merged[term]["translation"] = ov
            merged[term]["locked"] = True
            merged[term]["status"] = "manual_locked"
            merged[term]["notes"].append("manual override string")
            continue

        if isinstance(ov, dict):
            translation = ov.get("translation", "")
            category = ov.get("category", "")
            locked = ov.get("locked", True)
            aliases = ov.get("aliases", [])
            note = ov.get("note", "manual override")

            if translation:
                merged[term]["translation"] = translation
            if category:
                merged[term]["category"] = category

            merged[term]["locked"] = bool(locked)
            if merged[term]["locked"]:
                merged[term]["status"] = "manual_locked"
            else:
                merged[term]["status"] = "manual_unlocked"

            if isinstance(aliases, list):
                for alias in aliases:
                    alias = normalize_term(alias)
                    if alias and alias not in merged[term]["aliases"]:
                        merged[term]["aliases"].append(alias)

            if note:
                merged[term]["notes"].append(str(note))

    return merged


def finalize_glossary(merged: dict) -> dict:
    filtered = {}

    for term, item in merged.items():
        if item["total_count"] >= MIN_TOTAL_COUNT or item["locked"]:
            item["confidence"] = confidence_score(
                item.get("total_count", 0),
                item.get("book_count", 0),
                item.get("locked", False),
            )
            filtered[term] = item

    sorted_items = sorted(
        filtered.items(),
        key=lambda kv: (
            not kv[1].get("locked", False),
            kv[1].get("category", ""),
            -kv[1].get("book_count", 0),
            -kv[1].get("total_count", 0),
            kv[0].lower(),
        ),
    )

    return dict(sorted_items)


def build_character_alias_index(glossary: dict) -> dict:
    resolver = CharacterResolver()
    resolver.load_from_glossary(glossary)
    return resolver.export_alias_index()


def build_summary(glossary: dict, source_files: list[Path], character_alias_index: dict | None = None) -> dict:
    category_counts = {}
    locked_count = 0
    translated_count = 0

    for item in glossary.values():
        category = item.get("category", "unknown")
        category_counts[category] = category_counts.get(category, 0) + 1

        if item.get("locked"):
            locked_count += 1
        if item.get("translation"):
            translated_count += 1

    return {
        "ntpe_module": "Glossary Builder",
        "version": "1.1.1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_file_count": len(source_files),
        "source_files": [p.name for p in source_files],
        "term_total": len(glossary),
        "locked_count": locked_count,
        "translated_count": translated_count,
        "character_alias_count": (character_alias_index or {}).get("alias_count", 0),
        "character_collision_count": len((character_alias_index or {}).get("collisions", {})),
        "category_counts": category_counts,
    }


def save_glossary(glossary: dict, summary: dict) -> None:
    output = {
        "summary": summary,
        "terms": glossary,
    }
    save_json(MEMORY_DIR / "glossary.json", output)
    save_json(MEMORY_DIR / "glossary_only.json", glossary)


def save_character_alias_index(character_alias_index: dict) -> None:
    save_json(MEMORY_DIR / "character_alias_index.json", character_alias_index)


def save_report(glossary: dict, summary: dict, character_alias_index: dict | None = None) -> None:
    character_alias_index = character_alias_index or {}

    lines = []
    lines.append("====================================")
    lines.append("NTPE Glossary Builder v1.1.1")
    lines.append("====================================")
    lines.append("")
    lines.append(f"產生時間：{summary['generated_at']}")
    lines.append(f"來源檔案數：{summary['source_file_count']}")
    lines.append(f"術語總數：{summary['term_total']}")
    lines.append(f"已鎖定術語：{summary['locked_count']}")
    lines.append(f"已有譯名：{summary['translated_count']}")
    lines.append(f"角色別名數：{summary['character_alias_count']}")
    lines.append(f"角色別名碰撞數：{summary['character_collision_count']}")
    lines.append("")
    lines.append("〖分類統計〗")
    for category, count in sorted(summary["category_counts"].items()):
        lines.append(f"- {category}: {count}")

    lines.append("")
    lines.append("〖來源檔案〗")
    for name in summary["source_files"]:
        lines.append(f"- {name}")

    lines.append("")
    lines.append("〖鎖定術語〗")
    for term, item in glossary.items():
        if item.get("locked"):
            lines.append(
                f"- {term} -> {item.get('translation', '')} "
                f"[{item.get('category', '')}] "
                f"(總次數：{item.get('total_count', 0)}，卷數：{item.get('book_count', 0)})"
            )

    aliases = character_alias_index.get("aliases", {})
    if aliases:
        lines.append("")
        lines.append("〖角色別名索引〗")
        for source, target in aliases.items():
            lines.append(f"- {source} -> {target}")

    collisions = character_alias_index.get("collisions", {})
    if collisions:
        lines.append("")
        lines.append("〖角色別名碰撞警告〗")
        for source, targets in collisions.items():
            lines.append(f"- {source}: {', '.join(targets)}")

    lines.append("")
    lines.append("〖自動候選 TOP 120〗")
    auto_items = [
        (term, item)
        for term, item in glossary.items()
        if not item.get("locked")
    ]
    auto_items = sorted(
        auto_items,
        key=lambda kv: (
            -kv[1].get("book_count", 0),
            -kv[1].get("total_count", 0),
            kv[0].lower(),
        ),
    )

    for term, item in auto_items[:120]:
        lines.append(
            f"- {term} "
            f"[{item.get('category', '')}] "
            f"(總次數：{item.get('total_count', 0)}，"
            f"卷數：{item.get('book_count', 0)}，"
            f"信心：{item.get('confidence', 0)})"
        )

    lines.append("")
    lines.append("====================================")
    lines.append("完成")
    lines.append("====================================")
    lines.append("")

    (MEMORY_DIR / "glossary_report.txt").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def save_csv(glossary: dict) -> None:
    path = MEMORY_DIR / "glossary.csv"

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "source",
            "translation",
            "category",
            "total_count",
            "book_count",
            "confidence",
            "locked",
            "status",
            "books",
            "aliases",
            "notes",
        ])

        for term, item in glossary.items():
            books = "; ".join(
                f"{book}:{count}"
                for book, count in sorted(item.get("books", {}).items())
            )
            aliases = "; ".join(item.get("aliases", []))
            notes = "; ".join(item.get("notes", []))

            writer.writerow([
                term,
                item.get("translation", ""),
                item.get("category", ""),
                item.get("total_count", 0),
                item.get("book_count", 0),
                item.get("confidence", 0),
                item.get("locked", False),
                item.get("status", ""),
                books,
                aliases,
                notes,
            ])


# =====================================================
# P0 Stage 5 Batch 5.4 — Series Glossary Extensions
# =====================================================

SERIES_GLOSSARY_SCHEMA_NAME = "ntpe.series_glossary"
SERIES_GLOSSARY_SCHEMA_VERSION = "1.0"


class SeriesGlossaryValidationError(Exception):
    """Raised when SeriesGlossary schema validation fails."""
    pass


class SeriesGlossaryIntegrityError(Exception):
    """Raised when SeriesGlossary fingerprint verification fails (fail-closed)."""
    pass


@dataclass(frozen=True)
class SeriesGlossaryTerm:
    """Persistent canonical glossary term — series-scoped."""
    source: str
    translation: str
    category: str
    locked: bool
    status: str  # "manual_locked" | "auto_high_confidence" | "series_canonical"
    source_books: tuple[str, ...]
    book_coverage: int
    confidence: float
    aliases: tuple[str, ...]
    notes: tuple[str, ...]
    approved_at: str
    approved_by: str
    version: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "translation": self.translation,
            "category": self.category,
            "locked": self.locked,
            "status": self.status,
            "source_books": list(self.source_books),
            "book_coverage": self.book_coverage,
            "confidence": self.confidence,
            "aliases": list(self.aliases),
            "notes": list(self.notes),
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SeriesGlossaryTerm":
        return cls(
            source=data["source"],
            translation=data["translation"],
            category=data["category"],
            locked=data["locked"],
            status=data["status"],
            source_books=tuple(data.get("source_books", [])),
            book_coverage=data["book_coverage"],
            confidence=data["confidence"],
            aliases=tuple(data.get("aliases", [])),
            notes=tuple(data.get("notes", [])),
            approved_at=data["approved_at"],
            approved_by=data["approved_by"],
            version=data["version"],
        )

    def with_updated_translation(self, new_translation: str, approved_by: str, now: str) -> "SeriesGlossaryTerm":
        """Return new term with updated translation (version increment)."""
        return SeriesGlossaryTerm(
            source=self.source,
            translation=new_translation,
            category=self.category,
            locked=self.locked,
            status=self.status,
            source_books=self.source_books,
            book_coverage=self.book_coverage,
            confidence=self.confidence,
            aliases=self.aliases,
            notes=self.notes + (f"updated from {self.translation} to {new_translation}",),
            approved_at=now,
            approved_by=approved_by,
            version=self.version + 1,
        )


@dataclass(frozen=True)
class SeriesGlossary:
    """Series-canonical glossary — persistent across volumes."""
    schema_name: str
    schema_version: str
    series_id: str
    terms: dict[str, SeriesGlossaryTerm]
    glossary_hash: str

    def to_dict(self, include_glossary_hash: bool = True) -> dict[str, Any]:
        payload = {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "series_id": self.series_id,
            "terms": {k: v.to_dict() for k, v in self.terms.items()},
        }
        if include_glossary_hash:
            payload["glossary_hash"] = self.glossary_hash
        return payload

    def get_glossary_hash(self) -> str:
        """Return the glossary hash (same as glossary_hash field)."""
        return self.glossary_hash

    def get_locked_dictionary(self) -> dict[str, str]:
        """Extract locked terms for frozen component integration (adapter pattern)."""
        return {
            term.source: term.translation
            for term in self.terms.values()
            if term.locked or term.confidence >= 0.95
        }

    def get_alias_map(self) -> dict[str, str]:
        """Extract aliases for GlossaryContext alias_map."""
        alias_map = {}
        for term in self.terms.values():
            for alias in term.aliases:
                if alias not in alias_map:
                    alias_map[alias] = term.translation
        return alias_map


@dataclass(frozen=True)
class GlossaryPromotionRecord:
    """Audit trail for Book → Series glossary promotion."""
    promotion_id: str
    series_id: str
    book_identity: str
    source_term: str
    previous_translation: str | None
    new_translation: str
    action: str  # "created" | "no_op" | "conflict" | "updated"
    resolved_by: str | None
    resolved_at: str
    source_status: str  # "locked" | "auto_high_confidence"


def to_canonical_json(obj: dict) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_series_glossary_fingerprint(series_glossary_dict: dict) -> str:
    """Compute SHA-256 of canonical glossary payload (excluding glossary_hash itself)."""
    payload = {k: v for k, v in series_glossary_dict.items() if k != "glossary_hash"}
    canonical = to_canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_series_glossary_path(output_root: Path, series_id: str) -> Path:
    """Get the path for series glossary file."""
    series_dir = output_root / "series" / series_id
    return series_dir / f"series_glossary_{series_id}.json"


def save_series_glossary(series_glossary: SeriesGlossary, path: Path) -> None:
    """Save SeriesGlossary to disk with atomic write and fingerprint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    data = series_glossary.to_dict(include_glossary_hash=True)
    temp_path.write_text(
        to_canonical_json(data),
        encoding="utf-8"
    )
    temp_path.replace(path)


def load_series_glossary_from_path(path: Path, expected_series_id: str) -> SeriesGlossary:
    """Load SeriesGlossary from disk with integrity verification (fail-closed)."""
    if not path.exists():
        # Return empty glossary for fresh series
        return SeriesGlossary(
            schema_name=SERIES_GLOSSARY_SCHEMA_NAME,
            schema_version=SERIES_GLOSSARY_SCHEMA_VERSION,
            series_id=expected_series_id,
            terms={},
            glossary_hash="",
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SeriesGlossaryValidationError(f"Invalid JSON in glossary file: {e}")

    # Schema validation
    if data.get("schema_name") != SERIES_GLOSSARY_SCHEMA_NAME:
        raise SeriesGlossaryValidationError(f"Invalid schema_name: {data.get('schema_name')}")
    if data.get("schema_version") != SERIES_GLOSSARY_SCHEMA_VERSION:
        raise SeriesGlossaryValidationError(f"Invalid schema_version: {data.get('schema_version')}")
    if data.get("series_id") != expected_series_id:
        raise SeriesGlossaryValidationError(f"Series ID mismatch: expected {expected_series_id}, got {data.get('series_id')}")

    # Fingerprint verification (fail-closed)
    stored_hash = data.get("glossary_hash", "")
    if stored_hash:
        computed_hash = compute_series_glossary_fingerprint(data)
        if stored_hash != computed_hash:
            raise SeriesGlossaryIntegrityError(f"Glossary fingerprint mismatch: stored={stored_hash}, computed={computed_hash}")

    # Parse terms
    terms = {}
    for source, term_data in data.get("terms", {}).items():
        try:
            terms[source] = SeriesGlossaryTerm.from_dict(term_data)
        except Exception as e:
            raise SeriesGlossaryValidationError(f"Invalid term data for '{source}': {e}")

    return SeriesGlossary(
        schema_name=data["schema_name"],
        schema_version=data["schema_version"],
        series_id=data["series_id"],
        terms=terms,
        glossary_hash=stored_hash,
    )


def load_series_glossary(series_id: str, output_root: Path) -> SeriesGlossary:
    """Load SeriesGlossary from output root with integrity verification."""
    path = get_series_glossary_path(output_root, series_id)
    return load_series_glossary_from_path(path, series_id)


def validate_series_glossary(series_glossary: SeriesGlossary) -> None:
    """Validate SeriesGlossary business rules."""
    if not series_glossary.schema_name == SERIES_GLOSSARY_SCHEMA_NAME:
        raise SeriesGlossaryValidationError("Invalid schema_name")
    if not series_glossary.schema_version == SERIES_GLOSSARY_SCHEMA_VERSION:
        raise SeriesGlossaryValidationError("Invalid schema_version")

    for term in series_glossary.terms.values():
        if not term.locked and term.confidence < 0.95:
            raise SeriesGlossaryValidationError(f"Term '{term.source}' is not locked and confidence < 0.95")
        if not 0.0 <= term.confidence <= 1.0:
            raise SeriesGlossaryValidationError(f"Term '{term.source}' confidence out of range: {term.confidence}")
        if term.version < 1:
            raise SeriesGlossaryValidationError(f"Term '{term.source}' version < 1: {term.version}")


def _get_book_glossary_terms(series_id: str, book_identity: str, output_root: Path) -> dict[str, dict]:
    """Load book glossary from analysis file for promotion."""
    # Look for analysis file matching the book
    analysis_dir = output_root.parent / "analysis"
    if not analysis_dir.exists():
        return {}

    for file in analysis_dir.glob("*_glossary_auto.json"):
        if infer_book_name(file) == book_identity:
            data = load_json(file)
            if isinstance(data, dict):
                return data
    return {}


def build_series_glossary(
    series_id: str,
    series_manifest: Any,  # SeriesManifest from series_identity
    output_root: Path,
    character_memory_store: Any | None = None,  # SeriesMemoryStore
    entity_registry: Any | None = None,  # SeriesEntityRegistry
) -> SeriesGlossary:
    """
    Build canonical glossary from all completed books in series.

    Rules:
    - Only terms from books with status="completed" or "promoted"
    - Only terms with locked=True or confidence >= 0.95
    - Merged across all volumes (reuse existing merge_glossary logic)
    - EntityRegistry canonical names included as locked terms
    - CharacterMemory canonical names included as locked terms
    """
    # Collect completed book identities from SeriesManifest
    completed_book_identities = []
    for book in series_manifest.books:
        if book.status.value in ("completed", "promoted"):
            completed_book_identities.append(book.book_identity)

    if not completed_book_identities:
        # No completed books yet - return empty glossary
        return SeriesGlossary(
            schema_name=SERIES_GLOSSARY_SCHEMA_NAME,
            schema_version=SERIES_GLOSSARY_SCHEMA_VERSION,
            series_id=series_id,
            terms={},
            glossary_hash="",
        )

    # Collect glossary files for completed books
    glossary_files = []
    for book_id in completed_book_identities:
        # Find analysis file for this book
        analysis_dir = output_root.parent / "analysis"
        if analysis_dir.exists():
            for file in analysis_dir.glob("*_glossary_auto.json"):
                if infer_book_name(file) == book_id:
                    glossary_files.append(file)

    if not glossary_files:
        # No glossary files found
        return SeriesGlossary(
            schema_name=SERIES_GLOSSARY_SCHEMA_NAME,
            schema_version=SERIES_GLOSSARY_SCHEMA_VERSION,
            series_id=series_id,
            terms={},
            glossary_hash="",
        )

    # Merge glossaries from completed books using existing logic
    merged = merge_glossary(glossary_files)
    override = load_override()
    merged = apply_override(merged, override)
    finalized = finalize_glossary(merged)

    # Filter: only locked or confidence >= 0.95
    filtered_terms = {}
    for source, item in finalized.items():
        if item.get("locked") or item.get("confidence", 0) >= 0.95:
            filtered_terms[source] = item

    # Enrich with EntityRegistry canonical names (locked terms)
    if entity_registry is not None:
        for record in entity_registry.get_all():
            if record.source_name not in filtered_terms:
                filtered_terms[record.source_name] = {
                    "source": record.source_name,
                    "translation": record.canonical_target,
                    "category": "person_name",
                    "total_count": 0,
                    "books": {},
                    "book_count": 0,
                    "locked": True,
                    "status": "series_canonical",
                    "aliases": [],
                    "notes": [f"from entity_registry: {record.series_entity_id}"],
                    "confidence": 1.0,
                    "created_by": "NTPE Series Glossary Builder",
                }

    # Enrich with CharacterMemory canonical names (locked terms)
    if character_memory_store is not None:
        for record in character_memory_store.get_all_canonical_facts():
            if record.korean_name not in filtered_terms and record.canonical_name:
                filtered_terms[record.korean_name] = {
                    "source": record.korean_name,
                    "translation": record.canonical_name,
                    "category": "person_name",
                    "total_count": 0,
                    "books": {},
                    "book_count": 0,
                    "locked": True,
                    "status": "series_canonical",
                    "aliases": list(record.aliases),
                    "notes": [f"from character_memory: {record.series_character_id}"],
                    "confidence": 1.0,
                    "created_by": "NTPE Series Glossary Builder",
                }

    # Convert to SeriesGlossaryTerm objects
    now = datetime.now().isoformat(timespec="seconds")
    series_terms = {}
    for source, item in filtered_terms.items():
        # Determine status
        if item.get("status") == "manual_locked" or item.get("locked"):
            status = "manual_locked" if item.get("locked") else "auto_high_confidence"
            if item.get("status") == "series_canonical":
                status = "series_canonical"
        else:
            status = "auto_high_confidence"

        series_terms[source] = SeriesGlossaryTerm(
            source=source,
            translation=item.get("translation", ""),
            category=item.get("category", "unknown"),
            locked=item.get("locked", False) or item.get("confidence", 0) >= 0.95,
            status=status,
            source_books=tuple(item.get("books", {}).keys()),
            book_coverage=item.get("book_count", 0),
            confidence=item.get("confidence", 1.0 if item.get("locked") else 0.95),
            aliases=tuple(item.get("aliases", [])),
            notes=tuple(item.get("notes", [])),
            approved_at=item.get("notes", [now])[-1] if item.get("notes") else now,
            approved_by="series_promotion" if status == "series_canonical" else "auto_high_confidence",
            version=1,
        )

    # Compute fingerprint
    glossary = SeriesGlossary(
        schema_name=SERIES_GLOSSARY_SCHEMA_NAME,
        schema_version=SERIES_GLOSSARY_SCHEMA_VERSION,
        series_id=series_id,
        terms=series_terms,
        glossary_hash="",  # Will be computed
    )

    fingerprint = compute_series_glossary_fingerprint(glossary.to_dict(include_glossary_hash=False))
    glossary = SeriesGlossary(
        schema_name=glossary.schema_name,
        schema_version=glossary.schema_version,
        series_id=glossary.series_id,
        terms=glossary.terms,
        glossary_hash=fingerprint,
    )

    validate_series_glossary(glossary)
    return glossary


def merge_into_series_glossary(
    series_glossary: SeriesGlossary,
    book_glossary: dict,  # Terms dict from glossary_builder output
    book_identity: str,
    approval_gate: bool = True,
) -> tuple[SeriesGlossary, tuple[GlossaryPromotionRecord, ...]]:
    """
    Promote locked/high-confidence terms from completed book to SeriesGlossary.

    Requires MANUAL approval gate (D-07 frozen).
    Only processes terms with locked=True or confidence >= 0.95.
    """
    if not approval_gate:
        raise SeriesGlossaryValidationError(
            "Glossary promotion requires MANUAL approval gate (D-07 frozen). "
            "Auto-promotion is not permitted."
        )

    now = datetime.now().isoformat(timespec="seconds")
    promotion_id = hashlib.sha256(f"{series_glossary.series_id}|{book_identity}|{now}".encode()).hexdigest()[:12]

    promotions = []
    updated_terms = dict(series_glossary.terms)

    for source, item in book_glossary.items():
        # Check eligibility: locked or confidence >= 0.95
        is_locked = item.get("locked", False)
        confidence = item.get("confidence", 0)
        translation = item.get("translation", "")

        if not translation:
            continue

        if not (is_locked or confidence >= 0.95):
            continue  # Not eligible for promotion

        source_status = "locked" if is_locked else "auto_high_confidence"

        if source not in updated_terms:
            # CREATE new term
            new_term = SeriesGlossaryTerm(
                source=source,
                translation=translation,
                category=item.get("category", "unknown"),
                locked=True,
                status=source_status,
                source_books=(book_identity,),
                book_coverage=1,
                confidence=1.0 if is_locked else confidence,
                aliases=tuple(item.get("aliases", [])),
                notes=(f"promoted from {book_identity}",),
                approved_at=now,
                approved_by="series_promotion",
                version=1,
            )
            updated_terms[source] = new_term
            promotions.append(GlossaryPromotionRecord(
                promotion_id=promotion_id,
                series_id=series_glossary.series_id,
                book_identity=book_identity,
                source_term=source,
                previous_translation=None,
                new_translation=translation,
                action="created",
                resolved_by="user",
                resolved_at=now,
                source_status=source_status,
            ))
        else:
            # Existing term - check for conflict
            existing = updated_terms[source]
            if existing.translation == translation:
                # NO-OP
                promotions.append(GlossaryPromotionRecord(
                    promotion_id=promotion_id,
                    series_id=series_glossary.series_id,
                    book_identity=book_identity,
                    source_term=source,
                    previous_translation=existing.translation,
                    new_translation=translation,
                    action="no_op",
                    resolved_by=None,
                    resolved_at=now,
                    source_status=source_status,
                ))
            else:
                # CONFLICT - different translation
                promotions.append(GlossaryPromotionRecord(
                    promotion_id=promotion_id,
                    series_id=series_glossary.series_id,
                    book_identity=book_identity,
                    source_term=source,
                    previous_translation=existing.translation,
                    new_translation=translation,
                    action="conflict",
                    resolved_by=None,  # Requires manual resolution
                    resolved_at=now,
                    source_status=source_status,
                ))

    # Build updated glossary
    updated_glossary = SeriesGlossary(
        schema_name=series_glossary.schema_name,
        schema_version=series_glossary.schema_version,
        series_id=series_glossary.series_id,
        terms=updated_terms,
        glossary_hash="",
    )

    fingerprint = compute_series_glossary_fingerprint(updated_glossary.to_dict(include_glossary_hash=False))
    updated_glossary = SeriesGlossary(
        schema_name=updated_glossary.schema_name,
        schema_version=updated_glossary.schema_version,
        series_id=updated_glossary.series_id,
        terms=updated_glossary.terms,
        glossary_hash=fingerprint,
    )

    validate_series_glossary(updated_glossary)
    return updated_glossary, tuple(promotions)


def resolve_promotion_conflict(
    series_glossary: SeriesGlossary,
    source_term: str,
    resolution: str,  # "book_wins" | "series_wins" | "manual"
    resolved_by: str,
    manual_value: str | None = None,
) -> tuple[SeriesGlossary, GlossaryPromotionRecord]:
    """
    Resolve a promotion conflict manually.

    Args:
        series_glossary: Current series glossary
        source_term: The source term with conflict
        resolution: "book_wins" (use book translation), "series_wins" (keep series), "manual" (use manual_value)
        resolved_by: Who resolved the conflict
        manual_value: Custom value for "manual" resolution

    Returns:
        Updated SeriesGlossary and the resolution record
    """
    now = datetime.now().isoformat(timespec="seconds")

    if source_term not in series_glossary.terms:
        raise SeriesGlossaryValidationError(f"Term not found in series glossary: {source_term}")

    existing = series_glossary.terms[source_term]

    if resolution == "book_wins":
        # This would require knowing the book translation - pass via manual_value
        if manual_value is None:
            raise SeriesGlossaryValidationError("book_wins requires manual_value")
        new_translation = manual_value
        action = "updated"
    elif resolution == "series_wins":
        # Keep existing translation - no change needed
        return series_glossary, GlossaryPromotionRecord(
            promotion_id=hashlib.sha256(f"{series_glossary.series_id}|{source_term}|{now}".encode()).hexdigest()[:12],
            series_id=series_glossary.series_id,
            book_identity="",
            source_term=source_term,
            previous_translation=existing.translation,
            new_translation=existing.translation,
            action="no_op",
            resolved_by=resolved_by,
            resolved_at=now,
            source_status="manual_resolution",
        )
    elif resolution == "manual":
        if manual_value is None:
            raise SeriesGlossaryValidationError("manual resolution requires manual_value")
        new_translation = manual_value
        action = "updated"
    else:
        raise SeriesGlossaryValidationError(f"Invalid resolution: {resolution}")

    if new_translation == existing.translation:
        action = "no_op"

    updated_term = existing.with_updated_translation(new_translation, resolved_by, now)

    updated_terms = dict(series_glossary.terms)
    updated_terms[source_term] = updated_term

    updated_glossary = SeriesGlossary(
        schema_name=series_glossary.schema_name,
        schema_version=series_glossary.schema_version,
        series_id=series_glossary.series_id,
        terms=updated_terms,
        glossary_hash="",
    )

    fingerprint = compute_series_glossary_fingerprint(updated_glossary.to_dict(include_glossary_hash=False))
    updated_glossary = SeriesGlossary(
        schema_name=updated_glossary.schema_name,
        schema_version=updated_glossary.schema_version,
        series_id=updated_glossary.series_id,
        terms=updated_glossary.terms,
        glossary_hash=fingerprint,
    )

    validate_series_glossary(updated_glossary)

    resolution_record = GlossaryPromotionRecord(
        promotion_id=hashlib.sha256(f"{series_glossary.series_id}|{source_term}|{now}".encode()).hexdigest()[:12],
        series_id=series_glossary.series_id,
        book_identity="",
        source_term=source_term,
        previous_translation=existing.translation,
        new_translation=new_translation,
        action=action,
        resolved_by=resolved_by,
        resolved_at=now,
        source_status="manual_resolution",
    )

    return updated_glossary, resolution_record


def main() -> None:
    ensure_dirs()
    log("NTPE Glossary Builder v1.1.1 啟動")

    files = list_glossary_files()
    if not files:
        log("analysis 資料夾內沒有 *_glossary_auto.json")
        log("請先執行 Document Analyzer v1.0")
        return

    log(f"找到 {len(files)} 個術語候選檔")

    override = load_override()
    log(f"讀取手動術語表：{len(override)} 筆")

    merged = merge_glossary(files)
    log(f"自動合併術語候選：{len(merged)} 筆")

    merged = apply_override(merged, override)
    glossary = finalize_glossary(merged)

    character_alias_index = build_character_alias_index(glossary)
    summary = build_summary(glossary, files, character_alias_index)

    save_glossary(glossary, summary)
    save_character_alias_index(character_alias_index)
    save_report(glossary, summary, character_alias_index)
    save_csv(glossary)

    log("術語庫建立完成")
    log(f"術語總數：{summary['term_total']}")
    log(f"已鎖定術語：{summary['locked_count']}")
    log(f"已有譯名：{summary['translated_count']}")
    log(f"角色別名數：{summary['character_alias_count']}")
    log(f"角色別名碰撞數：{summary['character_collision_count']}")
    log(f"輸出：{MEMORY_DIR / 'glossary.json'}")
    log(f"輸出：{MEMORY_DIR / 'character_alias_index.json'}")


if __name__ == "__main__":
    main()
