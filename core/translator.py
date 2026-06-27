import json
import re
import time
from pathlib import Path

import chardet

try:
    from opencc import OpenCC
except Exception:
    OpenCC = None

from engine.nvidia import NvidiaEngine
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


def load_config():
    default_path = CONFIG_DIR / "default_config.json"
    local_path = CONFIG_DIR / "config.json"

    config = {}
    if default_path.exists():
        with open(default_path, "r", encoding="utf-8") as f:
            config.update(json.load(f))
    if local_path.exists():
        with open(local_path, "r", encoding="utf-8") as f:
            config.update(json.load(f))

    config.setdefault("chunk_size", 1800)
    config.setdefault("context_size", 700)
    config.setdefault("max_retry", 4)
    config.setdefault("opencc", True)
    config.setdefault("timeout", 180)
    config.setdefault("self_check", True)
    config.setdefault("profile", "PASSION")
    return config


def read_text_auto(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr", "big5", "gb18030"]:
        try:
            return raw.decode(enc)
        except Exception:
            pass
    detected = chardet.detect(raw)
    encoding = detected.get("encoding") or "utf-8"
    return raw.decode(encoding, errors="replace")


def split_chunks(text: str, size: int = 1800):
    """Safe paragraph chunker. Smart Chunk will replace this later."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = re.split(r"(\n\s*\n)", text)
    chunks = []
    current = ""

    for part in paragraphs:
        if not part:
            continue
        if len(current) + len(part) <= size:
            current += part
            continue
        if current.strip():
            chunks.append(current.strip())
            current = ""
        if len(part) <= size:
            current = part
        else:
            sentences = re.split(r"(?<=[.!?。！？다])\s+", part)
            buf = ""
            for s in sentences:
                if len(buf) + len(s) <= size:
                    buf += (" " if buf else "") + s
                else:
                    if buf.strip():
                        chunks.append(buf.strip())
                    buf = s
            current = buf

    if current.strip():
        chunks.append(current.strip())
    return chunks


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_progress(progress):
    CACHE_DIR.mkdir(exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def normalize_output(text: str, src: str, glossary: dict, cc):
    if cc:
        text = cc.convert(text)
    text = enforce_glossary_output(src, text, glossary)
    text = apply_postprocess(text)
    return text.strip()


def self_check(engine: NvidiaEngine, prompt_engine: PromptEngine, source: str, translated: str, glossary: dict):
    prompt = prompt_engine.build_self_check_prompt(source, translated, glossary)
    result = engine.translate(prompt).strip()
    first_line = result.splitlines()[0].strip() if result else ""
    if first_line.upper() == "PASS":
        return True, "PASS"
    return False, result[:300]


def translate_file(path: Path, engine: NvidiaEngine, config: dict):
    OUTPUT_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)

    output_path = OUTPUT_DIR / f"{path.stem}_zh.txt"
    source_text = read_text_auto(path)
    chunks = split_chunks(source_text, config.get("chunk_size", 1800))
    glossary = load_glossary()
    prompt_engine = PromptEngine(profile_name=config.get("profile", "PASSION"))

    progress = load_progress()
    file_key = path.name
    done_count = progress.get(file_key, 0)

    translated_parts = []
    if output_path.exists():
        translated_parts.append(output_path.read_text(encoding="utf-8"))

    cc = OpenCC("s2twp") if config.get("opencc", True) and OpenCC else None

    print(f"\n📘 開始：{path.name}")
    print(f"📦 共 {len(chunks)} 區塊，從第 {done_count + 1} 區塊開始")

    context = ""
    if translated_parts:
        context = translated_parts[-1][-config.get("context_size", 700):]

    for index, chunk in enumerate(chunks):
        if index < done_count:
            continue

        print(f"🔄 翻譯區塊 {index + 1}/{len(chunks)}")
        result = None
        last_error = None

        for attempt in range(config.get("max_retry", 4)):
            try:
                prompt = prompt_engine.build_translation_prompt(chunk, context, glossary)
                candidate = engine.translate(prompt)
                candidate = normalize_output(candidate, chunk, glossary, cc)

                ok, reason = validate_translation(chunk, candidate, glossary)
                if not ok:
                    raise RuntimeError(reason)

                if config.get("self_check", True):
                    passed, check_reason = self_check(engine, prompt_engine, chunk, candidate, glossary)
                    if not passed:
                        raise RuntimeError(f"Self Check 未通過：{check_reason}")

                result = candidate
                break
            except Exception as e:
                last_error = e
                wait = min(8 * (attempt + 1), 40)
                print(f"⚠️ 第 {attempt + 1} 次失敗：{e}")
                print(f"⏳ 等待 {wait} 秒後重試")
                time.sleep(wait)

        if result is None:
            raise RuntimeError(f"區塊 {index + 1} 翻譯失敗：{last_error}")

        translated_parts.append(result)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(translated_parts))

        progress[file_key] = index + 1
        save_progress(progress)
        context = result[-config.get("context_size", 700):]
        time.sleep(2)

    print(f"✅ 完成：{output_path.name}")


def run_translation():
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
        except Exception as e:
            print(f"❌ 失敗：{file.name}")
            print(e)

    print("\n🎉 全部處理完成")
