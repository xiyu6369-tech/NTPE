# NTPE S7-07 — Literary Quality Contract v1 Design Report

**Design Date**: 2026-09-30
**Auditor**: Kilo (Automated)
**Scope**: Literary Quality Contract v1 Design per S7-07 mandate

---

## 1. Baseline

| Metric | Value |
|--------|-------|
| HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` ✓ |
| Branch | `main` ✓ |
| S7-06 Input Report | `artifacts/NTPE_S7_06_LITERARY_QUALITY_CONTRACT_AUDIT_REPORT.md` |
| S7-06 Verdict | `S7_06_QUALITY_CONTRACT_DEFINED_WITH_UNDEFINED_AREAS` |

### Working Tree (Pre-existing, Untouched)

| Category | Count |
|----------|-------|
| Modified (literary outputs) | 4 |
| Untracked (artifacts) | 25+ |

---

## 2. S7-06 Input Consumption

**S7-06 Audit Report**: Consumed ✅
**Key Findings from S7-06**:
- 9 deterministic production gates identified and verified
- Literary Naturalness / PS-03 / Best Attempt / Segment Recovery / Context Continuity / Reviewer-Editor-ACE all classified as non-production
- Retry boundary locked (S7-03)
- Model/Provider frozen

---

## 3. Files Inspected (Phase A Audit)

### Quality Runtime Core
- `core/translation_quality_v5/quality_baseline.py` — Fidelity/completeness checks
- `core/translation_quality_v5/completeness_guard.py` — Omission/duplicate detection
- `core/translation_quality_v5/terminology_guard.py` — Locked terms, forbidden variants
- `core/translation_quality_v5/quality_core_pipeline.py` — Orchestrates baseline/completeness/terminology/normalization
- `core/translation_quality_v5/quality_repair_pipeline.py` — Chains quality → repair → retry → rebuild

### Quality Gates & Decisions
- `core/translation_quality_v5/quality_runtime_gate_contract.py` — Gate contract (disabled by default)
- `core/translation_quality_v5/quality_runtime_gate_decision.py` — Gate decision logic
- `core/translation_quality_v5/unified_quality_gate.py` — Merges v5 + legacy QA, enforces discipline
- `core/translation_quality_v5/quality_decision.py` — Gate state machine (`accepted`/`accepted_with_warnings`/`retry_required`/`rejected`)
- `core/translation_quality_v5/quality_issue.py` — Severity normalization, canonical codes

### Discipline & Retry
- `core/translation_discipline/quality_enforcement.py` — Routes issues: local_repair / provider_retry / warning
- `core/translation_discipline/quality_adapter.py` — Maps issue codes to discipline rules
- `core/translation_reliability/adaptive_retry_policy.py` — Retry decisions, chunk halving, provider switch

### Advanced Features
- `core/translation_quality_v5/best_attempt.py` — `select_best_attempt()` (NOT connected to production)
- `core/translation_quality_v5/segment_recovery.py` — Segment splitting (env-gated, NOT connected)
- `core/adapters/production_submission_adapter.py` — `quality_context_scene_v72=False` default
- `core/translation_engine/translation_engine.py` — TQI V72 flags from metadata

### Literary Evaluation (Tooling Only)
- `ntpe_literary_evaluation.py` — PS-03 100-point evaluation (post-hoc only)

### ACE / Reviewer / Editor
- `tests/integration/translation_engine_v700_stage0*_ace_*.py` — ACE tests only (mode disabled/shadow/active)

---

## 4. Contract Design Summary (Phase B)

### Deterministic Production Gates (9 HARD_GATES + 1 LOCAL_REPAIR)

| # | Dimension | Gate | Threshold | Action |
|---|-----------|------|-----------|--------|
| 1 | Empty Output | HARD | Zero tolerance | Provider retry |
| 2 | Length Ratio | HARD | `min_length_ratio=0.35` / `0.18` (LTS) | Provider retry |
| 3 | Paragraph Omission | HARD | Corroborated ratio < 0.5 | Provider retry |
| 4 | Sentence Omission | HARD | Ratio < 0.5 | Provider retry |
| 5 | Duplicate Paragraphs | HARD | `max_duplicate_paragraphs=0` | Provider retry |
| 6 | Duplicate Lines | HARD | `max_duplicate_lines=1` | Provider retry |
| 7 | Locked Terms Missing | HARD | Zero missing | Local repair → retry |
| 8 | Forbidden Variants | HARD | Zero wrong variants | Local repair |
| 9 | Full-name Over-expansion | HARD | Zero over-expansion | Local repair |
| 10 | Simplified Chinese | HARD | Zero tolerance | Local repair (conversion) |
| 11 | Dialogue Quote Format | LOCAL_REPAIR | Convert to `「」` | Local repair |
| 12 | Paragraph Count | HARD | Ratio ≥ 0.5 (corroborated) | Provider retry |
| 13 | Sentence Count | HARD | Ratio ≥ 0.5 | Provider retry |
| 14 | Character Consistency | HARD | Via locked terms + memory | Local repair |

### Gate State Machine

| State | Condition | Retry |
|-------|-----------|-------|
| `accepted` | All HARD_GATE pass | No |
| `accepted_with_warnings` | HARD_GATE pass; only low/medium non-retry | No |
| `retry_required` | Any critical/high OR `retry_required=true` | **Yes** |
| `rejected` | `rejected=true` (hallucination, added_detail) | No |

### Severity Contract

| Severity | Codes | Gate Effect | Retry |
|----------|-------|-------------|-------|
| `critical` | empty_output, too_short, hangul_residue | Blocks accepted | Yes |
| `high` | duplicate_paragraph, locked_term_missing, omission_suspected | Blocks accepted | Yes |
| `medium` | duplicate_line, paragraph_structure_merged (non-corroborated) | Warning | No |
| `low`/`info` | dialogue_quote_format | Warning | No |

---

## 5. Explicitly Bounded Non-Production Areas

| Area | Classification | Rationale |
|------|----------------|-----------|
| **Literary Naturalness** | OBSERVATIONAL_ONLY | PS-03 proxy (20pts); no calibration; no human correlation |
| **PS-03 Aggregate Score** | OBSERVATIONAL_ONLY | 100pt with arbitrary weights (30/20/20/15/10/5); thresholds 80/65 uncalibrated |
| **Best Attempt Selection** | NOT_IMPLEMENTED | Function exists (`best_attempt.py`) but **zero call sites** in production; cross-attempt score comparability undefined |
| **Segment Recovery Quality Merge** | NOT_IMPLEMENTED | Env-gated (`NTPE_SEGMENT_COMPLETENESS_RECOVERY`) but **zero call sites**; no merge strategy, no cross-segment consistency |
| **Context Continuity** | FEATURE_GATED_OFF | `quality_context_scene_v72=False` default in `production_submission_adapter.py:38` |
| **Literary Reviewer** | NOT_IMPLEMENTED | Zero repository evidence |
| **Literary Editor** | NOT_IMPLEMENTED | Zero repository evidence |
| **ACE** | TEST_ONLY | Tests only (`mode='disabled'|'shadow'|'active'`); no production path |

---

## 6. Retry Boundary Verification (LOCKED)

| Rule | Value | Status |
|------|-------|--------|
| Max Attempts | 5 | LOCKED |
| Provider Switch | After attempt 3 for 429/503/exhausted | LOCKED |
| Quality Retry Chunk Halving | empty_output, too_short, hangul_residue, read_timeout | LOCKED |
| No Real Translation in Decision | `provider_called=false`, `http_called=false`, `api_key_accessed=false` | LOCKED |

**No modifications made to retry boundary.**

---

## 7. Production Reachability Verification

| Component | Reachability | Evidence |
|-----------|--------------|----------|
| All 14 production gates | YES | Called in `TranslationQualityCorePipeline` → `QualityRepairPipeline` |
| Gate State Machine | YES | `run_unified_quality_gate()` in LTS pipeline |
| Discipline Routing | YES | `DisciplineQualityEnforcer.enforce()` |
| Adaptive Retry Policy | YES | `QualityRetryOrchestrator` |
| Literary Naturalness (PS-03) | NO | Post-hoc tooling only (`ntpe_literary_evaluation.py`) |
| PS-03 Aggregate | NO | Post-hoc tooling only |
| Best Attempt | NO | Function exists, **0 call sites** |
| Segment Recovery Merge | NO | Env-gated, **0 call sites** |
| Context Continuity | CONDITIONAL | Feature flag default `False` |
| ACE / Reviewer / Editor | NO | Test-only / not implemented |

---

## 8. Validation Results

### Regression Tests (All Pass)

| Suite | Collected | Passed | Failed |
|-------|-----------|--------|--------|
| S6-02 TXT Success/Failure | 6 | 6 | 0 |
| S6-03 EPUB Success/Failure/Thread/Canonical/Output | 7 | 7 | 0 |
| S6-04 Validation | 16 | 16 | 0 |
| S6-05 Dry-Run | 8 | 8 | 0 |
| **Total** | **37** | **37** | **0** |

### Static Validation

| Check | Result |
|-------|--------|
| `python -m compileall ui/translation_studio -q` | ✅ PASS |
| `git diff --check` | ✅ PASS (only CRLF warnings on pre-existing files) |

### Production Safety

| Metric | Value |
|--------|-------|
| Real Translation Execution | 0 |
| Provider Execution | 0 |
| Network Execution | 0 |
| Production Files Modified | 0 |
| Model Changed | NO (`meta/llama-3.2-90b-vision-instruct`) |
| Provider Changed | NO (`nvidia`) |

---

## 9. Artifacts Produced

| Artifact | Path |
|----------|------|
| Quality Contract v1 | `artifacts/NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1.md` |
| Design Report | `artifacts/NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1_REPORT.md` |

---

## 10. Working Tree Safety

| Check | Status |
|-------|--------|
| Pre-existing modifications preserved | ✅ 4 literary output files unchanged |
| Historical artifacts preserved | ✅ 25+ untracked artifacts untouched |
| No root scratch files created | ✅ |
| No unexpected root artifacts | ✅ |

---

## 11. Final Verdict

```
S7_07_QUALITY_CONTRACT_V1_DEFINED_WITH_EXPLICIT_BOUNDARIES
```

### Summary

**Contract Defined For** (deterministic, production-integrated):
- 14 deterministic production gates (13 HARD_GATE + 1 LOCAL_REPAIR)
- Gate State Machine (4 states)
- Severity Contract (4 levels)
- Retry Boundary (LOCKED from S7-03/S7-06)

**Explicitly Bounded as Non-Production**:
- Literary Naturalness → OBSERVATIONAL_ONLY
- PS-03 Aggregate → OBSERVATIONAL_ONLY
- Best Attempt Selection → NOT_IMPLEMENTED
- Segment Recovery Quality Merge → NOT_IMPLEMENTED
- Context Continuity → FEATURE_GATED_OFF
- Literary Reviewer/Editor/ACE → TEST_ONLY / NOT_IMPLEMENTED

**No Production Defects Found**. No arbitrary thresholds introduced. No unauthorized capability claims. All existing production contracts preserved.

---

*End of Report*

**Report Path**: `artifacts/NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1_REPORT.md`
**Design Complete**: `S7_07_QUALITY_CONTRACT_V1_DEFINED_WITH_EXPLICIT_BOUNDARIES`