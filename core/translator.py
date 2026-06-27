from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import chardet

try:
    from opencc import OpenCC
except Exception:
    OpenCC = None

from engine.nvidia import NvidiaEngine
from core.chunker import split_chunks
from core.formatter import format_chunk, format_document
from core.prompt_engine import PromptEngine
from core.rules import (
    apply_postprocess,
    enforce_glossary_output,
    load_glossary,
    validate_translation,
)

ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "input"
OUTPUT_DIR = ROOT / "output"
CACHE_DIR = ROOT / "cache"
CONFIG_DIR = ROOT / "config"
PROGRESS_FILE = CACHE_DIR / "progress.json"


def load_config() -> dict:
    default_path = CONFIG_DIR / "default_config.json"
    local_path = CONFIG_DIR / "config.json"

    config = {}
    if default_path.exists():
        with open(default_path, "r", encoding="utf-8") as f:
            config.update(json.load(f))
    if local_path.exists():
        with open(local_path, "r", encoding="utf-8") as f:
            config.update(json.load(f))

    # Sprint 1: smaller semantic chunks reduce summarization and hallucination.
    config.setdefault("chunk_size", 1100)
    config.setdefault("context_size", 650)
    config.setdefault("max_retry", 4)
    config.setdefault("opencc", True)
    config.setdefault("timeout", 180)
    config.setdefault("retry_wait_base", 8)
    return config


def read_text_auto(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr", "big5", "gb18030"]:
        try:
            return raw.decode(enc)
        except Exception:
            continue
    detected = chardet.detect(raw)
    encoding = detected.get("encoding") or "utf-8"
    return raw.decode(encoding, errors="replace")


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_progress(progress: dict) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def normalize_output(text: str, source: str, glossary: Dict[str, str], cc) -> str:
    if cc:
        text = cc.convert(text)
    text = enforce_glossary_output(source, text, glossary)
    text = apply_postprocess(text)
    text = format_chunk(text, source=source)
    return text.strip()


def translate_chunk(
    chunk: str,
    context: str,
    engine: NvidiaEngine,
    prompt_engine: PromptEngine,
    glossary: Dict[str, str],
    config: dict,
    cc,
) -> Tuple[str, str]:
    last_error = None
    max_retry = config.get("max_retry", 4)

    for attempt in range(max_retry):
        try:
            prompt = prompt_engine.build_translate_prompt(
                text=chunk,
                context=context,
                glossary=glossary,
            )
            candidate = engine.translate(prompt)
            candidate = normalize_output(candidate, chunk, glossary, cc)

            ok, reason = validate_translation(chunk, candidate, glossary)
            if not ok:
                raise RuntimeError(reason)

            return candidate, "OK"

        except Exception as exc:
            last_error = exc
            wait = min(config.get("retry_wait_base", 8) * (attempt + 1), 40)
            print(f"⚠️ 第 {attempt + 1} 次失敗：{exc}")
            print(f"⏳ 等待 {wait} 秒後重試")
            time.sleep(wait)

    raise RuntimeError(f"區塊翻譯失敗：{last_error}")


def translate_file(path: Path, engine: NvidiaEngine, config: dict) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)

    output_path = OUTPUT_DIR / f"{path.stem}_zh.txt"
    source_text = read_text_auto(path)
    chunks = split_chunks(source_text, config.get("chunk_size", 1100))
    glossary = load_glossary()
    prompt_engine = PromptEngine()

    progress = load_progress()
    file_key = path.name
    done_count = progress.get(file_key, 0)

    translated_parts: List[str] = []
    if output_path.exists():
        existing = output_path.read_text(encoding="utf-8").strip()
        if existing:
            translated_parts.append(existing)

    cc = OpenCC("s2twp") if config.get("opencc", True) and OpenCC else None

    print(f"\n📘 開始：{path.name}")
    print(f"📦 共 {len(chunks)} 區塊，從第 {done_count + 1} 區塊開始")

    context = ""
    if translated_parts:
        context = translated_parts[-1][-config.get("context_size", 650):]

    for index, chunk in enumerate(chunks):
        if index < done_count:
            continue

        print(f"🔄 翻譯區塊 {index + 1}/{len(chunks)}")
        result, _ = translate_chunk(
            chunk=chunk,
            context=context,
            engine=engine,
            prompt_engine=prompt_engine,
            glossary=glossary,
            config=config,
            cc=cc,
        )

        translated_parts.append(result)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(format_document(translated_parts))

        progress[file_key] = index + 1
        save_progress(progress)
        context = result[-config.get("context_size", 650):]
        time.sleep(2)

    print(f"✅ 完成：{output_path.name}")


def run_translation() -> None:
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)

    config = load_config()
    if not config.get("api_key"):
        print("❌ 尚未設定 NVIDIA API Key")
        print("請建立或修改：config/config.json")
        return

    engine = NvidiaEngine(config)
    files = sorted(INPUT_DIR.glob("*.txt"))

    if not files:
        print("⚠️ input 資料夾沒有 TXT 檔案")
        return

    print(f"📚 偵測到 {len(files)} 個 TXT 檔案")
    for file in files:
        try:
            translate_file(file, engine, config)
        except Exception as exc:
            print(f"❌ 失敗：{file.name}")
            print(exc)

    print("\n🎉 全部處理完成")
