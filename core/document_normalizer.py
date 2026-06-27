# =====================================================
# NTPE Document Normalizer v1.0
# 功能：
# 1. 自動偵測 TXT 編碼
# 2. 修復常見亂碼 / BOM / NUL
# 3. 繁簡統一為台灣繁體
# 4. 標點、空白、段落正規化
# 5. 保留原始檔備份
# 6. 批次處理 input/*.txt → output/*_normalized.txt
# =====================================================

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

import chardet

try:
    from opencc import OpenCC
    OPENCC_AVAILABLE = True
except Exception:
    OPENCC_AVAILABLE = False


ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "input"
OUTPUT_DIR = ROOT / "output"
BACKUP_DIR = ROOT / "backup"
LOG_DIR = ROOT / "logs"

SUPPORTED_EXT = ".txt"

ENCODING_CANDIDATES = [
    "utf-8-sig",
    "utf-8",
    "cp949",
    "euc-kr",
    "big5",
    "gb18030",
    "cp950",
]


def ensure_dirs() -> None:
    for folder in [INPUT_DIR, OUTPUT_DIR, BACKUP_DIR, LOG_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    ensure_dirs()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line)

    log_file = LOG_DIR / "normalizer_log.txt"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def read_bytes(path: Path) -> bytes:
    with path.open("rb") as f:
        return f.read()


def score_decoded_text(text: str) -> int:
    """
    分數越高代表越可能是正確解碼。
    """
    if not text:
        return -999999

    bad_chars = text.count("�")
    nul_chars = text.count("\x00")
    korean = len(re.findall(r"[\uac00-\ud7af]", text))
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    ascii_letters = len(re.findall(r"[A-Za-z]", text))
    punctuation = len(re.findall(r"[。！？…「」『』，、；：,.!?]", text))

    score = 0
    score -= bad_chars * 500
    score -= nul_chars * 500
    score += korean * 3
    score += chinese * 2
    score += punctuation
    score += min(ascii_letters, 300)

    # 過度控制字元通常表示解碼錯誤
    control_chars = len(re.findall(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", text))
    score -= control_chars * 100

    return score


def decode_text(data: bytes) -> tuple[str, str]:
    best_text = ""
    best_encoding = ""
    best_score = -999999

    for enc in ENCODING_CANDIDATES:
        try:
            text = data.decode(enc)
            score = score_decoded_text(text)
            if score > best_score:
                best_text = text
                best_encoding = enc
                best_score = score
        except Exception:
            continue

    detected = chardet.detect(data)
    detected_enc = detected.get("encoding")

    if detected_enc:
        try:
            text = data.decode(detected_enc, errors="replace")
            score = score_decoded_text(text)
            if score > best_score:
                best_text = text
                best_encoding = detected_enc
                best_score = score
        except Exception:
            pass

    if not best_text:
        best_text = data.decode("utf-8", errors="replace")
        best_encoding = "utf-8-replace"

    return best_text, best_encoding


def remove_bom_and_null(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\x00", "")
    return text


def normalize_linebreaks(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def normalize_spaces(text: str) -> str:
    # 全形空白轉半形空白
    text = text.replace("\u3000", " ")

    # 行首行尾空白清掉
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # 同一行多空白壓成一格，但不破壞換行
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text


def normalize_punctuation(text: str) -> str:
    replacements = {
        "“": "「",
        "”": "」",
        "‘": "『",
        "’": "』",
        "﹁": "「",
        "﹂": "」",
        "﹃": "『",
        "﹄": "』",
        "（": "（",
        "）": "）",
        "… …": "……",
        "......": "……",
        "。。。": "……",
    }

    for src, dst in replacements.items():
        text = text.replace(src, dst)

    # 英文逗號句號在中文旁邊時轉中文標點
    text = re.sub(r"(?<=[\u4e00-\u9fff]),", "，", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\.", "。", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff]);", "；", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff]):", "：", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\?", "？", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])!", "！", text)

    # 重複標點收斂
    text = re.sub(r"。{2,}", "……", text)
    text = re.sub(r"，{2,}", "，", text)
    text = re.sub(r"！{2,}", "！", text)
    text = re.sub(r"？{2,}", "？", text)
    text = re.sub(r"…{3,}", "……", text)

    return text


def normalize_paragraphs(text: str) -> str:
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        line = line.strip()
        cleaned.append(line)

    text = "\n".join(cleaned)

    # 三個以上空行壓成兩個
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 檔案頭尾空白
    text = text.strip() + "\n"

    return text


def convert_to_tw_traditional(text: str) -> str:
    if not OPENCC_AVAILABLE:
        return text

    try:
        cc = OpenCC("s2twp")
        return cc.convert(text)
    except Exception:
        return text


def fix_common_mojibake(text: str) -> str:
    """
    v1.0 只做安全修復，不做高風險猜測式改寫。
    """
    replacements = {
        "Ã¢â‚¬Â¦": "……",
        "â€¦": "……",
        "â€”": "——",
        "â€“": "—",
        "ï¼Œ": "，",
        "ï¼š": "：",
        "ï¼›": "；",
        "ï¼ˆ": "（",
        "ï¼‰": "）",
        "ï¼Ÿ": "？",
        "ï¼": "！",
    }

    for src, dst in replacements.items():
        text = text.replace(src, dst)

    return text


def normalize_text(text: str) -> str:
    text = remove_bom_and_null(text)
    text = normalize_linebreaks(text)
    text = fix_common_mojibake(text)
    text = convert_to_tw_traditional(text)
    text = normalize_punctuation(text)
    text = normalize_spaces(text)
    text = normalize_paragraphs(text)
    return text


def backup_file(src: Path) -> Path:
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / f"{src.stem}_{timestamp}{src.suffix}"
    shutil.copy2(src, dst)
    return dst


def normalize_file(path: Path) -> Path:
    data = read_bytes(path)
    text, encoding = decode_text(data)
    normalized = normalize_text(text)

    backup_path = backup_file(path)

    output_name = f"{path.stem}_normalized.txt"
    output_path = OUTPUT_DIR / output_name

    with output_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(normalized)

    original_len = len(text)
    final_len = len(normalized)

    log(f"完成：{path.name}")
    log(f"  偵測編碼：{encoding}")
    log(f"  原文字數：{original_len}")
    log(f"  輸出字數：{final_len}")
    log(f"  備份：{backup_path.name}")
    log(f"  輸出：{output_path.name}")

    return output_path


def list_input_files() -> list[Path]:
    ensure_dirs()
    return sorted(
        [p for p in INPUT_DIR.iterdir() if p.is_file() and p.suffix.lower() == SUPPORTED_EXT],
        key=lambda p: p.name.lower(),
    )


def main() -> None:
    ensure_dirs()

    log("NTPE Document Normalizer v1.0 啟動")

    files = list_input_files()

    if not files:
        log("input 資料夾內沒有 TXT 檔案")
        log(f"請把要整理的 .txt 放到：{INPUT_DIR}")
        return

    log(f"找到 {len(files)} 個 TXT 檔")

    success = 0
    failed = 0

    for index, path in enumerate(files, start=1):
        log(f"[{index}/{len(files)}] 開始處理：{path.name}")

        try:
            normalize_file(path)
            success += 1
        except Exception as e:
            failed += 1
            log(f"失敗：{path.name}｜{e}")

    log("全部處理完成")
    log(f"成功：{success}")
    log(f"失敗：{failed}")
    log(f"輸出資料夾：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
