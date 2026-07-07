from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.translation_engine import TranslationEngine
from core.translation_engine.utils import now_iso, save_json, save_text
from core.literary import LiteraryPromptBuilder, normalize_profile, normalize_literary_style


DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OUTPUT_SUFFIX = "_zh"
DEFAULT_MAX_RETRIES = 3
DEFAULT_QA_RETRY_PROMPT_ENABLED = True
DEFAULT_RETRY_BASE_SECONDS = 5.0
DEFAULT_CHARACTER_MEMORY = "memory/character_memory_lts.json"
DEFAULT_MIN_LENGTH_RATIO = 0.18
DEFAULT_MAX_KOREAN_CHARS = 2
DEFAULT_MAX_REPEATED_LINES = 2
DEFAULT_OUTPUT_FORMATTER_ENABLED = True
QA_FAIL_POLICIES = ("retry", "fail", "warn")
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
    qa_enabled: bool = True
    qa_fail_policy: str = "retry"
    min_length_ratio: float = DEFAULT_MIN_LENGTH_RATIO
    max_korean_chars: int = DEFAULT_MAX_KOREAN_CHARS
    max_repeated_lines: int = DEFAULT_MAX_REPEATED_LINES
    output_formatter_enabled: bool = DEFAULT_OUTPUT_FORMATTER_ENABLED
    taiwan_traditional_normalization: bool = True
    quality_profile: str = "novel"
    previous_context_chars: int = 700
    simplified_chinese_policy: str = "normalize"  # normalize|warn|fail
    progress_enabled: bool = True


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


# Stage-18.12: production name-lock hotfix.
# The model sometimes translates locked Korean names into plausible but wrong Chinese
# variants.  These aliases are applied after provider output and again before final
# assembly, so glossary terms remain stable even when the model drifts.
DEFAULT_LOCKED_TRANSLATION_ALIASES: dict[str, set[str]] = {
    "鄭泰義": {"定泰義", "丁泰義", "正泰義", "鄭太義", "正太義", "鄭泰宜", "鄭泰儀"},
    "伊萊": {"伊蕾", "伊雷", "伊來", "伊莱", "一萊"},
    "凱爾": {"卡爾", "凱爾爾", "凯尔"},
    "伊萊・里格勞": {"伊萊·里格勞", "伊萊里格勞", "伊萊・利格羅", "伊萊·利格羅", "伊蕾・里格勞", "伊蕾·里格勞"},
    "凱爾・里格勞": {"凱爾·里格勞", "凱爾里格勞", "凱爾・利格羅", "凱爾·利格羅", "卡爾・里格勞"},
}


def build_translation_alias_map(locked_dictionary: dict[str, str]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for target in locked_dictionary.values():
        if not target:
            continue
        for alias in DEFAULT_LOCKED_TRANSLATION_ALIASES.get(target, set()):
            if alias and alias != target:
                aliases[alias] = target
    return aliases


def apply_locked_dictionary(text: str, locked_dictionary: dict[str, str]) -> str:
    result = text or ""
    # TER-v1.1: apply target aliases before source replacements so wrong Chinese
    # variants such as 伊蕾 are normalized even when the Korean source term is
    # already gone from provider output.
    for alias, target in sorted(build_translation_alias_map(locked_dictionary).items(), key=lambda item: len(item[0]), reverse=True):
        if alias and target:
            result = result.replace(alias, target)
    for source, target in sorted(locked_dictionary.items(), key=lambda item: len(item[0]), reverse=True):
        if not source or not target:
            continue
        # Remove accidental Korean/source residue and normalize any exact source term that survived provider output.
        result = result.replace(source, target)
    return result


def matched_locked_dictionary(source_text: str, locked_dictionary: dict[str, str]) -> dict[str, str]:
    """Return only terms that must be enforced for this source segment."""
    return {src: target for src, target in locked_dictionary.items() if src and target and src in source_text}


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
        return {"version": "1.1-lts-stage-05", "chunks": {}, "events": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"version": "1.1-lts-stage-05", "chunks": {}, "events": []}
    if not isinstance(data, dict):
        return {"version": "1.1-lts-stage-05", "chunks": {}, "events": []}
    data.setdefault("version", "1.1-lts-stage-05")
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


def progress_enabled(options: TxtTranslationOptions | None = None) -> bool:
    if options is not None and not getattr(options, "progress_enabled", True):
        return False
    value = os.environ.get("NTPE_PROGRESS", "1").lower()
    return value not in {"0", "false", "no", "off"}


def emit_progress(message: str, *, options: TxtTranslationOptions | None = None) -> None:
    if progress_enabled(options):
        print(f"[NTPE PROGRESS] {message}", flush=True)


def save_live_progress(path: Path, payload: dict) -> None:
    try:
        save_json(path, payload)
    except Exception:
        # Live progress must never break translation.
        pass


def translate_package_with_retry(engine: TranslationEngine, package: dict, package_path: Path, options: TxtTranslationOptions) -> dict:
    attempts = max(1, int(options.max_retries) + 1)
    last_result: dict = {"status": "failed", "error": "translation was not attempted"}
    package_id = package.get("package_id", package_path.stem)
    for attempt in range(1, attempts + 1):
        emit_progress(f"provider request start package={package_id} attempt={attempt}/{attempts}", options=options)
        started = time.time()
        result = engine.translate_package(package, package_path=package_path)
        elapsed = time.time() - started
        result["attempt"] = attempt
        result["provider_elapsed_seconds"] = round(elapsed, 3)
        last_result = result
        if result.get("status") == "success":
            emit_progress(f"provider request success package={package_id} attempt={attempt}/{attempts} elapsed={elapsed:.1f}s", options=options)
            return result
        error = result.get("error", "")
        emit_progress(f"provider request failed package={package_id} attempt={attempt}/{attempts} elapsed={elapsed:.1f}s error={error[:180]}", options=options)
        if attempt >= attempts or not is_retryable_error(error):
            return result
        delay = retry_delay_seconds(attempt, options.retry_base_seconds)
        if delay > 0:
            emit_progress(f"retry wait {delay:.1f}s before next provider request", options=options)
            time.sleep(delay)
    return last_result



TAIWAN_TRADITIONAL_REPLACEMENTS = {
    "台湾": "台灣",
    "台北": "臺北",
    "里面": "裡面",
    "里头": "裡頭",
    "这里": "這裡",
    "那里": "那裡",
    "哪里": "哪裡",
    "为": "為",
    "这": "這",
    "个": "個",
    "后": "後",
    "说": "說",
    "开": "開",
    "门": "門",
    "这": "這",
    "个": "個",
    "为": "為",
    "会": "會",
    "里": "裡",
    "后": "後",
    "发": "發",
    "么": "麼",
    "没": "沒",
    "过": "過",
    "对": "對",
    "还": "還",
    "种": "種",
    "现": "現",
    "实": "實",
    "当": "當",
    "从": "從",
    "长": "長",
    "处": "處",
    "头": "頭",
    "给": "給",
    "让": "讓",
    "觉": "覺",
    "声": "聲",
    "气": "氣",
    "爱": "愛",
    "书": "書",
    "边": "邊",
    "间": "間",
    "见": "見",
    "听": "聽",
    "话": "話",
    "问": "問",
    "答": "答",
    "还": "還",
    "会": "會",
    "对": "對",
    "发": "發",
    "头": "頭",
    "么": "麼",
    "没": "沒",
    "让": "讓",
    "过": "過",
    "时": "時",
    "间": "間",
    "门": "門",
    "声": "聲",
    "来": "來",
    "见": "見",
    "现": "現",
    "长": "長",
    "体": "體",
    "书": "書",
    "气": "氣",
    "脸": "臉",
    "眼": "眼",
    "边": "邊",
    "从": "從",
    "点": "點",
    "样": "樣",
    "听": "聽",
    "话": "話",
    "轻": "輕",
    "动": "動",
    "实": "實",
    "觉": "覺",
    "该": "該",
    "着": "著",
}


# TER-v1.2: extra high-frequency simplified forms observed in provider output.
TAIWAN_TRADITIONAL_REPLACEMENTS.update({
    "扬": "揚",
    "涌": "湧",
    "转": "轉",
    "离": "離",
    "视": "視",
    "顾": "顧",
    "绝": "絕",
    "严": "嚴",
    "为": "為",
    "与": "與",
    "处": "處",
    "压": "壓",
    "积": "積",
    "绪": "緒",
    "郁": "鬱",
    "亚": "亞",
    "尔": "爾",
    "莱": "萊",
    "凯": "凱",
})

def normalize_punctuation_for_zh_tw(text: str) -> str:
    result = text or ""
    # Normalize common ASCII punctuation from provider output into CJK punctuation.
    result = result.replace("...", "……")
    result = result.replace(",", "，")
    result = result.replace(":", "：")
    result = result.replace(";", "；")
    result = result.replace("?", "？")
    result = result.replace("!", "！")
    result = result.replace("(", "（").replace(")", "）")
    # Convert straight quotes in simple dialogue-like output to corner brackets conservatively.
    result = re.sub(r'"([^"\n]{1,200})"', r'「\1」', result)
    result = re.sub(r"'([^'\n]{1,200})'", r"『\1』", result)
    # Collapse excessive punctuation introduced by provider formatting.
    result = re.sub(r"。{2,}", "。", result)
    result = re.sub(r"，{2,}", "，", result)
    result = re.sub(r"！{2,}", "！", result)
    result = re.sub(r"？{2,}", "？", result)
    return result


def normalize_taiwan_traditional(text: str) -> str:
    result = text or ""
    for simplified, traditional in sorted(TAIWAN_TRADITIONAL_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        result = result.replace(simplified, traditional)
    return result


def clean_provider_output(text: str) -> str:
    result = text or ""
    # Remove common model preambles without touching narrative content.
    preamble_patterns = (
        r"^以下(?:是|為).{0,20}翻譯[:：]\s*",
        r"^譯文[:：]\s*",
        r"^翻譯結果[:：]\s*",
    )
    for pattern in preamble_patterns:
        result = re.sub(pattern, "", result.strip(), flags=re.IGNORECASE)
    result = result.replace("\ufeff", "").replace("\x00", "")
    result = result.replace("\r\n", "\n").replace("\r", "\n")
    result = re.sub(r"[ \t]+\n", "\n", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def format_translation_output(text: str, options: TxtTranslationOptions | None = None) -> str:
    options = options or TxtTranslationOptions(input_path=Path("input.txt"), output_dir=Path("output"))
    result = clean_provider_output(text)
    if not options.output_formatter_enabled:
        return result.strip()
    result = normalize_punctuation_for_zh_tw(result)
    if options.taiwan_traditional_normalization:
        result = normalize_taiwan_traditional(result)
    result = normalize_literary_style(result)
    if options.taiwan_traditional_normalization:
        result = normalize_taiwan_traditional(result)
    result = clean_provider_output(result)
    return result.strip()

def count_korean_characters(text: str) -> int:
    return len(re.findall(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]", text or ""))


def _normalized_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def detect_repeated_lines(text: str, max_repeated_lines: int = DEFAULT_MAX_REPEATED_LINES) -> list[str]:
    counts: dict[str, int] = {}
    repeated: list[str] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if len(line) < 4:
            continue
        counts[line] = counts.get(line, 0) + 1
        if counts[line] > max_repeated_lines and line not in repeated:
            repeated.append(line)
    return repeated


def detect_simplified_chinese(text: str) -> list[str]:
    """Return possible simplified-Chinese hits after formatter normalization.

    Stage-18.14 note:
    This detector is intentionally conservative. A single remaining hit should
    not fail a full translation job because providers sometimes output rare
    characters that overlap with simplified forms or proper nouns.
    """
    return [simp for simp in TAIWAN_TRADITIONAL_REPLACEMENTS if simp in (text or "")][:20]


def should_fail_on_simplified_chinese(options: TxtTranslationOptions, hit_count: int) -> bool:
    policy = (getattr(options, "simplified_chinese_policy", "normalize") or "normalize").lower()
    if policy == "fail":
        return hit_count > 0
    return False


def detect_locked_term_violations(source_text: str, translated_text: str, locked_dictionary: dict[str, str]) -> list[dict]:
    violations: list[dict] = []
    for src, target in locked_dictionary.items():
        if src and src in source_text and target and target not in translated_text:
            violations.append({"source": src, "target": target, "code": "LOCKED_TERM_MISSING"})
    for alias, target in build_translation_alias_map(locked_dictionary).items():
        if alias and alias in translated_text:
            violations.append({"alias": alias, "target": target, "code": "LOCKED_ALIAS_USED"})
    return violations


def analyze_translation_quality(source_text: str, translated_text: str, options: TxtTranslationOptions | None = None, locked_dictionary: dict[str, str] | None = None) -> dict:
    options = options or TxtTranslationOptions(input_path=Path("input.txt"), output_dir=Path("output"))
    korean_chars = count_korean_characters(translated_text)
    source_len = max(1, _normalized_len(source_text))
    translated_len = _normalized_len(translated_text)
    length_ratio = translated_len / source_len
    repeated_lines = detect_repeated_lines(translated_text, options.max_repeated_lines)
    simplified_hits = detect_simplified_chinese(translated_text) if options.taiwan_traditional_normalization else []
    term_violations = detect_locked_term_violations(source_text, translated_text, locked_dictionary or {})
    issues: list[dict] = []
    if korean_chars > options.max_korean_chars:
        issues.append({
            "code": "KOREAN_RESIDUE",
            "message": f"KOREAN_RESIDUE korean_chars={korean_chars} max={options.max_korean_chars}",
        })
    if translated_len == 0:
        issues.append({"code": "EMPTY_TRANSLATION", "message": "EMPTY_TRANSLATION translated output is empty"})
    elif length_ratio < options.min_length_ratio:
        issues.append({"code": "LENGTH_RATIO_TOO_LOW", "message": f"LENGTH_RATIO_TOO_LOW ratio={length_ratio:.3f} min={options.min_length_ratio:.3f}"})
    if repeated_lines:
        issues.append({"code": "REPEATED_LINES", "message": f"REPEATED_LINES count={len(repeated_lines)}", "samples": repeated_lines[:3]})
    if simplified_hits:
        issue = {
            "code": "SIMPLIFIED_CHINESE",
            "message": f"SIMPLIFIED_CHINESE hits={len(simplified_hits)} policy={options.simplified_chinese_policy}",
            "samples": simplified_hits[:10],
            "severity": "error" if should_fail_on_simplified_chinese(options, len(simplified_hits)) else "warning",
        }
        if should_fail_on_simplified_chinese(options, len(simplified_hits)):
            issues.append(issue)
        else:
            # Keep metric visibility without failing the chunk.
            pass
    if term_violations:
        issues.append({"code": "LOCKED_TERM_VIOLATION", "message": f"LOCKED_TERM_VIOLATION count={len(term_violations)}", "samples": term_violations[:10]})
    return {
        "passed": not any(issue.get("severity", "error") == "error" for issue in issues),
        "issues": issues,
        "metrics": {
            "korean_chars": korean_chars,
            "source_chars": source_len,
            "translated_chars": translated_len,
            "length_ratio": round(length_ratio, 4),
            "repeated_line_count": len(repeated_lines),
            "simplified_hits": len(simplified_hits),
            "locked_term_violations": len(term_violations),
        },
    }


def qa_retry_delay_seconds(attempt: int, base_seconds: float) -> float:
    # QA retry uses a softer delay than provider-limit retry.
    return min(retry_delay_seconds(attempt, base_seconds), 30.0)


def _extract_pairs(data) -> dict[str, str]:
    pairs: dict[str, str] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and isinstance(key, str):
                pairs[key] = value
            elif isinstance(value, dict):
                source = value.get("source") or value.get("ko") or value.get("korean") or key
                target = value.get("target") or value.get("translation") or value.get("zh") or value.get("traditional") or value.get("name")
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



def get_max_output_tokens(chunk_text: str, options: TxtTranslationOptions) -> int:
    env_value = __import__("os").environ.get("NTPE_MAX_OUTPUT_TOKENS")
    if env_value:
        try:
            return max(800, min(6000, int(float(env_value))))
        except ValueError:
            pass
    profile = (options.quality_profile or "novel").lower()
    if profile == "fast":
        return max(900, min(1800, math.ceil(len(chunk_text) * 1.25)))
    if profile == "balanced":
        return max(1100, min(2800, math.ceil(len(chunk_text) * 1.50)))
    if profile == "premium":
        return max(1600, min(4600, math.ceil(len(chunk_text) * 1.95)))
    if profile == "quality":
        # Backward compatible alias for premium.
        return max(1500, min(4200, math.ceil(len(chunk_text) * 1.85)))
    # literary / novel default
    return max(1200, min(3400, math.ceil(len(chunk_text) * 1.65)))

def build_prompt_package(
    *,
    options: TxtTranslationOptions,
    chunk_text: str,
    chunk_index: int,
    chunk_total: int,
    locked_dictionary: dict[str, str],
    previous_context: str = "",
) -> dict:
    input_name = options.input_path.name
    package_id = f"TXT_{options.input_path.stem}_{chunk_index:06d}"
    source_hash = hashlib.sha1(chunk_text.encode("utf-8")).hexdigest()
    matched = {src: target for src, target in locked_dictionary.items() if src and src in chunk_text}

    alias_map = build_translation_alias_map(matched)
    profile = normalize_profile(options.quality_profile or "literary")

    prompt_result = LiteraryPromptBuilder().build(
        chunk_text=chunk_text,
        locked_dictionary=matched,
        alias_map=alias_map,
        previous_context=previous_context.strip(),
        profile=profile,
    )
    system_prompt = prompt_result.system_prompt
    user_prompt = prompt_result.user_prompt

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
            "temperature": 0.12 if profile in ("literary", "premium") else 0.15,
            "top_p": 0.82 if profile in ("literary", "premium") else 0.85,
            "max_output_tokens": get_max_output_tokens(chunk_text, options),
        },
        "source": {
            "chunk_text": chunk_text,
            "source_hash": source_hash,
            "char_count": len(chunk_text),
        },
        "context": {
            "previous_summary": "",
            "previous_chunk_tail": previous_context[-options.previous_context_chars:] if previous_context else "",
            "recent_characters": prompt_result.character_context.current_focus,
            "recent_terms": [term.target for term in prompt_result.glossary_context.matched_terms],
            "narrative_context": prompt_result.narrative_context.to_dict(),
            "character_context": prompt_result.character_context.to_dict(),
        },
        "knowledge": {
            "locked_dictionary": matched,
        },
        "prompt": prompt_result.to_prompt_dict(),
        "qa_requirements": {
            "check_korean_residue": True,
            "check_name_rules": True,
            "check_glossary": True,
            "check_repetition": True,
            "check_length_ratio": True,
            "check_literary_policy": True,
        },
        "metadata": {
            "created_at": now_iso(),
            "created_by": "NTPE 1.2 Translation Engine Refactoring v1.2",
            "package_version": "1.2-translation-engine-refactor-v1.2",
        },
    }


def build_qa_retry_user_prompt(original_user_prompt: str, qa_report: dict, qa_attempt: int) -> str:
    """Create a stricter retry prompt after QA rejects a provider output."""
    issues = qa_report.get("issues", []) if isinstance(qa_report, dict) else []
    issue_lines = []
    locked_lines = []
    for issue in issues[:8]:
        if isinstance(issue, dict):
            code = issue.get("code") or issue.get("type") or "QA_ISSUE"
            message = issue.get("message") or ""
            issue_lines.append(f"- {code}: {message}")
            for sample in issue.get("samples", []) if isinstance(issue.get("samples"), list) else []:
                if isinstance(sample, dict) and sample.get("source") and sample.get("target"):
                    locked_lines.append(f"- {sample['source']} => {sample['target']}")
    issue_text = "\n".join(issue_lines) or "- QA_FAILED: previous output did not pass validation"
    locked_text = "\n".join(dict.fromkeys(locked_lines)) or "- 依 Glossary 欄位嚴格執行"
    retry_note = f"""

【NTPE 自動重試指令】
前一次輸出未通過品質檢查，請重新翻譯，不要沿用前一次輸出。
失敗原因：
{issue_text}

必須修正的鎖定譯名：
{locked_text}

重試要求：
- 請直接完整翻成自然流暢、符合小說背景的繁體中文。
- 鎖定譯名必須逐字一致，不能自行改成近似音譯。
- 嚴禁複製韓文原文作為譯文。
- 嚴禁輸出「以下是翻譯」等說明。
- 保留段落順序與劇情資訊，不可摘要。
- 這是第 {qa_attempt} 次 QA 重試。
"""
    return original_user_prompt.rstrip() + retry_note

def translate_txt(options: TxtTranslationOptions, root: str | Path | None = None) -> dict:
    root_path = Path(root) if root else Path(__file__).resolve().parents[1]
    input_path = options.input_path if options.input_path.is_absolute() else root_path / options.input_path
    output_dir = options.output_dir if options.output_dir.is_absolute() else root_path / options.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    emit_progress(f"read input: {input_path}", options=options)
    text = read_text_auto(input_path)
    emit_progress(f"split text: chars={len(text)} chunk_size={options.chunk_size}", options=options)
    chunks = split_text(text, options.chunk_size)
    if not chunks:
        raise ValueError(f"輸入檔案沒有可翻譯內容：{input_path}")
    emit_progress(f"chunk plan: total={len(chunks)}", options=options)

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
    live_progress_path = output_dir / f"{input_path.stem}_live_progress.json"
    save_live_progress(live_progress_path, {
        "status": "running",
        "input": str(input_path),
        "output_dir": str(output_dir),
        "chunk_total": len(chunks),
        "chunk_completed": 0,
        "current_step": "initialized",
        "updated_at": now_iso(),
    })
    resume_state = load_resume_state(resume_state_path)
    resume_state["input"] = str(input_path)
    resume_state["output_dir"] = str(output_dir)
    resume_state["chunk_total"] = len(chunks)
    resume_state["updated_at"] = now_iso()
    save_resume_state(resume_state_path, resume_state)

    for idx, chunk in enumerate(chunks, start=1):
        emit_progress(f"chunk {idx}/{len(chunks)} prepare package chars={len(chunk)}", options=options)
        save_live_progress(live_progress_path, {
            "status": "running",
            "input": str(input_path),
            "output_dir": str(output_dir),
            "chunk_total": len(chunks),
            "chunk_completed": max(0, idx - 1),
            "current_chunk": idx,
            "current_step": "prepare_package",
            "updated_at": now_iso(),
        })
        package = build_prompt_package(
            options=options,
            chunk_text=chunk,
            chunk_index=idx,
            chunk_total=len(chunks),
            locked_dictionary=locked_dictionary,
            previous_context="\n\n".join(translated_chunks[-2:])[-options.previous_context_chars:] if translated_chunks else "",
        )
        package_path = stage_dir / f"{input_path.stem}_chunk_{idx:06d}.json"
        save_json(package_path, package)
        prompt_profile = package.get("prompt", {}).get("prompt_profile", {})
        if prompt_profile:
            emit_progress(
                "chunk {}/{} prompt profile: total={} system={} policy={} context={} glossary={} source={}".format(
                    idx,
                    len(chunks),
                    prompt_profile.get("total_tokens", "?"),
                    prompt_profile.get("system_tokens", "?"),
                    prompt_profile.get("policy_tokens", "?"),
                    prompt_profile.get("context_tokens", "?"),
                    prompt_profile.get("glossary_tokens", "?"),
                    prompt_profile.get("source_tokens", "?"),
                ),
                options=options,
            )
        emit_progress(f"chunk {idx}/{len(chunks)} package saved: {package_path.name}", options=options)

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
            emit_progress(f"chunk {idx}/{len(chunks)} resume hit: using cached output", options=options)
            translation = chunk_file.read_text(encoding="utf-8")
            if options.strict_lock_terms:
                translation = apply_locked_dictionary(translation, locked_dictionary)
            result = {"status": "skipped", "output_path": str(chunk_file), "package_id": package["package_id"], "attempt": 0}
        elif options.dry_run:
            emit_progress(f"chunk {idx}/{len(chunks)} dry-run: skip provider", options=options)
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
            qa_attempt_records: list[dict] = []
            qa_report = {"passed": True, "issues": [], "metrics": {}}
            translation = ""
            result = {"status": "failed", "error": "translation was not attempted", "attempt": 0}
            qa_attempts = max(1, int(options.max_retries) + 1) if options.qa_fail_policy == "retry" else 1
            original_user_prompt = package["prompt"]["user_prompt"]
            for qa_attempt in range(1, qa_attempts + 1):
                emit_progress(f"chunk {idx}/{len(chunks)} QA attempt {qa_attempt}/{qa_attempts}", options=options)
                save_live_progress(live_progress_path, {
                    "status": "running",
                    "input": str(input_path),
                    "output_dir": str(output_dir),
                    "chunk_total": len(chunks),
                    "chunk_completed": max(0, idx - 1),
                    "current_chunk": idx,
                    "current_step": f"provider_and_qa_attempt_{qa_attempt}",
                    "updated_at": now_iso(),
                })
                if qa_attempt > 1:
                    package["prompt"]["user_prompt"] = build_qa_retry_user_prompt(original_user_prompt, qa_report, qa_attempt)
                    save_json(package_path, package)
                result = translate_package_with_retry(engine, package, package_path, options)
                result["qa_attempt"] = qa_attempt
                if result.get("status") != "success":
                    break
                generated_path = Path(result["output_path"])
                emit_progress(f"chunk {idx}/{len(chunks)} provider output received", options=options)
                translation = generated_path.read_text(encoding="utf-8")
                if options.strict_lock_terms:
                    translation = apply_locked_dictionary(translation, locked_dictionary)
                translation = format_translation_output(translation, options)
                qa_report = analyze_translation_quality(chunk, translation, options, locked_dictionary=package.get("knowledge", {}).get("locked_dictionary", {})) if options.qa_enabled else {"passed": True, "issues": [], "metrics": {}}
                qa_attempt_records.append({"qa_attempt": qa_attempt, "qa": qa_report})
                emit_progress(f"chunk {idx}/{len(chunks)} QA {'PASS' if qa_report.get('passed') else 'FAIL'} issues={len(qa_report.get('issues', []))}", options=options)
                if qa_report.get("passed") or options.qa_fail_policy == "warn":
                    break
                if options.qa_fail_policy == "fail" or qa_attempt >= qa_attempts:
                    break
                delay = qa_retry_delay_seconds(qa_attempt, options.retry_base_seconds)
                if delay > 0:
                    time.sleep(delay)

            if result.get("status") != "success":
                resume_state["chunks"][chunk_key] = {
                    "status": "failed",
                    "source_hash": source_hash,
                    "error": result.get("error", "unknown error"),
                    "attempt": result.get("attempt", 1),
                    "qa_attempt": result.get("qa_attempt", 1),
                    "updated_at": now_iso(),
                }
                resume_state["events"].append({
                    "event": "chunk_failed",
                    "chunk_index": idx,
                    "error": result.get("error", "unknown error"),
                    "at": now_iso(),
                })
                save_resume_state(resume_state_path, resume_state)
                save_live_progress(live_progress_path, {
                    "status": "failed",
                    "input": str(input_path),
                    "chunk_total": len(chunks),
                    "chunk_completed": max(0, idx - 1),
                    "failed_chunk": idx,
                    "current_step": "provider_failed",
                    "error": result.get("error", "unknown error"),
                    "updated_at": now_iso(),
                })
                emit_progress(f"chunk {idx}/{len(chunks)} FAILED provider error={result.get('error', 'unknown error')[:180]}", options=options)
                return {
                    "status": "failed",
                    "input": str(input_path),
                    "failed_chunk": idx,
                    "error": result.get("error", "unknown error"),
                    "records": records,
                    "resume_state": str(resume_state_path),
                }

            qa_failed = options.qa_enabled and not qa_report.get("passed", True) and options.qa_fail_policy != "warn"
            if qa_failed:
                error = "; ".join(issue.get("message", issue.get("code", "QA_FAILED")) for issue in qa_report.get("issues", [])) or "translation QA failed"
                resume_state["chunks"][chunk_key] = {
                    "status": "qa_failed",
                    "source_hash": source_hash,
                    "error": error,
                    "qa": qa_report,
                    "attempt": result.get("attempt", 1),
                    "qa_attempt": result.get("qa_attempt", 1),
                    "updated_at": now_iso(),
                }
                resume_state["events"].append({
                    "event": "chunk_qa_failed",
                    "chunk_index": idx,
                    "error": error,
                    "qa": qa_report,
                    "at": now_iso(),
                })
                save_resume_state(resume_state_path, resume_state)
                save_live_progress(live_progress_path, {
                    "status": "failed",
                    "input": str(input_path),
                    "chunk_total": len(chunks),
                    "chunk_completed": max(0, idx - 1),
                    "failed_chunk": idx,
                    "current_step": "qa_failed",
                    "error": error,
                    "updated_at": now_iso(),
                })
                emit_progress(f"chunk {idx}/{len(chunks)} FAILED QA error={error[:180]}", options=options)
                return {
                    "status": "failed",
                    "input": str(input_path),
                    "failed_chunk": idx,
                    "error": error,
                    "qa": qa_report,
                    "records": records,
                    "resume_state": str(resume_state_path),
                }

            save_text(chunk_file, translation)
            emit_progress(f"chunk {idx}/{len(chunks)} saved: {chunk_file.name}", options=options)
            resume_state["chunks"][chunk_key] = {
                "status": "success",
                "source_hash": source_hash,
                "output_path": str(chunk_file),
                "attempt": result.get("attempt", 1),
                "qa_attempt": result.get("qa_attempt", 1),
                "qa": qa_report,
                "updated_at": now_iso(),
            }
            result["qa"] = qa_report
            result["qa_attempt_records"] = qa_attempt_records
            save_resume_state(resume_state_path, resume_state)

        save_live_progress(live_progress_path, {
            "status": "running",
            "input": str(input_path),
            "output_dir": str(output_dir),
            "chunk_total": len(chunks),
            "chunk_completed": idx,
            "current_chunk": idx,
            "current_step": "chunk_completed",
            "updated_at": now_iso(),
        })
        if translation:
            translated_chunks.append(translation.strip())
        records.append(result | {"chunk_index": idx, "chunk_total": len(chunks)})

    final_output = output_dir / f"{input_path.stem}{DEFAULT_OUTPUT_SUFFIX}.txt"
    if not options.dry_run:
        final_text = "\n\n".join(translated_chunks).strip() + "\n"
        if options.strict_lock_terms:
            final_text = apply_locked_dictionary(final_text, locked_dictionary)
        final_text = format_translation_output(final_text, options).strip() + "\n"
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
        "qa": {"enabled": options.qa_enabled, "fail_policy": options.qa_fail_policy, "min_length_ratio": options.min_length_ratio, "max_korean_chars": options.max_korean_chars, "max_repeated_lines": options.max_repeated_lines},
        "formatter": {"enabled": options.output_formatter_enabled, "taiwan_traditional_normalization": options.taiwan_traditional_normalization},
        "character_memory": str(character_memory_path),
        "dry_run": options.dry_run,
        "completed_at": now_iso(),
        "records": records,
    }
    save_json(output_dir / f"{input_path.stem}_translation_manifest.json", manifest)
    save_live_progress(live_progress_path, {
        "status": "success",
        "input": str(input_path),
        "output": str(final_output),
        "chunk_total": len(chunks),
        "chunk_completed": len(chunks),
        "current_step": "completed",
        "updated_at": now_iso(),
    })
    emit_progress(f"completed: {final_output}", options=options)
    return manifest


def parse_args(argv: Iterable[str] | None = None) -> TxtTranslationOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS Stage-05 TXT novel translation entry")
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
    parser.add_argument("--no-qa", action="store_true", help="disable translation QA checks")
    parser.add_argument("--qa-fail-policy", choices=QA_FAIL_POLICIES, default="retry", help="QA failure behavior: retry, fail, or warn")
    parser.add_argument("--min-length-ratio", type=float, default=DEFAULT_MIN_LENGTH_RATIO, help="minimum translated/source character ratio")
    parser.add_argument("--max-korean-chars", type=int, default=DEFAULT_MAX_KOREAN_CHARS, help="maximum allowed Korean characters after translation")
    parser.add_argument("--max-repeated-lines", type=int, default=DEFAULT_MAX_REPEATED_LINES, help="maximum allowed repeats for the same non-trivial output line")
    parser.add_argument("--no-output-formatter", action="store_true", help="disable output punctuation/cleanup formatter")
    parser.add_argument("--no-taiwan-normalization", action="store_true", help="disable built-in Taiwan Traditional Chinese normalization")
    parser.add_argument("--simplified-chinese-policy", choices=("normalize", "warn", "fail"), default="normalize", help="remaining simplified Chinese behavior after normalization")
    parser.add_argument("--quality-profile", choices=("fast", "balanced", "novel", "literary", "quality", "premium"), default="literary", help="translation quality profile")
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
        qa_enabled=not ns.no_qa,
        qa_fail_policy=ns.qa_fail_policy,
        min_length_ratio=max(0.0, ns.min_length_ratio),
        max_korean_chars=max(0, ns.max_korean_chars),
        max_repeated_lines=max(0, ns.max_repeated_lines),
        output_formatter_enabled=not ns.no_output_formatter,
        taiwan_traditional_normalization=not ns.no_taiwan_normalization,
        quality_profile=ns.quality_profile,
        simplified_chinese_policy=ns.simplified_chinese_policy,
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
