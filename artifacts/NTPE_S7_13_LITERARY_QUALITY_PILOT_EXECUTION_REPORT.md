# NTPE S7-13 Literary Quality Pilot Execution Report

**Task**: `S7-13 Literary Quality Pilot Execution`
**Date**: 2026-09-30
**Executor**: Kilo (Automated)
**Status**: `PILOT_BLOCKED — NOT EXECUTED (NO REAL EVALUATORS)`

---

## 1. Baseline

| Metric | Value |
|--------|-------|
| Actual HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` |
| Branch | `main` |
| Upstream | `origin/main` (tracking; not modified) |
| Origin | `https://github.com/xiyu6369-tech/NTPE.git` |
| Working Tree | 4 pre-existing modified (literary outputs), 1 pre-existing deletion, 25+ pre-existing untracked artifacts — all preserved |

No destructive git operation was performed. Pre-existing changes preserved (S7-13 §77).

---

## 2. Input Design Versions

| Artifact | Path | Status |
|----------|------|--------|
| S7-07 Contract | `artifacts/NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1.md` | CONSUMED |
| S7-07 Report | `artifacts/NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1_REPORT.md` | CONSUMED |
| S7-08 Audit | `artifacts/NTPE_S7_08_LITERARY_QUALITY_EVIDENCE_CALIBRATION_AUDIT_REPORT.md` | CONSUMED |
| S7-09 Design v1.0 | `artifacts/NTPE_S7_09_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN.md` | CONSUMED |
| S7-09 Report | `artifacts/NTPE_S7_09_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN_REPORT.md` | CONSUMED |
| S7-10 Internal Audit | `artifacts/NTPE_S7_10_LITERARY_CALIBRATION_DESIGN_INTERNAL_AUDIT_REPORT.md` | CONSUMED |
| S7-11 Design v1.1 | `artifacts/NTPE_S7_11_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN_V1_1.md` | CONSUMED |
| S7-11 Revision Report | `artifacts/NTPE_S7_11_LITERARY_CALIBRATION_DESIGN_REVISION_REPORT.md` | CONSUMED |
| S7-12 Re-Audit | `artifacts/NTPE_S7_12_LITERARY_CALIBRATION_DESIGN_V1_1_INDEPENDENT_REAUDIT_REPORT.md` | CONSUMED |
| S7-12 Attack Test | `tools/one_shots/s7_12_contract_attack_test.py` | INSPECTED |

Applied versions: `pilot_dataset = v0.1 (unpopulated)`, `rubric = v1.1`, `protocol = v1.1`, `analysis = v0.1 (unpopulated)`.

---

## 3. Pilot Objective

Determine whether the v1.1 human-evaluation protocol is actually executable and whether
real evaluator data can be produced in a blind, randomized, traceable way. **Not** to
calibrate PS-03, thresholds, or weights.

---

## 4. Pilot Scope

Planned: 50 passages (`PILOT_ONLY`), 3–5 evaluators, scene-level rubric + binary
ACCEPT/REJECT + failure tags; optional pairwise studies only if approved offline
candidates exist.

**Executed**: none. **Blocking condition**: no real human evaluators are available
(S7-13 §13).

---

## 5. Evaluator Count

| Item | Value |
|------|-------|
| Planned | 3–5 (pilot design target — **not a validated requirement**) |
| Recruited | 0 |
| Completed | 0 |

No evaluator is present in the environment, and no real evaluator records exist in the
repository. Therefore no reliability evidence of any kind is produced.

---

## 6. Evaluator Protocol

Not executed. Protocol spec recorded in `artifacts/s7_13_pilot/protocol/PILOT_PROTOCOL_SPEC.md`.

## 7. Sampling

Not executed. Source material exists (`tests/literary/**/original_ko.txt`) but no sample
was drawn because evaluation cannot proceed without evaluators.

## 8. Candidate Provenance

Machine candidate outputs exist (PS-03 regression outputs, `original_ko_zh.txt`). These
are **machine outputs, not human references**. No approved pilot candidate bundle exists.

## 9. Reference Provenance

Independently verified: **no GOLD / SILVER / BRONZE reference translation exists** in the
repository (sources only). Consistent with S7-08. No reference-based comparison is possible.

## 10. Blinding

Not executed against humans. Offline presentation-contract check performed:
`tools/one_shots/s7_13_pilot_preflight.py` `blinding_leak` test correctly detected
`model` + `attempt_number` leakage in a synthetic presentation payload (`BLINDING_LEAK`),
and returned `OK` when metadata was absent. **Blinding: NOT EXECUTED (tooling verified).**

## 11. Randomization

Not executed. Offline order-balance check correctly flags a one-sided A-first design
(`ORDER_IMBALANCE`) and passes a counterbalanced design. **Randomization: NOT EXECUTED (tooling verified).**

---

## 12. Rubric

Pilot would use the S7-11 v1.1 rubric unchanged (7 dimensions × 7-point Likert + binary
ACCEPT/REJECT + predefined failure tags). No rubric change was made. No anchor-clearance
data was collected because no evaluator ran the rubric.

---

## 13. Pilot Data Integrity

| Check | Result |
|-------|--------|
| Raw row count | 0 (no data) |
| Expected row count | n/a (not executed) |
| Duplicate evaluation ids | n/a |
| Missing required fields | n/a |
| Invalid evaluator ids | n/a |

No raw data was fabricated. `artifacts/s7_13_pilot/raw/` remains empty.

---

## 14. Missing / Abstain / Invalid

No responses collected. Offline check confirms the protocol tooling detects silent
filling of `abstain` (`SILENT_FILL`) and preserves raw missing states (`OK`). No data
was dropped, filled, or invented.

## 15. Evaluator Burden

No evaluator; no timing data. Not reported (must not be estimated — S7-13 §41).

## 16. Fatigue / Carry-over

Not observed (no session). No fabricated fatigue figures.

## 17. Inter-Rater Analysis

Not estimable — 0 evaluators, 0 ratings. Reported as `NOT ESTIMABLE` (S7-13 §38).

## 18. Pairwise Analysis

Not executed. No approved offline candidate bundles exist for Best Attempt / Context /
Segment Merge / Reviewer–Editor–ACE (S7-13 §31–34).

## 19. PS-03 Exploratory Analysis

Not performed. No human labels exist; PS-03 remains `EXPLORATORY ONLY` and unchanged.

---

## 20. H02 Residual

`H02 = PARTIALLY_CLOSED (MEDIUM)`. No pilot data was collected, so character-arc
grouping could not be exercised or closed. Residual remains; **not** declared closed.
See S7-13 §57.

## 21. R1 Status

`R1 = CALIBRATION-BLOCKING — OPEN`. Validation-set role vs nested-CV inner tuning
ambiguity (S7-12 R1) is unresolved. No calibration model was built.

## 22. R2 Status

`R2 = OPEN`. No single primary endpoint is fixed ("ρ or AUC"). The pilot did not select
any primary endpoint after seeing results (there are none). Formal calibration endpoint
remains unresolved.

## 23. R3 Status

`R3 = OPEN`. Missing/outlier rules remain not fully enumerated. The pilot generated no
real missing/outlier data, so no proposed rule revision is possible yet. No post-hoc
exclusion was performed.

---

## 24. Protocol Deviations

| deviation_id | What happened | Impact | Data affected |
|--------------|---------------|--------|---------------|
| DEV-001 | Human evaluation could not be executed — no real evaluators available | Pilot cannot run | none (no data) |
| DEV-002 | No reference translations present | Reference-based tasks unavailable | none |
| DEV-003 | No approved offline pairwise candidate bundles | Best Attempt / Context / Segment / Reviewer tasks `NOT EXECUTED` | none |

## 25. Findings

1. **CRITICAL (blocking)**: No real human evaluator is available; the core pilot cannot
   be executed without fabrication, which is prohibited. → `PILOT_BLOCKED`.
2. **HIGH (pre-existing)**: No reference translations exist; reference-anchored evaluation
   is unavailable.
3. **INFO**: Offline presentation/data-integrity tooling correctly detects blinding
   leaks, reference conflicts, duplicate candidates, order imbalance, and silent
   missing-fill (10/10).

## 26. Required Revisions

- Recruit and onboard 3–5 qualified real evaluators (separate, authorized human-evaluation task).
- Produce at minimum one approved reference set (GOLD/SILVER) or explicitly run a
  reference-free rubric pilot.
- Resolve S7-12 R1/R2/R3 before any formal calibration.

---

## 27. Pilot Decision

```text
PILOT_BLOCKED (NOT EXECUTED — NO REAL EVALUATORS)
```

This is **not** `GO` (no data), and is **not** `NO-GO` (the protocol was not shown to be
unreliable — it simply could not be run). S7-13 §13 requires this blocked status.

## 28. Calibration Authorization

```text
NOT GRANTED BY THIS TASK
```

---

## 29. Production Boundary Verification

| Boundary | Code Evidence | Status |
|----------|---------------|--------|
| Model `meta/llama-3.2-90b-vision-instruct` | `core/adapters/production_submission_adapter.py:20`, `ntpe_production_translate.py:102`, `core/config.py:19` | FROZEN |
| Provider `nvidia` | `core/controlled_provider_routing/provider_profiles.py:28` | FROZEN |
| Retry boundary | `core/translation_reliability/adaptive_retry_policy.py` max_attempts=5, switch-after=3 (429/503/exhausted), chunk halving (empty/short/hangul/timeout) | PRESERVED |
| Context `quality_context_scene_v72=false` | `core/adapters/production_submission_adapter.py:38` default False | FROZEN OFF |
| PS-03 weights 30/20/20/15/10/5 | `ntpe_literary_evaluation.py:110,132,142,150,164,171` | FROZEN |
| Thresholds 80/65 | `ntpe_literary_evaluation.py:174` | FROZEN |
| Production files modified by S7-13 | none | NO |

---

## 30. Regression Tests

Command: `python -m pytest tests/ui/test_s6_02_acceptance.py tests/ui/test_s6_03_acceptance.py tests/ui/test_s6_04_acceptance.py tests/ui/test_s6_05_acceptance.py -q`

| Suite | Passed | Failed |
|-------|-------:|-------:|
| S6-02 TXT | 6 | 0 |
| S6-03 EPUB | 7 | 0 |
| S6-04 Validation | 16 | 0 |
| S6-05 Dry-Run | 8 | 0 |
| **Total** | **37/37** | **0** |

Before: 37/37. After: 37/37.

---

## 31. Human Evaluation

```text
0
```

Planned 3–5; recruited 0; completed 0; excluded 0. No exclusion occurred (no data).

## 32. Pilot Execution

```text
0 passages executed (0/50)
```

## 33. Calibration Execution

```text
0
```

## 34. Real Translation

```text
0
```

## 35. Provider / Network

```text
0
```

## 36. Production Files Modified

```text
NO
```

Only new files: the report artifact, the pilot artifact structure
(`artifacts/s7_13_pilot/`), and one offline preflight tool (`tools/one_shots/s7_13_pilot_preflight.py`).

## 37. Root Hygiene

```text
PASS
```

No root scratch files. Report/artifacts under `artifacts/`; one-shot tool under `tools/one_shots/`.

---

## 38. Final Verdict

```text
S7_13_PILOT_BLOCKED_NO_REAL_EVALUATORS
```

### Required Pilot Data Summary (§82)

| Metric | Result |
|--------|-------:|
| Passages planned | 50 |
| Passages completed | 0 |
| Evaluators planned | 3–5 |
| Evaluators completed | 0 |
| Total ratings expected | n/a |
| Total ratings collected | 0 |
| Missing | 0 |
| Abstain | 0 |
| Invalid | 0 |
| Duplicate | 0 |
| Median time/passage | NOT MEASURED |
| Dropout | 0 |
| Blinding failures | NOT EXECUTED (offline tooling OK) |
| Order randomization failures | NOT EXECUTED (offline tooling OK) |
| Reference conflicts | 0 (no references) |
| Protocol deviations | 3 |

### Required Reliability Table (§83)

| Dimension / Task | Method | Estimate | CI | Pilot Target | Interpretation |
|------------------|--------|---------:|----|-------------:|----------------|
| Naturalness | — | NOT ESTIMABLE | — | — | no data |
| Fidelity | — | NOT ESTIMABLE | — | — | no data |
| Character Voice | — | NOT ESTIMABLE | — | — | no data |
| Register/Tone | — | NOT ESTIMABLE | — | — | no data |
| Coherence | — | NOT ESTIMABLE | — | — | no data |
| Terminology | — | NOT ESTIMABLE | — | — | no data |
| Added/Missing | — | NOT ESTIMABLE | — | — | no data |

No fabricated numbers are provided.

### Required Pairwise Table (§84)

| Study | Pairs | Result |
|-------|------:|--------|
| Best Attempt | 0 | NOT EXECUTED — NO APPROVED OFFLINE CANDIDATES |
| Context | 0 | NOT EXECUTED — NO APPROVED OFFLINE CANDIDATES |
| Segment Merge | 0 | NOT EXECUTED — NO APPROVED OFFLINE CANDIDATES |
| Reviewer/Editor/ACE | 0 | NOT EXECUTED — NO APPROVED OFFLINE CANDIDATES |

### Required Evaluator Feedback Table (§85)

| Issue | Count | Severity | Action |
|-------|------:|----------|--------|
| (no feedback collected — no evaluators) | 0 | n/a | recruit evaluators |

### Required Final Compliance Block (§94)

```text
Production Model:
meta/llama-3.2-90b-vision-instruct

Provider:
nvidia

Production Quality Contract:
PRESERVED

Retry Boundary:
PRESERVED

Context:
quality_context_scene_v72=false

PS-03 Production:
UNCHANGED

80/65:
UNCHANGED

Real Translation:
0

Provider / Network:
0

Human Evaluation:
0

Pilot:
0

Calibration:
0

Production Code Modified:
NO

Regression:
37/37 PASS

Root Hygiene:
PASS

Commit:
NO

Push:
NO

Tag:
NO
```

---

## Artifacts Produced

| Artifact | Path |
|----------|------|
| Pilot Execution Report | `artifacts/NTPE_S7_13_LITERARY_QUALITY_PILOT_EXECUTION_REPORT.md` |
| Pilot status | `artifacts/s7_13_pilot/PILOT_STATUS.md` |
| Protocol spec | `artifacts/s7_13_pilot/protocol/PILOT_PROTOCOL_SPEC.md` |
| Provenance schema | `artifacts/s7_13_pilot/provenance/PROVENANCE_SCHEMA.md` |
| Offline preflight tool | `tools/one_shots/s7_13_pilot_preflight.py` |

**Commit: NO · Push: NO · Tag: NO**

---

*End of S7-13 Pilot Execution Report*
