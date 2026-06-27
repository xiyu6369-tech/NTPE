# =====================================================
# NTPE Character Memory Engine v1.0
# 功能：
# 1. 讀取 analysis/*_character_memory_auto.json
# 2. 合併所有卷數的人物候選
# 3. 統計總出現次數、出現卷數
# 4. 套用 character_override.json 手動鎖名表
# 5. 輸出 memory/character_memory.json
# 6. 輸出 report 與 csv
# =====================================================

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict


ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = ROOT / "analysis"
MEMORY_DIR = ROOT / "memory"
LOG_DIR = ROOT / "logs"
OVERRIDE_FILE = ROOT / "character_override.json"

MIN_TOTAL_COUNT = 3


def ensure_dirs() -> None:
    for folder in [ANALYSIS_DIR, MEMORY_DIR, LOG_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    ensure_dirs()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line)

    log_file = LOG_DIR / "character_memory_log.txt"
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

    name = name.replace("_character_memory_auto", "")
    name = name.replace("_normalized", "")

    return name


def list_memory_files() -> list[Path]:
    ensure_dirs()

    return sorted(
        ANALYSIS_DIR.glob("*_character_memory_auto.json"),
        key=lambda p: p.name.lower(),
    )


def load_override() -> dict:
    if not OVERRIDE_FILE.exists():
        log("未找到 character_override.json，將只使用自動候選")
        return {}

    try:
        data = load_json(OVERRIDE_FILE)
        if not isinstance(data, dict):
            log("character_override.json 格式不是 dict，已忽略")
            return {}
        return data
    except Exception as e:
        log(f"character_override.json 讀取失敗，已忽略：{e}")
        return {}


def normalize_source_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    return name


def merge_memory(files: list[Path]) -> dict:
    merged = {}

    for path in files:
        book = infer_book_name(path)
        data = load_json(path)

        if not isinstance(data, dict):
            log(f"跳過格式異常：{path.name}")
            continue

        for source_name, item in data.items():
            source_name = normalize_source_name(source_name)

            if not source_name:
                continue

            count = 0

            if isinstance(item, dict):
                count = int(item.get("count", 0) or 0)
            elif isinstance(item, int):
                count = item

            if count <= 0:
                continue

            if source_name not in merged:
                merged[source_name] = {
                    "source": source_name,
                    "translation": "",
                    "total_count": 0,
                    "books": {},
                    "book_count": 0,
                    "locked": False,
                    "status": "auto",
                    "aliases": [],
                    "notes": [],
                    "created_by": "NTPE Character Memory Engine v1.0",
                }

            merged[source_name]["total_count"] += count
            merged[source_name]["books"][book] = merged[source_name]["books"].get(book, 0) + count

    for source_name, item in merged.items():
        item["book_count"] = len(item["books"])

    return merged


def apply_override(merged: dict, override: dict) -> dict:
    for source_name, ov in override.items():
        source_name = normalize_source_name(source_name)

        if not source_name:
            continue

        if source_name not in merged:
            merged[source_name] = {
                "source": source_name,
                "translation": "",
                "total_count": 0,
                "books": {},
                "book_count": 0,
                "locked": False,
                "status": "manual_only",
                "aliases": [],
                "notes": [],
                "created_by": "NTPE Character Memory Engine v1.0",
            }

        if isinstance(ov, str):
            merged[source_name]["translation"] = ov
            merged[source_name]["locked"] = True
            merged[source_name]["status"] = "manual_locked"
            merged[source_name]["notes"].append("manual override string")
            continue

        if isinstance(ov, dict):
            translation = ov.get("translation", "")
            locked = ov.get("locked", True)
            note = ov.get("note", "manual override")
            aliases = ov.get("aliases", [])

            if translation:
                merged[source_name]["translation"] = translation

            merged[source_name]["locked"] = bool(locked)

            if merged[source_name]["locked"]:
                merged[source_name]["status"] = "manual_locked"
            else:
                merged[source_name]["status"] = "manual_unlocked"

            if note:
                merged[source_name]["notes"].append(str(note))

            if isinstance(aliases, list):
                for alias in aliases:
                    alias = str(alias).strip()
                    if alias and alias not in merged[source_name]["aliases"]:
                        merged[source_name]["aliases"].append(alias)

    return merged


def filter_and_sort_memory(merged: dict) -> dict:
    filtered = {}

    for source_name, item in merged.items():
        if item["total_count"] >= MIN_TOTAL_COUNT or item["locked"]:
            filtered[source_name] = item

    sorted_items = sorted(
        filtered.items(),
        key=lambda kv: (
            not kv[1]["locked"],
            -kv[1]["book_count"],
            -kv[1]["total_count"],
            kv[0],
        ),
    )

    return dict(sorted_items)


def build_summary(memory: dict, source_files: list[Path]) -> dict:
    locked_count = sum(1 for item in memory.values() if item.get("locked"))
    translated_count = sum(1 for item in memory.values() if item.get("translation"))
    auto_count = sum(1 for item in memory.values() if item.get("status") == "auto")

    return {
        "ntpe_module": "Character Memory Engine",
        "version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_file_count": len(source_files),
        "source_files": [p.name for p in source_files],
        "character_total": len(memory),
        "locked_count": locked_count,
        "translated_count": translated_count,
        "auto_count": auto_count,
    }


def save_memory(memory: dict, summary: dict) -> None:
    output = {
        "summary": summary,
        "characters": memory,
    }

    save_json(MEMORY_DIR / "character_memory.json", output)
    save_json(MEMORY_DIR / "character_memory_only.json", memory)


def save_report(memory: dict, summary: dict) -> None:
    lines = []
    lines.append("====================================")
    lines.append("NTPE Character Memory Engine v1.0")
    lines.append("====================================")
    lines.append("")
    lines.append(f"產生時間：{summary['generated_at']}")
    lines.append(f"來源檔案數：{summary['source_file_count']}")
    lines.append(f"角色總數：{summary['character_total']}")
    lines.append(f"已鎖定譯名：{summary['locked_count']}")
    lines.append(f"已有譯名：{summary['translated_count']}")
    lines.append("")
    lines.append("【來源檔案】")
    for name in summary["source_files"]:
        lines.append(f"- {name}")
    lines.append("")
    lines.append("【鎖定角色】")
    locked = [
        (name, item) for name, item in memory.items()
        if item.get("locked")
    ]
    for name, item in locked:
        lines.append(
            f"- {name} -> {item.get('translation', '')} "
            f"(總次數：{item.get('total_count', 0)}，卷數：{item.get('book_count', 0)})"
        )
    lines.append("")
    lines.append("【自動候選 TOP 80】")
    auto_items = [
        (name, item) for name, item in memory.items()
        if not item.get("locked")
    ]
    auto_items = sorted(
        auto_items,
        key=lambda kv: (-kv[1].get("book_count", 0), -kv[1].get("total_count", 0), kv[0]),
    )
    for name, item in auto_items[:80]:
        lines.append(
            f"- {name} "
            f"(總次數：{item.get('total_count', 0)}，卷數：{item.get('book_count', 0)})"
        )

    lines.append("")
    lines.append("====================================")
    lines.append("完成")
    lines.append("====================================")
    lines.append("")

    (MEMORY_DIR / "character_memory_report.txt").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def save_csv(memory: dict) -> None:
    path = MEMORY_DIR / "character_memory.csv"

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "source",
            "translation",
            "total_count",
            "book_count",
            "locked",
            "status",
            "books",
            "aliases",
            "notes",
        ])

        for source, item in memory.items():
            books = "; ".join(
                f"{book}:{count}"
                for book, count in sorted(item.get("books", {}).items())
            )
            aliases = "; ".join(item.get("aliases", []))
            notes = "; ".join(item.get("notes", []))

            writer.writerow([
                source,
                item.get("translation", ""),
                item.get("total_count", 0),
                item.get("book_count", 0),
                item.get("locked", False),
                item.get("status", ""),
                books,
                aliases,
                notes,
            ])


def main() -> None:
    ensure_dirs()

    log("NTPE Character Memory Engine v1.0 啟動")

    files = list_memory_files()

    if not files:
        log("analysis 資料夾內沒有 *_character_memory_auto.json")
        log("請先執行 Document Analyzer v1.0")
        return

    log(f"找到 {len(files)} 個角色候選檔")

    override = load_override()
    log(f"讀取手動鎖名：{len(override)} 筆")

    merged = merge_memory(files)
    log(f"自動合併候選：{len(merged)} 筆")

    merged = apply_override(merged, override)
    memory = filter_and_sort_memory(merged)
    summary = build_summary(memory, files)

    save_memory(memory, summary)
    save_report(memory, summary)
    save_csv(memory)

    log("角色記憶庫建立完成")
    log(f"角色總數：{summary['character_total']}")
    log(f"已鎖定譯名：{summary['locked_count']}")
    log(f"已有譯名：{summary['translated_count']}")
    log(f"輸出：{MEMORY_DIR / 'character_memory.json'}")


if __name__ == "__main__":
    main()
