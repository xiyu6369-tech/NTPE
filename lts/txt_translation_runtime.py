from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.translation_engine import TranslationEngine
from core.translation_engine.utils import now_iso, save_json, save_text


DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"
DEFAULT_CHUNK_SIZE = 1800
DEFAULT_OUTPUT_SUFFIX = "_zh"
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_SECONDS = 5.0
DEFAULT_CHARACTER_MEMORY = "memory/character_memory_lts.json"
RETRYABLE_ERROR_PATTERNS = (
    "503",
    "429",
    "resourceexhausted",
    "rate limit",
    "too many requests",
    "service unavailable",
    "timeout",
    "temporarily unavailable",
)


@dataclass(frozen=True)
class TxtTranslationOptions:
    input_path: Path
    output_dir: Path
    chunk_size: int = DEFAULT_CHUNK_SIZE
    model: str = DEFAULT_MODEL
    project_name: str = "NTPE Novel Translation"
    source_language: str = "ko"
    target_language: str = "zh-TW"
    resume: bool = True
    dry_run: bool = False
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_base_seconds: float = DEFAULT_RETRY_BASE_SECONDS
    glossary_path: Path | None = None
    character_memory_path: Path | None = None
    strict_lock_terms: bool = True


def read_text_auto(path: str | Path) -> str:
    path = Path(path)
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr", "big5", "cp950"):
        try:
            text = raw.decode(enc)
            return normalize_text(text)
        except UnicodeDecodeError:
            continue
    return normalize_text(raw.decode("utf-8", errors="replace"))


def normalize_text(text: str) -> str:
    text = text.replace("\ufeff", "").replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip() + "\n" if text.strip() else ""


def split_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    if chunk_size < 300:
        raise ValueError("chunk_size must be >= 300")

    paragraphs = re.split(r"(\n{2,})", text)
    blocks: list[str] = []
    current = ""

    for item in paragraphs:
        if not item:
            continue
        candidate = current + item
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current.strip():
            blocks.extend(_split_oversized(current, chunk_size))
        current = item

    if current.strip():
        blocks.extend(_split_oversized(current, chunk_size))

    return [b.strip() + "\n" for b in blocks if b.strip()]


def _split_oversized(text: str, chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind("。"), window.rfind("！"), window.rfind("？"), window.rfind("."), window.rfind("\n"))
            if cut > chunk_size * 0.45:
                end = start + cut + 1
        pieces.append(text[start:end])
        start = end
    return pieces


def load_glossary_text(path: str | Path) -> dict[str, str]:
    path = Path(path)
    if not path.exists():
        return {}
    pairs: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        delimiter = "=" if "=" in line else "->" if "->" in line else "→" if "→" in line else None
        if delimiter is None:
            continue
        src, target = line.split(delimiter, 1)
        src = src.strip().strip("- ").strip()
        target = target.strip()
        if src and target:
            pairs[src] = target
    return pairs


def load_json_pairs(path: str | Path) -> dict[str, str]:
    path = Path(path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return _extract_pairs(data)


def load_locked_dictionary(root: Path, options: TxtTranslationOptions | None = None) -> dict[str, str]:
    locked: dict[str, str] = {}
    for path in (root / "character_override.json", root / "glossary_override.json"):
        locked.update(load_json_pairs(path))

    locked.update(load_glossary_text(root / "glossary.txt"))

    if options and options.glossary_path:
        custom_glossary = options.glossary_path if options.glossary_path.is_absolute() else root / options.glossary_path
        locked.update(load_glossary_text(custom_glossary))
        locked.update(load_json_pairs(custom_glossary))

    memory_path = resolve_character_memory_path(root, options)
    if memory_path:
        locked.update(load_json_pairs(memory_path))
    return locked


def resolve_character_memory_path(root: Path, options: TxtTranslationOptions | None = None) -> Path:
    if options and options.character_memory_path:
        return options.character_memory_path if options.character_memory_path.is_absolute() else root / options.character_memory_path
    return root / DEFAULT_CHARACTER_MEMORY


def apply_locked_dictionary(text: str, locked_dictionary: dict[str, str]) -> str:
    result = text
    for source, target in sorted(locked_dictionary.items(), key=lambda item: len(item[0]), reverse=True):
        if not source or not target:
            continue
        # Remove accidental Korean/source residue and normalize any exact source term that survived provider output.
        result = result.replace(source, target)
    return result


def collect_matched_locked_terms(chunks: list[str], locked_dictionary: dict[str, str]) -> dict[str, str]:
    source_text = "\n".join(chunks)
    return {src: target for src, target in locked_dictionary.items() if src and src in source_text}


def update_character_memory(path: str | Path, matched_terms: dict[str, str]) -> None:
    if not matched_terms:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_json_pairs(path)
    existing.update(matched_terms)
    payload = {
        "version": "1.1-lts-stage-03",
        "updated_at": now_iso(),
        "characters": existing,
    }
    save_json(path, payload)



def get_resume_state_path(output_dir: Path, input_path: Path) -> Path:
    return output_dir / f"{input_path.stem}_resume_state.json"


def load_resume_state(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        return {"version": "1.1-lts-stage-03", "chunks": {}, "events": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"version": "1.1-lts-stage-03", "chunks": {}, "events": []}
    if not isinstance(data, dict):
        return {"version": "1.1-lts-stage-03", "chunks": {}, "events": []}
    data.setdefault("version", "1.1-lts-stage-03")
    data.setdefault("chunks", {})
    data.setdefault("events", [])
    return data


def save_resume_state(path: str | Path, state: dict) -> None:
    save_json(path, state)


def is_retryable_error(error: str) -> bool:
    lowered = str(error or "").lower()
    return any(pattern in lowered for pattern in RETRYABLE_ERROR_PATTERNS)


def retry_delay_seconds(attempt: int, base_seconds: float) -> float:
    return max(0.0, float(base_seconds)) * (2 ** max(0, attempt - 1))


def translate_package_with_retry(engine: TranslationEngine, package: dict, package_path: Path, options: TxtTranslationOptions) -> dict:
    attempts = max(1, int(options.max_retries) + 1)
    last_result: dict = {"status": "failed", "error": "translation was not attempted"}
    for attempt in range(1, attempts + 1):
        result = engine.translate_package(package, package_path=package_path)
        result["attempt"] = attempt
        last_result = result
        if result.get("status") == "success":
            return result
        error = result.get("error", "")
        if attempt >= attempts or not is_retryable_error(error):
            return result
        delay = retry_delay_seconds(attempt, options.retry_base_seconds)
        if delay > 0:
            time.sleep(delay)
    return last_result

def _extract_pairs(data) -> dict[str, str]:
    pairs: dict[str, str] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and isinstance(key, str):
                pairs[key] = value
            elif isinstance(value, dict):
                source = value.get("source") or value.get("ko") or value.get("korean") or key
                target = value.get("target") or value.get("zh") or value.get("traditional") or value.get("name")
                if isinstance(source, str) and isinstance(target, str):
                    pairs[source] = target
                pairs.update(_extract_pairs(value))
            elif isinstance(value, list):
                for item in value:
                    pairs.update(_extract_pairs(item))
    elif isinstance(data, list):
        for item in data:
            pairs.update(_extract_pairs(item))
    return pairs


def build_prompt_package(
    *,
    options: TxtTranslationOptions,
    chunk_text: str,
    chunk_index: int,
    chunk_total: int,
    locked_dictionary: dict[str, str],
) -> dict:
    input_name = options.input_path.name
    package_id = f"TXT_{options.input_path.stem}_{chunk_index:06d}"
    source_hash = hashlib.sha1(chunk_text.encode("utf-8")).hexdigest()
    matched = {src: target for src, target in locked_dictionary.items() if src and src in chunk_text}

    locked_lines = "\n".join(f"- {src} → {target}" for src, target in matched.items()) or "- 無"
    system_prompt = (
        "你是 NTPE 的專業小說翻譯引擎。請將原文完整翻譯成自然流暢的台灣繁體中文。"
        "只輸出譯文，不要加解釋、標題或 Markdown。"
    )
    user_prompt = f"""【翻譯規則】
- 翻譯為自然流暢的台灣繁體中文。
- 保留原文劇情、段落與敘事順序。
- 不可刪減、不可摘要、不可自行補劇情。
- 對話使用「」。
- 人名與術語必須遵守鎖定譯名。
- 不可留下大量韓文原文。

【本段鎖定譯名】
{locked_lines}

【待翻譯內容】
{chunk_text}"""

    return {
        "package_id": package_id,
        "project": {
            "project_name": options.project_name,
            "source_language": options.source_language,
            "target_language": options.target_language,
        },
        "session": {
            "session_id": f"TXT_{options.input_path.stem}",
            "file_name": input_name,
            "chunk_index": chunk_index,
            "chunk_total": chunk_total,
            "resume_key": f"{input_name}:chunk:{chunk_index:06d}",
        },
        "model_profile": {
            "engine": "NVIDIA",
            "model": options.model,
            "context_window": 131072,
            "temperature": 0.15,
            "top_p": 0.85,
            "max_output_tokens": max(1000, min(6000, math.ceil(len(chunk_text) * 1.8))),
        },
        "source": {
            "chunk_text": chunk_text,
            "source_hash": source_hash,
            "char_count": len(chunk_text),
        },
        "context": {
            "previous_summary": "",
            "previous_chunk_tail": "",
            "recent_characters": [],
            "recent_terms": [],
        },
        "knowledge": {
            "locked_dictionary": matched,
        },
        "prompt": {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "prompt_mode": "translate_txt",
        },
        "qa_requirements": {
            "check_korean_residue": True,
            "check_name_rules": True,
            "check_glossary": True,
            "check_repetition": True,
            "check_length_ratio": True,
        },
        "metadata": {
            "created_at": now_iso(),
            "created_by": "NTPE 1.1 LTS Stage-03 TXT Translation Entry",
            "package_version": "1.1-lts-stage-03",
        },
    }


def translate_txt(options: TxtTranslationOptions, root: str | Path | None = None) -> dict:
    root_path = Path(root) if root else Path(__file__).resolve().parents[1]
    input_path = options.input_path if options.input_path.is_absolute() else root_path / options.input_path
    output_dir = options.output_dir if options.output_dir.is_absolute() else root_path / options.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    text = read_text_auto(input_path)
    chunks = split_text(text, options.chunk_size)
    if not chunks:
        raise ValueError(f"輸入檔案沒有可翻譯內容：{input_path}")

    stage_dir = root_path / "prompt_packages" / "txt_runtime"
    stage_dir.mkdir(parents=True, exist_ok=True)
    chunk_out_dir = output_dir / f"{input_path.stem}_chunks"
    chunk_out_dir.mkdir(parents=True, exist_ok=True)

    locked_dictionary = load_locked_dictionary(root_path, options)
    character_memory_path = resolve_character_memory_path(root_path, options)
    matched_terms_for_memory = collect_matched_locked_terms(chunks, locked_dictionary)
    engine = TranslationEngine(root=root_path)
    translated_chunks: list[str] = []
    records: list[dict] = []
    resume_state_path = get_resume_state_path(output_dir, input_path)
    resume_state = load_resume_state(resume_state_path)
    resume_state["input"] = str(input_path)
    resume_state["output_dir"] = str(output_dir)
    resume_state["chunk_total"] = len(chunks)
    resume_state["updated_at"] = now_iso()
    save_resume_state(resume_state_path, resume_state)

    for idx, chunk in enumerate(chunks, start=1):
        package = build_prompt_package(
            options=options,
            chunk_text=chunk,
            chunk_index=idx,
            chunk_total=len(chunks),
            locked_dictionary=locked_dictionary,
        )
        package_path = stage_dir / f"{input_path.stem}_chunk_{idx:06d}.json"
        save_json(package_path, package)

        chunk_file = chunk_out_dir / f"{input_path.stem}_chunk_{idx:06d}_zh.txt"
        chunk_key = f"{idx:06d}"
        source_hash = package["source"]["source_hash"]
        state_entry = resume_state["chunks"].get(chunk_key, {})
        reusable_state = (
            options.resume
            and state_entry.get("status") == "success"
            and state_entry.get("source_hash") == source_hash
            and chunk_file.exists()
            and chunk_file.read_text(encoding="utf-8").strip()
        )

        if reusable_state:
            translation = chunk_file.read_text(encoding="utf-8")
            if options.strict_lock_terms:
                translation = apply_locked_dictionary(translation, locked_dictionary)
            result = {"status": "skipped", "output_path": str(chunk_file), "package_id": package["package_id"], "attempt": 0}
        elif options.dry_run:
            translation = ""
            result = {"status": "dry_run", "output_path": str(chunk_file), "package_id": package["package_id"], "attempt": 0}
            resume_state["chunks"][chunk_key] = {
                "status": "dry_run",
                "source_hash": source_hash,
                "output_path": str(chunk_file),
                "updated_at": now_iso(),
            }
            save_resume_state(resume_state_path, resume_state)
        else:
            result = translate_package_with_retry(engine, package, package_path, options)
            if result.get("status") != "success":
                resume_state["chunks"][chunk_key] = {
                    "status": "failed",
                    "source_hash": source_hash,
                    "error": result.get("error", "unknown error"),
                    "attempt": result.get("attempt", 1),
                    "updated_at": now_iso(),
                }
                resume_state["events"].append({
                    "event": "chunk_failed",
                    "chunk_index": idx,
                    "error": result.get("error", "unknown error"),
                    "at": now_iso(),
                })
                save_resume_state(resume_state_path, resume_state)
                return {
                    "status": "failed",
                    "input": str(input_path),
                    "failed_chunk": idx,
                    "error": result.get("error", "unknown error"),
                    "records": records,
                    "resume_state": str(resume_state_path),
                }
            generated_path = Path(result["output_path"])
            translation = generated_path.read_text(encoding="utf-8")
            if options.strict_lock_terms:
                translation = apply_locked_dictionary(translation, locked_dictionary)
            save_text(chunk_file, translation)
            resume_state["chunks"][chunk_key] = {
                "status": "success",
                "source_hash": source_hash,
                "output_path": str(chunk_file),
                "attempt": result.get("attempt", 1),
                "updated_at": now_iso(),
            }
            save_resume_state(resume_state_path, resume_state)

        if translation:
            translated_chunks.append(translation.strip())
        records.append(result | {"chunk_index": idx, "chunk_total": len(chunks)})

    final_output = output_dir / f"{input_path.stem}{DEFAULT_OUTPUT_SUFFIX}.txt"
    if not options.dry_run:
        final_text = "\n\n".join(translated_chunks).strip() + "\n"
        if options.strict_lock_terms:
            final_text = apply_locked_dictionary(final_text, locked_dictionary)
        save_text(final_output, final_text)
        update_character_memory(character_memory_path, matched_terms_for_memory)

    manifest = {
        "status": "success",
        "input": str(input_path),
        "output": str(final_output),
        "chunk_total": len(chunks),
        "chunk_size": options.chunk_size,
        "model": options.model,
        "resume": options.resume,
        "resume_state": str(resume_state_path),
        "retry": {"max_retries": options.max_retries, "base_seconds": options.retry_base_seconds},
        "glossary": {"locked_terms": len(locked_dictionary), "matched_terms": len(matched_terms_for_memory), "strict_lock_terms": options.strict_lock_terms},
        "character_memory": str(character_memory_path),
        "dry_run": options.dry_run,
        "completed_at": now_iso(),
        "records": records,
    }
    save_json(output_dir / f"{input_path.stem}_translation_manifest.json", manifest)
    return manifest


def parse_args(argv: Iterable[str] | None = None) -> TxtTranslationOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS Stage-02 TXT novel translation entry")
    parser.add_argument("input", help="input TXT file path")
    parser.add_argument("output", nargs="?", default="output", help="output directory")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--project-name", default="NTPE Novel Translation")
    parser.add_argument("--no-resume", action="store_true", help="disable chunk resume")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES, help="retry count for retryable provider errors")
    parser.add_argument("--retry-base-seconds", type=float, default=DEFAULT_RETRY_BASE_SECONDS, help="base seconds for exponential retry backoff")
    parser.add_argument("--glossary", dest="glossary_path", default=None, help="optional glossary file, supports source=target or source->target")
    parser.add_argument("--character-memory", dest="character_memory_path", default=None, help="optional character memory JSON path")
    parser.add_argument("--no-strict-lock-terms", action="store_true", help="disable output source-term normalization")
    parser.add_argument("--dry-run", action="store_true", help="build prompt packages without calling provider")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return TxtTranslationOptions(
        input_path=Path(ns.input),
        output_dir=Path(ns.output),
        chunk_size=ns.chunk_size,
        model=ns.model,
        project_name=ns.project_name,
        resume=not ns.no_resume,
        dry_run=ns.dry_run,
        max_retries=max(0, ns.max_retries),
        retry_base_seconds=max(0.0, ns.retry_base_seconds),
        glossary_path=Path(ns.glossary_path) if ns.glossary_path else None,
        character_memory_path=Path(ns.character_memory_path) if ns.character_memory_path else None,
        strict_lock_terms=not ns.no_strict_lock_terms,
    )


def main(argv: Iterable[str] | None = None) -> int:
    try:
        options = parse_args(argv)
        result = translate_txt(options)
        print("NTPE 1.1 LTS TXT Translation Entry")
        print("===================================")
        print(f"status: {result['status']}")
        print(f"input: {result.get('input', '')}")
        print(f"output: {result.get('output', '')}")
        print(f"chunks: {result.get('chunk_total', 0)}")
        print(f"resume_state: {result.get('resume_state', '')}")
        return 0 if result.get("status") == "success" else 1
    except Exception as exc:
        print("NTPE 1.1 LTS TXT Translation Entry")
        print("===================================")
        print("status: failed")
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
