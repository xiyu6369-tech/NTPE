from __future__ import annotations

import json
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path

from core.adaptive_context_canary_ab import evaluate_canary_ab, load_stage_evidence

ROOT = Path(__file__).resolve().parents[2]
SANDBOX_ROOT = ROOT / ".ntpe_test_sandbox" / "stage075_canary_ab"


@contextmanager
def _project_sandbox():
    path = SANDBOX_ROOT / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
        try:
            SANDBOX_ROOT.rmdir()
            SANDBOX_ROOT.parent.rmdir()
        except OSError:
            pass


def _stage(
    root: Path,
    name: str,
    score: int,
    accepted: bool = True,
    issues=(),
    source_hash: str = "h",
) -> None:
    base = root / "tests/literary/outputs" / name / "Golden_Set"
    chunks = base / "original_ko_chunks"
    chunks.mkdir(parents=True)
    (base / "original_ko_resume_state.json").write_text(
        json.dumps(
            {
                "chunks": {
                    "000003": {
                        "status": "success" if accepted else "failed",
                        "source_hash": source_hash,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (chunks / "original_ko_chunk_000003_quality_v5_attempt_1.json").write_text(
        json.dumps(
            {
                "accepted": accepted,
                "status": "accepted" if accepted else "retry_required",
                "quality_score": score,
                "issues": list(issues),
                "metrics": {
                    "source_chars": 514,
                    "translated_chars": 360 if accepted else 250,
                    "source_paragraph_count": 4,
                    "translated_paragraph_count": 3 if accepted else 2,
                    "length_ratio": 0.65 if accepted else 0.45,
                },
            }
        ),
        encoding="utf-8",
    )


def test_stage_loader_and_pass():
    with _project_sandbox() as sandbox:
        _stage(sandbox, "base", 100)
        _stage(sandbox, "canary", 100)
        report = evaluate_canary_ab(
            load_stage_evidence(sandbox, "base", 3),
            load_stage_evidence(sandbox, "canary", 3),
        )
        assert report.ready


def test_omission_fails_closed():
    with _project_sandbox() as sandbox:
        _stage(sandbox, "base", 100)
        _stage(
            sandbox,
            "canary",
            80,
            False,
            ("PARAGRAPH_OMISSION_SUSPECTED",),
        )
        report = evaluate_canary_ab(
            load_stage_evidence(sandbox, "base", 3),
            load_stage_evidence(sandbox, "canary", 3),
        )
        assert not report.ready
        assert "new-omission-issue" in report.blockers
