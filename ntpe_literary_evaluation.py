# =====================================================
# NTPE 1.2 Production Stabilization — PS-03
# Translation Corpus Evaluation Engine
# =====================================================
from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from core.translation_engine.utils import now_iso, save_json
except Exception:  # pragma: no cover
    from datetime import datetime

    def now_iso() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def save_json(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

LITERARY_ROOT = Path("tests") / "literary"
OUTPUT_NAME = "original_ko_zh.txt"
REPORT_JSON = "Literary_Quality_Report.json"
REPORT_MD = "Literary_Quality_Report.md"
DIFF_MD = "Literary_Diff_Report.md"
HISTORY_JSON = "Regression_History.json"
HISTORY_MD = "Regression_History.md"

LOCKED_TERMS = {
    "정태의": "鄭泰義",
    "카일": "凱爾",
    "일라이": "伊萊",
    "리그로우": "里格勞",
}

WRONG_NAME_VARIANTS = {
    "定泰義": "鄭泰義",
    "正太義": "鄭泰義",
    "鄭太義": "鄭泰義",
    "郑泰义": "鄭泰義",
}

SIMPLIFIED_HINTS = set("这为来时说过后还个们对会无发车门见气头间里国与吗从给让边长");
KOREAN_RE = re.compile(r"[\uac00-\ud7a3]")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


@dataclass(frozen=True)
class QualityMetric:
    name: str
    score: float
    max_score: float
    status: str
    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "score": round(self.score, 2),
            "max_score": self.max_score,
            "status": self.status,
            "notes": self.notes,
        }


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def _ratio(a: int, b: int) -> float:
    return 0.0 if b <= 0 else a / b


def _score_status(score: float, max_score: float, warn_ratio: float = 0.75) -> str:
    if score >= max_score * 0.9:
        return "PASS"
    if score >= max_score * warn_ratio:
        return "WARN"
    return "FAIL"


def evaluate_translation_text(source: str, translated: str) -> dict:
    source = source or ""
    translated = translated or ""
    metrics: list[QualityMetric] = []

    # 1. Plot / coverage proxy: translated text should not be empty or absurdly short.
    src_cjk = len(KOREAN_RE.findall(source)) or len(CJK_RE.findall(source)) or len(source.strip())
    zh_chars = len(CJK_RE.findall(translated))
    length_ratio = _ratio(zh_chars, max(1, src_cjk))
    if not translated.strip():
        coverage = 0.0
        coverage_note = "missing output"
    elif length_ratio < 0.18:
        coverage = 8.0
        coverage_note = f"very short translation ratio={length_ratio:.2f}"
    elif length_ratio < 0.35:
        coverage = 20.0
        coverage_note = f"short translation ratio={length_ratio:.2f}"
    else:
        coverage = 30.0
        coverage_note = f"length ratio={length_ratio:.2f}"
    metrics.append(QualityMetric("plot_fidelity_proxy", coverage, 30.0, _score_status(coverage, 30.0), coverage_note))

    # 2. Locked names and term consistency.
    required_terms = {ko: zh for ko, zh in LOCKED_TERMS.items() if ko in source}
    missing_locked = [f"{ko}->{zh}" for ko, zh in required_terms.items() if zh not in translated]
    wrong_hits = [wrong for wrong in WRONG_NAME_VARIANTS if wrong in translated]
    korean_name_residue = [ko for ko in required_terms if ko in translated]
    locked_score = 20.0
    if missing_locked:
        locked_score -= min(12.0, 6.0 * len(missing_locked))
    if wrong_hits:
        locked_score -= min(10.0, 5.0 * len(wrong_hits))
    if korean_name_residue:
        locked_score -= min(8.0, 4.0 * len(korean_name_residue))
    locked_score = max(0.0, locked_score)
    locked_notes = []
    if missing_locked:
        locked_notes.append("missing locked terms: " + ", ".join(missing_locked))
    if wrong_hits:
        locked_notes.append("wrong variants: " + ", ".join(wrong_hits))
    if korean_name_residue:
        locked_notes.append("source name residue: " + ", ".join(korean_name_residue))
    metrics.append(QualityMetric("locked_names_terms", locked_score, 20.0, _score_status(locked_score, 20.0), "; ".join(locked_notes) or "ok"))

    # 3. Natural Chinese proxy: enough Chinese, not dominated by Korean/ASCII, avoids common machine prefaces.
    korean_hits = len(KOREAN_RE.findall(translated))
    preface_penalty = 5.0 if any(p in translated[:120] for p in ("以下", "翻譯如下", "以下是")) else 0.0
    korean_penalty = min(12.0, korean_hits * 1.5)
    chinese_density = _ratio(zh_chars, max(1, len(translated.strip())))
    density_penalty = 0.0 if chinese_density >= 0.45 else 6.0
    natural_score = max(0.0, 20.0 - korean_penalty - preface_penalty - density_penalty)
    natural_note = f"korean_hits={korean_hits}, chinese_density={chinese_density:.2f}"
    metrics.append(QualityMetric("natural_chinese_proxy", natural_score, 20.0, _score_status(natural_score, 20.0), natural_note))

    # 4. Subject/pronoun proxy: cannot truly infer, but flags risky repeated demonstratives and known Passion Kyle mistake.
    risky = translated.count("那個") + translated.count("這個")
    kyle_wrong = "鄭泰義堅持" in translated and "카일" in source and "주장" in source
    subject_score = 15.0 - min(5.0, risky * 0.8) - (8.0 if kyle_wrong else 0.0)
    subject_score = max(0.0, subject_score)
    subject_note = f"demonstrative_repetition={risky}" + ("; possible Kyle/Jeong subject confusion" if kyle_wrong else "")
    metrics.append(QualityMetric("subject_pronoun_proxy", subject_score, 15.0, _score_status(subject_score, 15.0), subject_note))

    # 5. Character voice / dialogue proxy: dialogue punctuation preserved when dialogue exists.
    source_dialogue_count = source.count('"') + source.count("“") + source.count("‘")
    zh_dialogue_count = translated.count("「") + translated.count("」")
    if source_dialogue_count == 0:
        voice_score = 10.0
        voice_note = "no dialogue in source"
    elif zh_dialogue_count >= 2:
        voice_score = 10.0
        voice_note = "dialogue punctuation present"
    else:
        voice_score = 4.0
        voice_note = "dialogue punctuation may be missing"
    metrics.append(QualityMetric("character_voice_dialogue_proxy", voice_score, 10.0, _score_status(voice_score, 10.0), voice_note))

    # 6. Format / punctuation / simplified residue.
    simplified_hits = sorted(ch for ch in set(translated) if ch in SIMPLIFIED_HINTS)
    simplified_penalty = min(4.0, len(simplified_hits) * 0.5)
    format_score = max(0.0, 5.0 - simplified_penalty)
    format_note = "simplified_hints=" + ("".join(simplified_hits) if simplified_hits else "0")
    metrics.append(QualityMetric("format_punctuation", format_score, 5.0, _score_status(format_score, 5.0, warn_ratio=0.65), format_note))

    total = round(sum(m.score for m in metrics), 2)
    status = "success" if total >= 80 else "warning" if total >= 65 else "failed"
    return {
        "status": status,
        "overall_score": total,
        "max_score": 100,
        "metrics": [m.as_dict() for m in metrics],
        "raw": {
            "source_chars": len(source),
            "translation_chars": len(translated),
            "source_korean_chars": src_cjk,
            "translation_cjk_chars": zh_chars,
            "length_ratio": round(length_ratio, 3),
            "korean_residue_count": korean_hits,
            "simplified_hint_count": len(simplified_hits),
        },
    }


def _find_previous_stage(outputs_root: Path, stage: str) -> str | None:
    if not outputs_root.exists():
        return None
    candidates = [p.name for p in outputs_root.iterdir() if p.is_dir() and p.name != stage]
    if not candidates:
        return None
    return sorted(candidates)[-1]


def _write_diff_report(path: Path, root: Path, stage: str, previous_stage: str | None, test_sets: Iterable[str]) -> None:
    outputs = root / LITERARY_ROOT / "outputs"
    lines = [f"# NTPE Literary Diff Report — {stage}", ""]
    if not previous_stage:
        lines.append("No previous stage was found or specified.")
        path.write_text("\n".join(lines), encoding="utf-8")
        return
    lines.append(f"Previous Stage: `{previous_stage}`")
    lines.append("")
    for name in test_sets:
        prev = outputs / previous_stage / name / OUTPUT_NAME
        curr = outputs / stage / name / OUTPUT_NAME
        lines.append(f"## {name}")
        if not prev.exists() or not curr.exists():
            lines.append("Diff skipped because one side is missing.")
            lines.append("")
            continue
        prev_lines = prev.read_text(encoding="utf-8", errors="ignore").splitlines()
        curr_lines = curr.read_text(encoding="utf-8", errors="ignore").splitlines()
        diff = list(difflib.unified_diff(prev_lines, curr_lines, fromfile=previous_stage, tofile=stage, lineterm=""))
        if not diff:
            lines.append("No textual diff.")
        else:
            lines.append("```diff")
            lines.extend(diff[:240])
            if len(diff) > 240:
                lines.append("... diff truncated ...")
            lines.append("```")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def evaluate_stage_outputs(root: Path, stage: str, previous_stage: str | None = None) -> dict:
    root = root.resolve()
    base = root / LITERARY_ROOT
    output_dir = base / "outputs" / stage
    output_dir.mkdir(parents=True, exist_ok=True)
    test_sets = ["Test_Set_0", "Test_Set_A", "Test_Set_B"]
    records: list[dict] = []
    for name in test_sets:
        source = base / name / "original_ko.txt"
        output = output_dir / name / OUTPUT_NAME
        source_text = _read_text(source)
        translated_text = _read_text(output)
        evaluation = evaluate_translation_text(source_text, translated_text)
        records.append({
            "name": name,
            "source": str(source),
            "output": str(output),
            "exists": output.exists(),
            "evaluation": evaluation,
        })
    scored = [r["evaluation"]["overall_score"] for r in records if r["exists"]]
    overall = round(sum(scored) / len(scored), 2) if scored else 0.0
    status = "success" if scored and overall >= 80 else "warning" if scored and overall >= 65 else "failed"
    report_json = output_dir / REPORT_JSON
    report_md = output_dir / REPORT_MD
    diff_md = output_dir / DIFF_MD
    prev = previous_stage or _find_previous_stage(base / "outputs", stage)
    report = {
        "version": "1.2-ps-03-translation-corpus-evaluation-engine",
        "status": status,
        "stage": stage,
        "created_at": now_iso(),
        "output_dir": str(output_dir),
        "report_json": str(report_json),
        "report_md": str(report_md),
        "diff_md": str(diff_md),
        "previous_stage": prev,
        "summary": {
            "total": len(records),
            "existing_outputs": sum(1 for r in records if r["exists"]),
            "overall_score": overall,
        },
        "records": records,
    }
    save_json(report_json, report)
    _write_quality_markdown(report_md, report)
    _write_diff_report(diff_md, root, stage, prev, test_sets)
    _update_history(base / "outputs", report)
    return report


def _write_quality_markdown(path: Path, report: dict) -> None:
    lines = [
        f"# NTPE Literary Quality Report — {report.get('stage')}",
        "",
        f"- Status: {report.get('status')}",
        f"- Overall Score: {report.get('summary', {}).get('overall_score', 0)}/100",
        f"- Previous Stage: `{report.get('previous_stage') or ''}`",
        "",
        "| Test Set | Exists | Score | Status | Key Notes |",
        "|---|---|---:|---|---|",
    ]
    for record in report.get("records", []):
        ev = record.get("evaluation", {})
        notes = []
        for metric in ev.get("metrics", []):
            if metric.get("status") != "PASS" or metric.get("notes") not in ("ok", ""):
                notes.append(f"{metric.get('name')}: {metric.get('notes')}")
        lines.append(
            f"| {record.get('name')} | {record.get('exists')} | {ev.get('overall_score', 0)} | {ev.get('status')} | {'; '.join(notes)[:300]} |"
        )
    lines.append("")
    lines.append("## Metric Detail")
    lines.append("")
    for record in report.get("records", []):
        lines.append(f"### {record.get('name')}")
        lines.append("")
        lines.append("| Metric | Score | Max | Status | Notes |")
        lines.append("|---|---:|---:|---|---|")
        for metric in record.get("evaluation", {}).get("metrics", []):
            lines.append(f"| {metric.get('name')} | {metric.get('score')} | {metric.get('max_score')} | {metric.get('status')} | {metric.get('notes')} |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _update_history(outputs_root: Path, report: dict) -> None:
    hist_json = outputs_root / HISTORY_JSON
    hist_md = outputs_root / HISTORY_MD
    if hist_json.exists():
        try:
            history = json.loads(hist_json.read_text(encoding="utf-8"))
        except Exception:
            history = {"records": []}
    else:
        history = {"records": []}
    stage = report.get("stage")
    history["records"] = [r for r in history.get("records", []) if r.get("stage") != stage]
    history["records"].append({
        "stage": stage,
        "created_at": report.get("created_at"),
        "status": report.get("status"),
        "overall_score": report.get("summary", {}).get("overall_score", 0),
        "report_md": report.get("report_md"),
    })
    history["records"] = sorted(history["records"], key=lambda r: r.get("created_at", ""))
    save_json(hist_json, history)
    lines = ["# NTPE Literary Regression History", "", "| Stage | Score | Status | Report |", "|---|---:|---|---|"]
    for item in history.get("records", []):
        lines.append(f"| {item.get('stage')} | {item.get('overall_score')} | {item.get('status')} | `{item.get('report_md')}` |")
    hist_md.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    result = evaluate_stage_outputs(Path.cwd(), "PS-03")
    print(json.dumps(result, ensure_ascii=False, indent=2))
