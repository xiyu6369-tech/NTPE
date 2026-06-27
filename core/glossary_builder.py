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
import json
import re
from pathlib import Path
from datetime import datetime

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
    resolver.load_from_glossary_terms(glossary)
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
