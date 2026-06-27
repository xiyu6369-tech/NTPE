# =====================================================
# NTPE Document Analyzer v1.0
# 功能：
# 1. 分析 normalized TXT 文件
# 2. 統計語言比例、字數、行數、段落數
# 3. 偵測章節、對話比例、重複段落
# 4. 偵測疑似人物名、術語、亂碼
# 5. 輸出 analysis.json / report.txt / statistics.csv
# =====================================================

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter


ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "output"
ANALYSIS_DIR = ROOT / "analysis"
LOG_DIR = ROOT / "logs"

SUPPORTED_EXT = ".txt"

TOP_CHARACTER_LIMIT = 80
TOP_TERM_LIMIT = 120
TOP_REPEAT_LIMIT = 80


def ensure_dirs() -> None:
    for folder in [INPUT_DIR, ANALYSIS_DIR, LOG_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    ensure_dirs()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line)

    log_file = LOG_DIR / "analyzer_log.txt"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def safe_percent(part: int | float, total: int | float) -> float:
    if not total:
        return 0.0
    return round((part / total) * 100, 4)


def count_language_chars(text: str) -> dict:
    korean = len(re.findall(r"[\uac00-\ud7af]", text))
    hangul_jamo = len(re.findall(r"[\u1100-\u11ff\u3130-\u318f]", text))
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    japanese = len(re.findall(r"[\u3040-\u30ff]", text))
    english = len(re.findall(r"[A-Za-z]", text))
    digits = len(re.findall(r"[0-9]", text))

    total_lang = korean + hangul_jamo + chinese + japanese + english + digits

    return {
        "korean": korean,
        "hangul_jamo": hangul_jamo,
        "chinese": chinese,
        "japanese": japanese,
        "english": english,
        "digits": digits,
        "total_language_chars": total_lang,
        "ratio": {
            "korean": safe_percent(korean + hangul_jamo, total_lang),
            "chinese": safe_percent(chinese, total_lang),
            "japanese": safe_percent(japanese, total_lang),
            "english": safe_percent(english, total_lang),
            "digits": safe_percent(digits, total_lang),
        },
    }


def count_basic_statistics(text: str) -> dict:
    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    return {
        "characters_total": len(text),
        "characters_no_spaces": len(re.sub(r"\s+", "", text)),
        "lines_total": len(lines),
        "lines_non_empty": len(non_empty_lines),
        "paragraphs": len(paragraphs),
        "estimated_korean_words": len(re.findall(r"[\uac00-\ud7af]+", text)),
        "estimated_chinese_chars": len(re.findall(r"[\u4e00-\u9fff]", text)),
    }


def detect_dialogue(text: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    dialogue_markers = [
        r"^「.*」$",
        r"^『.*』$",
        r'^".*"$',
        r"^'.*'$",
        r"^[「『\"']",
        r"[」』\"']$",
        r"^\-",
    ]

    dialogue_lines = 0

    for line in lines:
        if any(re.search(pattern, line) for pattern in dialogue_markers):
            dialogue_lines += 1

    quote_counts = {
        "「": text.count("「"),
        "」": text.count("」"),
        "『": text.count("『"),
        "』": text.count("』"),
        '"': text.count('"'),
        "'": text.count("'"),
    }

    return {
        "lines_total_non_empty": len(lines),
        "dialogue_lines_estimated": dialogue_lines,
        "narration_lines_estimated": max(len(lines) - dialogue_lines, 0),
        "dialogue_ratio_percent": safe_percent(dialogue_lines, len(lines)),
        "narration_ratio_percent": safe_percent(max(len(lines) - dialogue_lines, 0), len(lines)),
        "quote_counts": quote_counts,
    }


def detect_chapters(text: str) -> dict:
    patterns = [
        r"^\s*第\s*[一二三四五六七八九十百千0-9]+\s*[章回節卷部].*$",
        r"^\s*[一二三四五六七八九十百千0-9]+\s*[章回節卷部]\s*$",
        r"^\s*Chapter\s+\d+.*$",
        r"^\s*CHAPTER\s+\d+.*$",
        r"^\s*chapter\s+\d+.*$",
        r"^\s*\d+\s*[.)、]\s*$",
        r"^\s*#{1,6}\s+.+$",
        r"^\s*\*{3,}\s*$",
        r"^\s*-{3,}\s*$",
    ]

    chapters = []

    for i, line in enumerate(text.splitlines(), start=1):
        s = line.strip()
        if not s:
            continue

        if any(re.match(pattern, s) for pattern in patterns):
            chapters.append({
                "line": i,
                "title": s[:120],
            })

    return {
        "chapter_count_estimated": len(chapters),
        "chapters": chapters[:300],
    }


def detect_korean_names(text: str) -> list[dict]:
    """
    v1.0 使用保守規則：
    - 2~5 字韓文詞
    - 排除常見助詞與普通詞尾
    - 出現次數越高越可能是人物名
    """
    tokens = re.findall(r"[\uac00-\ud7af]{2,5}", text)

    stopwords = {
        "것이다", "그리고", "하지만", "그러나", "그것", "이것", "저것",
        "그는", "그녀", "나는", "너는", "우리는", "그들이", "사람",
        "남자", "여자", "아이", "오늘", "어제", "내일", "시간",
        "정말", "아주", "너무", "조금", "다시", "이미", "아니",
        "그런", "이런", "저런", "모든", "아무", "무엇", "어디",
        "했다", "한다", "있는", "없는", "된다", "됐다", "싶다",
        "말했다", "생각", "자신", "얼굴", "눈을", "손을",
    }

    candidates = []

    for token in tokens:
        if token in stopwords:
            continue
        if token.endswith(("했다", "한다", "었다", "였다", "있는", "없는", "지만", "면서", "에게", "에서", "으로", "하고", "처럼")):
            continue
        if len(token) < 2:
            continue
        candidates.append(token)

    counter = Counter(candidates)

    result = []
    for name, count in counter.most_common(TOP_CHARACTER_LIMIT):
        if count >= 3:
            result.append({
                "name": name,
                "count": count,
            })

    return result


def detect_terms(text: str) -> list[dict]:
    """
    偵測英文縮寫、英數術語、常見專有名詞候選。
    """
    patterns = [
        r"\b[A-Z]{2,}\b",
        r"\b[A-Za-z]+[0-9]+[A-Za-z0-9\-]*\b",
        r"\b[A-Za-z][A-Za-z\-]{3,}\b",
    ]

    terms = []
    for pattern in patterns:
        terms.extend(re.findall(pattern, text))

    counter = Counter(terms)

    result = []
    for term, count in counter.most_common(TOP_TERM_LIMIT):
        if count >= 2:
            result.append({
                "term": term,
                "count": count,
            })

    return result


def detect_repetition(text: str) -> dict:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    sentences = re.split(r"(?<=[。！？!?])\s*", text)

    paragraph_counter = Counter(p for p in paragraphs if len(p) >= 20)
    sentence_counter = Counter(s.strip() for s in sentences if len(s.strip()) >= 20)

    repeated_paragraphs = [
        {"text": p[:200], "count": c}
        for p, c in paragraph_counter.most_common(TOP_REPEAT_LIMIT)
        if c >= 2
    ]

    repeated_sentences = [
        {"text": s[:200], "count": c}
        for s, c in sentence_counter.most_common(TOP_REPEAT_LIMIT)
        if c >= 2
    ]

    return {
        "repeated_paragraph_count": len(repeated_paragraphs),
        "repeated_sentence_count": len(repeated_sentences),
        "repeated_paragraphs": repeated_paragraphs,
        "repeated_sentences": repeated_sentences,
    }


def detect_corruption(text: str) -> dict:
    replacement_char = text.count("�")
    null_char = text.count("\x00")
    control_chars = re.findall(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", text)
    mojibake_hits = []

    mojibake_patterns = [
        "Ã", "Â", "â€", "ï¼", "ì", "ê", "ë",
    ]

    for p in mojibake_patterns:
        count = text.count(p)
        if count:
            mojibake_hits.append({"pattern": p, "count": count})

    corruption_score = 0
    corruption_score += replacement_char * 10
    corruption_score += null_char * 10
    corruption_score += len(control_chars) * 3
    corruption_score += sum(item["count"] for item in mojibake_hits)

    if corruption_score == 0:
        level = "clean"
    elif corruption_score < 20:
        level = "minor"
    elif corruption_score < 100:
        level = "warning"
    else:
        level = "danger"

    return {
        "replacement_char": replacement_char,
        "null_char": null_char,
        "control_char_count": len(control_chars),
        "mojibake_hits": mojibake_hits,
        "corruption_score": corruption_score,
        "level": level,
    }


def build_character_memory(character_candidates: list[dict]) -> dict:
    memory = {}

    for item in character_candidates:
        name = item["name"]
        memory[name] = {
            "source": name,
            "translation": "",
            "count": item["count"],
            "locked": False,
            "note": "auto-detected by NTPE Document Analyzer v1.0",
        }

    return memory


def build_glossary_auto(terms: list[dict]) -> dict:
    glossary = {}

    for item in terms:
        term = item["term"]
        glossary[term] = {
            "source": term,
            "translation": "",
            "count": item["count"],
            "locked": False,
            "note": "auto-detected by NTPE Document Analyzer v1.0",
        }

    return glossary


def analyze_text(path: Path, text: str) -> dict:
    basic = count_basic_statistics(text)
    language = count_language_chars(text)
    dialogue = detect_dialogue(text)
    chapters = detect_chapters(text)
    characters = detect_korean_names(text)
    terms = detect_terms(text)
    repetition = detect_repetition(text)
    corruption = detect_corruption(text)

    return {
        "ntpe_module": "Document Analyzer",
        "version": "1.0",
        "file": {
            "name": path.name,
            "stem": path.stem,
            "path": str(path),
            "analyzed_at": datetime.now().isoformat(timespec="seconds"),
        },
        "basic_statistics": basic,
        "language_statistics": language,
        "dialogue_statistics": dialogue,
        "chapter_detection": chapters,
        "character_candidates": characters,
        "term_candidates": terms,
        "repetition_detection": repetition,
        "corruption_detection": corruption,
        "character_memory_auto": build_character_memory(characters),
        "glossary_auto": build_glossary_auto(terms),
    }


def save_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_report(path: Path, data: dict) -> None:
    b = data["basic_statistics"]
    l = data["language_statistics"]
    d = data["dialogue_statistics"]
    c = data["chapter_detection"]
    corrupt = data["corruption_detection"]

    lines = []
    lines.append("====================================")
    lines.append("NTPE Document Analyzer v1.0 Report")
    lines.append("====================================")
    lines.append("")
    lines.append(f"檔案：{data['file']['name']}")
    lines.append(f"分析時間：{data['file']['analyzed_at']}")
    lines.append("")
    lines.append("【基本統計】")
    lines.append(f"總字元數：{b['characters_total']}")
    lines.append(f"不含空白字元數：{b['characters_no_spaces']}")
    lines.append(f"總行數：{b['lines_total']}")
    lines.append(f"非空行數：{b['lines_non_empty']}")
    lines.append(f"段落數：{b['paragraphs']}")
    lines.append("")
    lines.append("【語言比例】")
    lines.append(f"韓文：{l['ratio']['korean']}%")
    lines.append(f"中文：{l['ratio']['chinese']}%")
    lines.append(f"日文：{l['ratio']['japanese']}%")
    lines.append(f"英文：{l['ratio']['english']}%")
    lines.append(f"數字：{l['ratio']['digits']}%")
    lines.append("")
    lines.append("【對話比例】")
    lines.append(f"推定對話行：{d['dialogue_lines_estimated']}")
    lines.append(f"推定敘述行：{d['narration_lines_estimated']}")
    lines.append(f"對話比例：{d['dialogue_ratio_percent']}%")
    lines.append("")
    lines.append("【章節偵測】")
    lines.append(f"推定章節數：{c['chapter_count_estimated']}")
    for ch in c["chapters"][:30]:
        lines.append(f"  Line {ch['line']}: {ch['title']}")
    if len(c["chapters"]) > 30:
        lines.append(f"  ... 其餘 {len(c['chapters']) - 30} 筆省略，完整資料請看 JSON")
    lines.append("")
    lines.append("【疑似人物名 TOP 30】")
    for item in data["character_candidates"][:30]:
        lines.append(f"  {item['name']}：{item['count']}")
    lines.append("")
    lines.append("【疑似術語 TOP 30】")
    for item in data["term_candidates"][:30]:
        lines.append(f"  {item['term']}：{item['count']}")
    lines.append("")
    lines.append("【重複偵測】")
    rep = data["repetition_detection"]
    lines.append(f"重複段落種類：{rep['repeated_paragraph_count']}")
    lines.append(f"重複句子種類：{rep['repeated_sentence_count']}")
    lines.append("")
    lines.append("【損壞偵測】")
    lines.append(f"等級：{corrupt['level']}")
    lines.append(f"損壞分數：{corrupt['corruption_score']}")
    lines.append(f"替代字元 �：{corrupt['replacement_char']}")
    lines.append(f"NULL：{corrupt['null_char']}")
    lines.append(f"控制字元：{corrupt['control_char_count']}")
    lines.append("")
    lines.append("====================================")
    lines.append("分析完成")
    lines.append("====================================")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def save_statistics_csv(path: Path, data: dict) -> None:
    b = data["basic_statistics"]
    l = data["language_statistics"]
    d = data["dialogue_statistics"]
    c = data["chapter_detection"]
    corrupt = data["corruption_detection"]
    rep = data["repetition_detection"]

    rows = [
        ("file", data["file"]["name"]),
        ("characters_total", b["characters_total"]),
        ("characters_no_spaces", b["characters_no_spaces"]),
        ("lines_total", b["lines_total"]),
        ("lines_non_empty", b["lines_non_empty"]),
        ("paragraphs", b["paragraphs"]),
        ("korean_ratio_percent", l["ratio"]["korean"]),
        ("chinese_ratio_percent", l["ratio"]["chinese"]),
        ("japanese_ratio_percent", l["ratio"]["japanese"]),
        ("english_ratio_percent", l["ratio"]["english"]),
        ("dialogue_ratio_percent", d["dialogue_ratio_percent"]),
        ("chapter_count_estimated", c["chapter_count_estimated"]),
        ("character_candidate_count", len(data["character_candidates"])),
        ("term_candidate_count", len(data["term_candidates"])),
        ("repeated_paragraph_count", rep["repeated_paragraph_count"]),
        ("repeated_sentence_count", rep["repeated_sentence_count"]),
        ("corruption_level", corrupt["level"]),
        ("corruption_score", corrupt["corruption_score"]),
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerows(rows)


def save_character_memory(path: Path, data: dict) -> None:
    save_json(path, data["character_memory_auto"])


def save_glossary_auto(path: Path, data: dict) -> None:
    save_json(path, data["glossary_auto"])


def list_input_files() -> list[Path]:
    ensure_dirs()
    files = sorted(
        [p for p in INPUT_DIR.iterdir() if p.is_file() and p.suffix.lower() == SUPPORTED_EXT],
        key=lambda p: p.name.lower(),
    )

    # 優先分析 normalizer 輸出的檔案
    normalized = [p for p in files if p.stem.endswith("_normalized")]
    if normalized:
        return normalized

    return files


def analyze_file(path: Path) -> None:
    text = read_text(path)
    data = analyze_text(path, text)

    stem = path.stem
    json_path = ANALYSIS_DIR / f"{stem}_analysis.json"
    report_path = ANALYSIS_DIR / f"{stem}_report.txt"
    csv_path = ANALYSIS_DIR / f"{stem}_statistics.csv"
    memory_path = ANALYSIS_DIR / f"{stem}_character_memory_auto.json"
    glossary_path = ANALYSIS_DIR / f"{stem}_glossary_auto.json"

    save_json(json_path, data)
    save_report(report_path, data)
    save_statistics_csv(csv_path, data)
    save_character_memory(memory_path, data)
    save_glossary_auto(glossary_path, data)

    log(f"完成分析：{path.name}")
    log(f"  JSON：{json_path.name}")
    log(f"  Report：{report_path.name}")
    log(f"  CSV：{csv_path.name}")
    log(f"  Character Memory：{memory_path.name}")
    log(f"  Glossary Auto：{glossary_path.name}")


def main() -> None:
    ensure_dirs()

    log("NTPE Document Analyzer v1.0 啟動")

    files = list_input_files()

    if not files:
        log("output 資料夾內沒有 TXT 檔案")
        log(f"請先執行 Document Normalizer，或把要分析的 TXT 放到：{INPUT_DIR}")
        return

    log(f"找到 {len(files)} 個 TXT 檔")

    success = 0
    failed = 0

    for index, path in enumerate(files, start=1):
        log(f"[{index}/{len(files)}] 開始分析：{path.name}")

        try:
            analyze_file(path)
            success += 1
        except Exception as e:
            failed += 1
            log(f"失敗：{path.name}｜{e}")

    log("全部分析完成")
    log(f"成功：{success}")
    log(f"失敗：{failed}")
    log(f"輸出資料夾：{ANALYSIS_DIR}")


if __name__ == "__main__":
    main()
