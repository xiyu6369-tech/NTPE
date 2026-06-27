# =====================================================
# NTPE Knowledge Base Builder v1.0
# 功能：
# 1. 讀取 memory/character_memory.json
# 2. 讀取 memory/glossary.json
# 3. 整合 characters / glossary / aliases / locked terms
# 4. 輸出 memory/knowledge_base.json
# 5. 輸出 knowledge_base_report.txt / knowledge_base_index.csv
# =====================================================

from __future__ import annotations

import csv
import json
from pathlib import Path
from datetime import datetime


ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = ROOT / "memory"
LOG_DIR = ROOT / "logs"

CHARACTER_MEMORY_FILE = MEMORY_DIR / "character_memory.json"
GLOSSARY_FILE = MEMORY_DIR / "glossary.json"

KB_FILE = MEMORY_DIR / "knowledge_base.json"
KB_ONLY_FILE = MEMORY_DIR / "knowledge_base_only.json"
KB_REPORT_FILE = MEMORY_DIR / "knowledge_base_report.txt"
KB_CSV_FILE = MEMORY_DIR / "knowledge_base_index.csv"


def ensure_dirs() -> None:
    for folder in [MEMORY_DIR, LOG_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    ensure_dirs()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line)

    with (LOG_DIR / "knowledge_base_log.txt").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_character_memory() -> tuple[dict, dict]:
    if not CHARACTER_MEMORY_FILE.exists():
        raise FileNotFoundError(f"找不到：{CHARACTER_MEMORY_FILE}")

    data = load_json(CHARACTER_MEMORY_FILE)

    summary = data.get("summary", {})
    characters = data.get("characters", data)

    if not isinstance(characters, dict):
        raise ValueError("character_memory.json 格式錯誤：characters 不是 dict")

    return summary, characters


def load_glossary() -> tuple[dict, dict]:
    if not GLOSSARY_FILE.exists():
        raise FileNotFoundError(f"找不到：{GLOSSARY_FILE}")

    data = load_json(GLOSSARY_FILE)

    summary = data.get("summary", {})
    terms = data.get("terms", data)

    if not isinstance(terms, dict):
        raise ValueError("glossary.json 格式錯誤：terms 不是 dict")

    return summary, terms


def build_alias_index(characters: dict, terms: dict) -> dict:
    aliases = {}

    def add_alias(alias: str, target: str, entry_type: str) -> None:
        alias = str(alias).strip()
        target = str(target).strip()

        if not alias or not target:
            return

        aliases[alias] = {
            "target": target,
            "type": entry_type,
        }

    for source, item in characters.items():
        add_alias(source, source, "character")

        translation = item.get("translation", "")
        if translation:
            add_alias(translation, source, "character_translation")

        for alias in item.get("aliases", []):
            add_alias(alias, source, "character_alias")

    for source, item in terms.items():
        add_alias(source, source, "glossary")

        translation = item.get("translation", "")
        if translation:
            add_alias(translation, source, "glossary_translation")

        for alias in item.get("aliases", []):
            add_alias(alias, source, "glossary_alias")

    return dict(sorted(aliases.items(), key=lambda kv: kv[0].lower()))


def build_locked_index(characters: dict, terms: dict) -> dict:
    locked = {}

    for source, item in characters.items():
        if item.get("locked") and item.get("translation"):
            locked[source] = {
                "type": "character",
                "translation": item.get("translation", ""),
                "source": source,
            }

    for source, item in terms.items():
        if item.get("locked") and item.get("translation"):
            locked[source] = {
                "type": "glossary",
                "translation": item.get("translation", ""),
                "source": source,
            }

    return dict(sorted(locked.items(), key=lambda kv: kv[0].lower()))


def build_prompt_dictionary(locked_index: dict) -> list[dict]:
    """
    給 Translation Engine 直接組 Prompt 用。
    只收 locked + 有 translation 的項目。
    """
    rows = []

    for source, item in locked_index.items():
        rows.append({
            "source": source,
            "translation": item.get("translation", ""),
            "type": item.get("type", ""),
        })

    return sorted(rows, key=lambda x: (x["type"], x["source"]))


def build_summary(
    character_summary: dict,
    glossary_summary: dict,
    characters: dict,
    terms: dict,
    aliases: dict,
    locked_index: dict,
) -> dict:
    character_locked = sum(1 for item in characters.values() if item.get("locked"))
    character_translated = sum(1 for item in characters.values() if item.get("translation"))
    glossary_locked = sum(1 for item in terms.values() if item.get("locked"))
    glossary_translated = sum(1 for item in terms.values() if item.get("translation"))

    return {
        "ntpe_module": "Knowledge Base Builder",
        "version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "inputs": {
            "character_memory": str(CHARACTER_MEMORY_FILE),
            "glossary": str(GLOSSARY_FILE),
        },
        "source_summaries": {
            "character_memory": character_summary,
            "glossary": glossary_summary,
        },
        "counts": {
            "characters": len(characters),
            "glossary_terms": len(terms),
            "aliases": len(aliases),
            "locked_entries": len(locked_index),
            "character_locked": character_locked,
            "character_translated": character_translated,
            "glossary_locked": glossary_locked,
            "glossary_translated": glossary_translated,
        },
    }


def build_knowledge_base() -> dict:
    character_summary, characters = load_character_memory()
    glossary_summary, terms = load_glossary()

    aliases = build_alias_index(characters, terms)
    locked_index = build_locked_index(characters, terms)
    prompt_dictionary = build_prompt_dictionary(locked_index)

    summary = build_summary(
        character_summary,
        glossary_summary,
        characters,
        terms,
        aliases,
        locked_index,
    )

    return {
        "summary": summary,
        "characters": characters,
        "glossary": terms,
        "aliases": aliases,
        "locked_index": locked_index,
        "prompt_dictionary": prompt_dictionary,
    }


def save_report(kb: dict) -> None:
    s = kb["summary"]
    counts = s["counts"]

    lines = []
    lines.append("====================================")
    lines.append("NTPE Knowledge Base Builder v1.0")
    lines.append("====================================")
    lines.append("")
    lines.append(f"產生時間：{s['generated_at']}")
    lines.append("")
    lines.append("【統計】")
    lines.append(f"角色數：{counts['characters']}")
    lines.append(f"術語數：{counts['glossary_terms']}")
    lines.append(f"別名索引數：{counts['aliases']}")
    lines.append(f"鎖定項目數：{counts['locked_entries']}")
    lines.append(f"角色已鎖定：{counts['character_locked']}")
    lines.append(f"角色已有譯名：{counts['character_translated']}")
    lines.append(f"術語已鎖定：{counts['glossary_locked']}")
    lines.append(f"術語已有譯名：{counts['glossary_translated']}")
    lines.append("")
    lines.append("【鎖定項目】")

    for source, item in kb["locked_index"].items():
        lines.append(
            f"- [{item.get('type', '')}] {source} -> {item.get('translation', '')}"
        )

    lines.append("")
    lines.append("【Prompt Dictionary】")
    for row in kb["prompt_dictionary"][:200]:
        lines.append(f"- [{row['type']}] {row['source']} = {row['translation']}")

    if len(kb["prompt_dictionary"]) > 200:
        lines.append(f"... 其餘 {len(kb['prompt_dictionary']) - 200} 筆省略，完整資料請看 JSON")

    lines.append("")
    lines.append("====================================")
    lines.append("完成")
    lines.append("====================================")
    lines.append("")

    KB_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def save_csv(kb: dict) -> None:
    with KB_CSV_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "type",
            "source",
            "translation",
            "locked",
            "total_count",
            "book_count",
            "category",
            "status",
        ])

        for source, item in kb["characters"].items():
            writer.writerow([
                "character",
                source,
                item.get("translation", ""),
                item.get("locked", False),
                item.get("total_count", 0),
                item.get("book_count", 0),
                "",
                item.get("status", ""),
            ])

        for source, item in kb["glossary"].items():
            writer.writerow([
                "glossary",
                source,
                item.get("translation", ""),
                item.get("locked", False),
                item.get("total_count", 0),
                item.get("book_count", 0),
                item.get("category", ""),
                item.get("status", ""),
            ])


def main() -> None:
    ensure_dirs()

    log("NTPE Knowledge Base Builder v1.0 啟動")

    try:
        kb = build_knowledge_base()
    except Exception as e:
        log(f"建立失敗：{e}")
        return

    save_json(KB_FILE, kb)

    kb_only = {
        "characters": kb["characters"],
        "glossary": kb["glossary"],
        "aliases": kb["aliases"],
        "locked_index": kb["locked_index"],
        "prompt_dictionary": kb["prompt_dictionary"],
    }
    save_json(KB_ONLY_FILE, kb_only)

    save_report(kb)
    save_csv(kb)

    counts = kb["summary"]["counts"]

    log("知識庫建立完成")
    log(f"角色數：{counts['characters']}")
    log(f"術語數：{counts['glossary_terms']}")
    log(f"別名索引數：{counts['aliases']}")
    log(f"鎖定項目數：{counts['locked_entries']}")
    log(f"輸出：{KB_FILE}")


if __name__ == "__main__":
    main()
