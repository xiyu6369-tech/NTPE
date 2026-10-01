# NTPE S7-14 Literary Pilot Dependency & Calibration Readiness

**Task**: `S7-14 Literary Pilot Dependency & Calibration Readiness Closure`
**Date**: 2026-09-30
**Executor**: Kilo (Automated)
**Status**: `READINESS_PACKAGE_COMPLETE — PILOT EXTERNALLY BLOCKED`

---

## 1. Baseline

| Metric | Value |
|--------|-------|
| Actual HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` |
| Branch | `main` |
| Upstream | `origin/main` (tracking; not modified) |
| Origin | `https://github.com/xiyu6369-tech/NTPE.git` |
| Working Tree | 4 pre-existing modified (literary outputs), 1 pre-existing deletion, prior untracked artifacts — all preserved |

No destructive git operation performed. Pre-existing changes preserved (S7-14 §66).

## 2. S7-13 Findings Consumed

`S7_13_PILOT_BLOCKED_NO_REAL_EVALUATORS` consumed. Blockers:
A = No real human evaluators (`EXTERNAL_RESOURCE_DEPENDENCY`),
B = No GOLD/SILVER/BRONZE references (`EXTERNAL_DATA_DEPENDENCY`),
plus calibration blockers R1/R2/R3 (OPEN) and H02 residual (PARTIALLY_CLOSED).

## 3. Mission

Close everything resolvable by engineering/methodology, and package the remaining
genuine external dependencies explicitly — without fabricating data.

---

## 4. R1 Closure

### 4.1 Problem
v1.1 §15 assigned the 20% Validation set to "hyperparameter selection" while
§12.2/§13.2 placed selection in the nested-CV inner loop → role overlap.

### 4.2 Revised Boundary
Four unambiguous layers (`artifacts/NTPE_S7_14_CALIBRATION_SPLIT_AND_NESTED_CV_POLICY.md`):
Calibration (60%) → Inner CV (tune only) → Outer Validation (20%, evaluate once, never tune)
→ Frozen Procedure → Final Holdout (20%, one-time, sealed).

### 4.3 Verification
- Inner tuning ≠ Outer validation: ENFORCED
- Outer validation ≠ Final holdout: ENFORCED
- Holdout sealed + one-time: explicit
- Validator check `r1_nested_cv_boundary` = PASS
- Attack test: `validation_leakage → FAIL`, `holdout_leakage → FAIL` (detected)

### 4.4 Final Status
```text
R1 = CLOSED_VERIFIED
```

---

## 5. R2 Closure

### 5.1 Problem
Primary endpoint stated as "ρ or AUC" (v1.1 §7.2) → post-hoc endpoint selection risk.

### 5.2 Primary Endpoint
**Aggregate Spearman ρ** — exactly ONE (`artifacts/NTPE_S7_14_PRIMARY_ENDPOINT_POLICY.md`).
Selected by methodology (ordinal human label; alignment/ranking objective; ordinal-appropriate
method; v1.1 §12.1 already says "Spearman ρ (primary)"; AUC depends on an uncalibrated
threshold). Selection is independent of results.

### 5.3 Secondary / Exploratory Metrics
- Secondary: AUC (binary discrimination), ECE, per-dimension Spearman ρ.
- Exploratory: Pearson r (assumption-dependent), Kendall τ, subgroup analyses, alternates.

### 5.4 Verification
- Single primary endpoint: YES
- Endpoint switching: FORBIDDEN
- Validator check `r2_primary_endpoint` = PASS
- Attack test: `endpoint_disjunction → FAIL` (detected), `endpoint_single → OK`

### 5.5 Final Status
```text
R2 = CLOSED_VERIFIED
```

---

## 6. R3 Closure

### 6.1 Missing Taxonomy
`MISSING / ABSTAIN / INVALID / INATTENTIVE / DUPLICATE / SYSTEM_FAILURE / PROTOCOL_VIOLATION`
(`artifacts/NTPE_S7_14_MISSING_DATA_AND_OUTLIER_POLICY.md`). No post-hoc expansion.

### 6.2 Outlier Rules
Four distinct classes: statistical outlier / protocol-invalid observation / evaluator-quality
issue / data corruption. Low score ≠ outlier; low-agreement evaluator ≠ auto-exclusion.

### 6.3 Exclusion Rules
Predefined, auditable, outcome-independent. Silent deletion / zero-fill / mean-fill /
post-hoc fill all prohibited. Sensitivity analysis mandatory.

### 6.4 Verification
- Exclusive rules predefined: YES; result-dependent deletion: FORBIDDEN
- Validator check `r3_missing_outlier` = PASS
- Attack test: `missing_posthoc_exclusion → FAIL` (detected), `missing_predefined → OK`

### 6.5 Final Status
```text
R3 = CLOSED_VERIFIED
```

---

## 7. H02 Character-Arc Status

Inspected schema: v1.1 provides `author_id`, `chapter_id`, `scene_id`, `character_ids[]`,
`terminology_group_id` — but **no `character_arc_id`**. Character identity metadata exists
coarsely (`character_ids[]`), and chapter+author split grouping is present, but true
narrative-arc grouping requires future human annotation.

No arc data was invented.

```text
H02 = EXTERNAL_DEPENDENCY (character-arc annotation)
Coarse character-id grouping: available
Arc-level grouping: requires external annotation
Pilot may proceed; calibration split requirement remains unresolved
```

---

## 8. Human Evaluator Dependency

`artifacts/NTPE_S7_14_HUMAN_EVALUATOR_REQUIREMENTS.md` — defines real-human definition
(no LLM/agent/self-rating), count 3–5 (pilot design target, not validated), qualification,
training/practice, blindness, randomization, pseudonymous id, COI, exclusion, session/fatigue,
withdrawal. Recruitment = 0; contact = 0; personal data collected = 0.

**Status: `HUMAN_EVALUATOR = UNAVAILABLE` (external).**

## 9. Reference Dependency

`artifacts/NTPE_S7_14_REFERENCE_DATA_REQUIREMENTS.md` — GOLD/SILVER/BRONZE creator/review/
eligibility unchanged; zero new references created. Repository has sources + machine outputs
only. **Status: `REFERENCE_DATA = MISSING_EXTERNAL_DEPENDENCY`.**

## 10. Pilot Corpus Dependency

`artifacts/s7_14_pilot/PILOT_CORPUS_REQUIREMENTS.md` — scene-level, chapter-aware, stratified,
diversity, manifest schema (incl. `character_arc_ids`). Source material exists; manifest
unpopulated. **Status: PARTIAL.**

## 11. Candidate Dependency

`artifacts/NTPE_S7_14_PILOT_CANDIDATE_REQUIREMENTS.md` — provenance fields, allowed origins,
no live generation, metric-leakage guard, pairwise bundles required. Machine outputs exist;
approved bundles do not. **Status: PARTIAL.**

## 12. Blinding Readiness

`artifacts/s7_14_pilot/BLINDING_REQUIREMENTS.md` + offline check. Forbidden fields
(model/provider/attempt/condition/reference-class/prompt/ps03) covered. **READY.**
Validator `blinding` = PASS.

## 13. Randomization Readiness

`artifacts/s7_14_pilot/RANDOMIZATION_REQUIREMENTS.md` — passage order, A/B order,
assignment, seed policy, counterbalancing. **READY.** Validator `randomization` = PASS.

## 14. Provenance Readiness

`artifacts/s7_14_pilot/PROVENANCE_REQUIREMENTS.md` — traceability chain, pseudonymous ids,
privacy, raw (immutable) vs derived (regenerable), integrity checks. **READY.**
Validator `provenance` = PASS.

## 15. Offline Readiness Validation

| Validator | Result |
|-----------|--------|
| `tools/one_shots/s7_12_contract_attack_test.py` | 8/8 PASS |
| `tools/one_shots/s7_13_pilot_preflight.py` | 10/10 PASS |
| `tools/one_shots/s7_14_pilot_readiness.py` | `overall = PASS` (1 WARN: H02) |
| `tools/one_shots/s7_14_readiness_attack_test.py` | 12/12 PASS |

No human, no provider, no network, no real translation.

## 16. Pilot Dependency Matrix

| Dependency | Status | Required | Available | Blocking |
|------------|--------|---------:|----------:|---------:|
| Human evaluators | UNAVAILABLE | Yes | No | **Yes** |
| Reference corpus | MISSING | Yes | No | **Yes** |
| Pilot corpus | PARTIAL | Yes | Partial | Yes (full pilot) |
| Candidates | PARTIAL | Yes | Partial | Yes (pairwise) |
| Protocol | READY | Yes | Yes | No |
| Schema | READY | Yes | Yes | No |
| Provenance | READY | Yes | Yes | No |
| Blinding | READY | Yes | Yes | No |
| Randomization | READY | Yes | Yes | No |

## 17. Calibration Blocker Matrix

| ID | Problem | Current Status | S7-14 Action | Final Status | Blocking |
|----|---------|----------------|--------------|--------------|----------|
| R1 | CV/validation overlap | OPEN | Split & Nested CV Policy | `CLOSED_VERIFIED` | No |
| R2 | Primary endpoint | OPEN | Primary Endpoint Policy | `CLOSED_VERIFIED` | No |
| R3 | Missing/outlier | OPEN | Missing & Outlier Policy | `CLOSED_VERIFIED` | No |
| H02 | Character arc | PARTIAL | Schema inspection (no invention) | `EXTERNAL_DEPENDENCY` | Calibration-split requirement |
| A | Human evaluators | BLOCKED | dependency package | `UNAVAILABLE` | **Yes** |
| B | References | BLOCKED | dependency package | `MISSING` | **Yes** |

## 18. Future Pilot Entry Conditions

1. Real evaluators available · 2. Approved evaluator IDs · 3. Reference requirements met ·
4. Pilot corpus manifest populated · 5. Candidate manifest populated · 6. Provenance complete ·
7. Blinding verified · 8. Randomization verified · 9. Primary endpoint fixed · 10. R1 closed ·
11. R3 closed · 12. H02 limitation documented · 13. Missing/outlier rules frozen ·
14. Protocol-deviation policy frozen · 15. Raw-data storage ready.

## 19. Future Calibration Entry Conditions

1. R1 CLOSED · 2. R2 CLOSED · 3. R3 CLOSED · 4. Pilot GO · 5. Human reliability acceptable
under pre-registered criteria · 6. Reference corpus sufficient · 7. Candidate diversity
sufficient · 8. Cluster-aware sample size satisfied · 9. Holdout protected ·
10. Pre-registration frozen · 11. No major leakage · 12. No major reference contamination ·
13. Calibration analysis plan frozen.

## 20. Residual Risks

| ID | Risk | Severity | Class | Blocking |
|----|------|----------|-------|----------|
| A | No real human evaluators | CRITICAL | External resource | Pilot-blocking |
| B | No reference corpus | HIGH | External data | Pilot/Calibration-blocking |
| H02 | Character-arc grouping incomplete | MEDIUM | External annotation | Calibration-split-blocking |
| C | Approved pairwise candidate bundles absent | MEDIUM | External/repo | Pairwise-study-blocking |
| D | Pilot corpus manifest unpopulated | MEDIUM | Repository-resolvable | Pilot-blocking |

No fabricated data. External dependencies are not represented as implemented.

## 21. Production Boundary Verification

| Boundary | Code Evidence | Status |
|----------|---------------|--------|
| Model `meta/llama-3.2-90b-vision-instruct` | `core/adapters/production_submission_adapter.py:20`, `ntpe_production_translate.py:102` | FROZEN |
| Provider `nvidia` | `core/controlled_provider_routing/provider_profiles.py:28` | FROZEN |
| Retry boundary | `core/translation_reliability/adaptive_retry_policy.py` (max 5, switch after 3, chunk halving) | PRESERVED |
| Context `quality_context_scene_v72=false` | `core/adapters/production_submission_adapter.py:38` | FROZEN OFF |
| PS-03 weights / thresholds | `ntpe_literary_evaluation.py` (30/20/20/15/10/5; 80/65) | UNCHANGED |
| Production files modified by S7-14 | none | NO |

## 22. Regression Tests

`python -m pytest tests/ui/test_s6_02_acceptance.py tests/ui/test_s6_03_acceptance.py tests/ui/test_s6_04_acceptance.py tests/ui/test_s6_05_acceptance.py -q`

```text
Before: 37/37 PASS
After:  37/37 PASS
```

## 23. Human Evaluation
```text
0
```

## 24. Pilot Execution
```text
0
```

## 25. Calibration
```text
0
```

## 26. Real Translation
```text
0
```

## 27. Provider / Network
```text
0
```

## 28. Production Files Modified
```text
NO
```

## 29. Root Hygiene
```text
PASS
```

## 30. Final Verdict

```text
S7_14_READINESS_PACKAGE_COMPLETE_PILOT_EXTERNALLY_BLOCKED
```

### Split Decision (§53)

```text
Methodology Readiness:
CALIBRATION_METHODOLOGY_READY      (R1/R2/R3 closed; H02 = external dependency)

Pilot Operational Readiness:
PILOT_BLOCKED_BY_EXTERNAL_DEPENDENCIES  (no real evaluators; no reference corpus)

Calibration:
NOT AUTHORIZED

Production Literary Quality:
OBSERVATIONAL_ONLY  (unchanged)
```

`PILOT_EXTERNALLY_BLOCKED` is **not** a task failure: the remaining blockers are external
resource/data dependencies, not implementation defects.

### Required Final Compliance Block

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
| Readiness Report | `artifacts/NTPE_S7_14_LITERARY_PILOT_DEPENDENCY_CALIBRATION_READINESS_REPORT.md` |
| R1 Policy | `artifacts/NTPE_S7_14_CALIBRATION_SPLIT_AND_NESTED_CV_POLICY.md` |
| R2 Policy | `artifacts/NTPE_S7_14_PRIMARY_ENDPOINT_POLICY.md` |
| R3 Policy | `artifacts/NTPE_S7_14_MISSING_DATA_AND_OUTLIER_POLICY.md` |
| Human Evaluator Requirements | `artifacts/NTPE_S7_14_HUMAN_EVALUATOR_REQUIREMENTS.md` |
| Reference Data Requirements | `artifacts/NTPE_S7_14_REFERENCE_DATA_REQUIREMENTS.md` |
| Candidate Requirements | `artifacts/NTPE_S7_14_PILOT_CANDIDATE_REQUIREMENTS.md` |
| Corpus Requirements | `artifacts/s7_14_pilot/PILOT_CORPUS_REQUIREMENTS.md` |
| Blinding Requirements | `artifacts/s7_14_pilot/BLINDING_REQUIREMENTS.md` |
| Randomization Requirements | `artifacts/s7_14_pilot/RANDOMIZATION_REQUIREMENTS.md` |
| Provenance Requirements | `artifacts/s7_14_pilot/PROVENANCE_REQUIREMENTS.md` |
| Pilot Dependency Status | `artifacts/s7_14_pilot/PILOT_DEPENDENCY_STATUS.md` |
| Calibration Blocker Status | `artifacts/NTPE_S7_14_CALIBRATION_BLOCKER_STATUS.md` |
| Readiness Validator | `tools/one_shots/s7_14_pilot_readiness.py` |
| Readiness Attack Test | `tools/one_shots/s7_14_readiness_attack_test.py` |

**Commit: NO · Push: NO · Tag: NO**

---

*End of S7-14 Report*
