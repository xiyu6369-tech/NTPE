# =====================================================
# NTPE 1.2 Production Stabilization — PS-02
# Literary Regression Runner
# =====================================================
from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json
from core.translation_runtime import TranslationRuntime
from lts.txt_translation_runtime import TxtTranslationOptions

LITERARY_ROOT = Path("tests") / "literary"
DEFAULT_TEST_SETS = ("Test_Set_0", "Test_Set_A", "Test_Set_B")
DEFAULT_SOURCE_NAME = "original_ko.txt"
DEFAULT_STAGE_NAME = "PS-02"


@dataclass(frozen=True)
class LiteraryRegressionOptions:
    root: Path
    test_sets: tuple[str, ...] = DEFAULT_TEST_SETS
    stage_name: str = DEFAULT_STAGE_NAME
    profile: str = "literary"
    chunk_size: int = 1000
    model: str = "meta/llama-3.3-70b-instruct"
    dry_run: bool = False
    overwrite: bool = False
    max_retries: int = 3
    retry_base_seconds: float = 5.0
    qa_fail_policy: str = "retry"
    simplified_chinese_policy: str = "normalize"


def _safe_stage_name(stage_name: str) -> str:
    cleaned = "".join(ch for ch in (stage_name or DEFAULT_STAGE_NAME).strip() if ch.isalnum() or ch in "-_.")
    return cleaned or DEFAULT_STAGE_NAME


def literary_root(root: Path) -> Path:
    return root / LITERARY_ROOT


def ensure_literary_structure(root: Path) -> dict:
    base = literary_root(root)
    created: list[str] = []
    for rel in [
        Path("Test_Set_0"),
        Path("Test_Set_A"),
        Path("Test_Set_B"),
        Path("outputs"),
    ]:
        path = base / rel
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
    readme = base / "README.md"
    if not readme.exists():
        readme.write_text(
            "# NTPE Literary Regression Corpus\n\n"
            "Use Test_Set_0 for smoke checks, Test_Set_A as the stable golden corpus, "
            "and Test_Set_B as a rotating regression corpus.\n",
            encoding="utf-8",
        )
        created.append(str(readme))
    return {"status": "success", "literary_root": str(base), "created": created}


def discover_test_sets(root: Path, requested: Iterable[str] | None = None) -> list[dict]:
    base = literary_root(root)
    names = tuple(requested or DEFAULT_TEST_SETS)
    sets: list[dict] = []
    for name in names:
        source = base / name / DEFAULT_SOURCE_NAME
        sets.append({
            "name": name,
            "path": str(base / name),
            "source": str(source),
            "exists": source.exists(),
            "has_content": source.exists() and bool(source.read_text(encoding="utf-8-sig", errors="ignore").strip()),
        })
    return sets


def _copy_reference_files(test_dir: Path, stage_output_dir: Path) -> None:
    for filename in (DEFAULT_SOURCE_NAME, "reference_notes.md", "evaluation.md", "README.md"):
        src = test_dir / filename
        if src.exists():
            shutil.copy2(src, stage_output_dir / filename)


def run_literary_regression(options: LiteraryRegressionOptions) -> dict:
    root = options.root.resolve()
    ensure_literary_structure(root)
    stage_name = _safe_stage_name(options.stage_name)
    base = literary_root(root)
    output_base = base / "outputs" / stage_name
    if output_base.exists() and options.overwrite:
        shutil.rmtree(output_base)
    output_base.mkdir(parents=True, exist_ok=True)

    runtime = TranslationRuntime(root=root)
    started = time.time()
    records: list[dict] = []

    for test in discover_test_sets(root, options.test_sets):
        name = test["name"]
        test_dir = base / name
        stage_output_dir = output_base / name
        stage_output_dir.mkdir(parents=True, exist_ok=True)
        record = dict(test)
        record["output_dir"] = str(stage_output_dir)
        record["started_at"] = now_iso()

        if not test["exists"]:
            record.update({"status": "skipped", "reason": f"missing {DEFAULT_SOURCE_NAME}", "completed_at": now_iso()})
            records.append(record)
            continue
        if not test["has_content"]:
            record.update({"status": "skipped", "reason": f"empty {DEFAULT_SOURCE_NAME}", "completed_at": now_iso()})
            records.append(record)
            continue

        _copy_reference_files(test_dir, stage_output_dir)
        txt_options = TxtTranslationOptions(
            input_path=Path(test["source"]),
            output_dir=stage_output_dir,
            chunk_size=max(300, int(options.chunk_size)),
            model=options.model,
            resume=False,
            dry_run=options.dry_run,
            max_retries=max(0, int(options.max_retries)),
            retry_base_seconds=max(0.0, float(options.retry_base_seconds)),
            qa_fail_policy=options.qa_fail_policy,
            quality_profile=options.profile,
            simplified_chinese_policy=options.simplified_chinese_policy,
        )
        try:
            result = runtime.translate_txt(txt_options)
            record.update({
                "status": result.get("status", "unknown"),
                "chunk_total": result.get("chunk_total", 0),
                "output": result.get("output", ""),
                "manifest": str(stage_output_dir / "original_ko_translation_manifest.json"),
                "completed_at": now_iso(),
            })
            if result.get("status") != "success":
                record["error"] = result.get("error", "regression translation did not succeed")
        except Exception as exc:
            record.update({"status": "failed", "error": str(exc), "completed_at": now_iso()})
        records.append(record)

    summary = {
        "total": len(records),
        "success": sum(1 for item in records if item.get("status") == "success"),
        "skipped": sum(1 for item in records if item.get("status") == "skipped"),
        "failed": sum(1 for item in records if item.get("status") not in ("success", "skipped")),
        "dry_run": options.dry_run,
        "elapsed_seconds": round(time.time() - started, 3),
    }
    report = {
        "version": "1.2-ps-02-literary-regression-runner",
        "status": "success" if summary["failed"] == 0 else "failed",
        "stage": stage_name,
        "profile": options.profile,
        "created_at": now_iso(),
        "literary_root": str(base),
        "output_dir": str(output_base),
        "summary": summary,
        "records": records,
    }
    save_json(output_base / "Literary_Regression_Report.json", report)
    _write_markdown_report(output_base / "Literary_Regression_Report.md", report)
    return report


def _write_markdown_report(path: Path, report: dict) -> None:
    lines = [
        f"# NTPE Literary Regression Report — {report.get('stage')}",
        "",
        f"- Status: {report.get('status')}",
        f"- Profile: {report.get('profile')}",
        f"- Output: `{report.get('output_dir')}`",
        "",
        "| Test Set | Status | Chunks | Output | Notes |",
        "|---|---|---:|---|---|",
    ]
    for record in report.get("records", []):
        note = record.get("error") or record.get("reason") or ""
        lines.append(
            f"| {record.get('name')} | {record.get('status')} | {record.get('chunk_total', 0)} | `{record.get('output', '')}` | {note} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    opts = LiteraryRegressionOptions(root=Path.cwd(), dry_run=True)
    print(json.dumps(run_literary_regression(opts), ensure_ascii=False, indent=2))
