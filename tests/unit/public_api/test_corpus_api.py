from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from ntpe.corpus import manage


ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "quality_corpus/golden_review/te_v71_initial_defects.json"
GOVERNANCE = ROOT / "artifacts/te_v71_stage116/TE_V71_STAGE116_GOLDEN_CORPUS_GOVERNANCE.json"


def test_corpus_view_reads_six_unapproved_cases_with_file_sha_parity() -> None:
    view = manage(corpus=CORPUS, governance_record=GOVERNANCE)
    assert len(view.cases) == 6
    assert view.approved_case_count == view.approved_translation_count == 0
    assert all(case.approved_final_translation is None for case in view.cases)
    assert view.content_sha256 == hashlib.sha256(CORPUS.read_bytes()).hexdigest()
    assert view.lifecycle_summary == (("under_review", 1),)


def test_manage_is_read_only_and_deterministic() -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    governance = json.loads(GOVERNANCE.read_text(encoding="utf-8"))
    before = copy.deepcopy((corpus, governance))
    first = manage(corpus=corpus, governance_record=governance)
    second = manage(corpus=corpus, governance_record=governance)
    assert first == second
    assert (corpus, governance) == before


def test_manage_exposes_no_mutating_method() -> None:
    view = manage(corpus=CORPUS, governance_record=GOVERNANCE)
    for name in ("approve", "reject", "supersede", "deprecate", "mutate", "save"):
        assert not hasattr(view, name)


def test_invalid_governance_record_fails_closed() -> None:
    governance = json.loads(GOVERNANCE.read_text(encoding="utf-8"))
    governance["current_corpus_summary"]["approved_cases"] = 1
    with pytest.raises(ValueError, match="unexpectedly approves"):
        manage(corpus=CORPUS, governance_record=governance)

