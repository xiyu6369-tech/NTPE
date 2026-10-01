# NTPE S7-07 — Literary Quality Contract v1

**Contract ID**: `NTPE_QUALITY_CONTRACT_V1`
**Status**: `DEFINED_WITH_EXPLICIT_BOUNDARIES`
**Date**: 2026-09-30
**Baseline HEAD**: `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5`
**Branch**: `main`
**S7-06 Input**: `S7_06_QUALITY_CONTRACT_DEFINED_WITH_UNDEFINED_AREAS`

---

## 1. Contract Purpose

This contract formally defines what NTPE considers "translation quality" for production acceptance purposes. It separates:

- **Deterministic Production Gates** — rules that block/accept/retry translation output in the live pipeline
- **Diagnostic / Observational Metrics** — signals that inform but do not gate production
- **Future / Undefined Capabilities** — areas requiring separate design tasks before production authorization

**Core Principle**: No arbitrary thresholds. Every production gate must trace to deterministic, repository-verifiable evidence.

---

## 2. Scope

| In Scope (Production Gates) | Out of Scope (Not Authorized) |
|-----------------------------|-------------------------------|
| Fidelity / Completeness gates | Literary Naturalness scoring |
| Terminology Consistency gates | Overall Literary Score aggregation |
| Character Consistency gates | Best Attempt Selection |
| Orthography / Formatting gates | Segment Recovery Quality Merge |
| Structural Integrity gates | Context Continuity (feature-gated) |
| Gate State Machine | Literary Reviewer / Editor / ACE |
| Retry Boundary | Model/Provider/Prompt changes |

---

## 3. Definitions

| Term | Definition |
|------|------------|
| **HARD_GATE** | Deterministic rule that blocks output (`retry_required`) or rejects (`rejected`) when violated. Must have deterministic measurement and explicit threshold in code. |
| **LOCAL_REPAIR** | Deterministic transformation applied to output before acceptance. Does not trigger retry. |
| **SOFT_GATE** | Produces warning only; does not affect acceptance or retry. |
| **OBSERVATIONAL** | Measurable signal for diagnostics; no acceptance threshold defined. |
| **MANUAL_REVIEW** | Requires human judgment; not automatable. |
| **UNDEFINED** | No deterministic contract exists; requires separate design task. |
| **NOT_IMPLEMENTED** | Component exists in code but not connected to production flow. |
| **NOT_REQUIRED** | Explicitly excluded from this contract version. |

---

## 4. Contract Classification Model

Each quality dimension is classified using the taxonomy above. Classification must be evidence-based.

---

## 5. Deterministic Production Gates

### 5.1 Fidelity / Completeness

| Dimension | Gate Type | Evidence | Threshold | Failure Action | Prod Reachability |
|-----------|-----------|----------|-----------|----------------|-------------------|
| Empty Output | HARD_GATE | `quality_baseline.py:53-57` — checks `not translated.strip()` | Zero tolerance | Provider retry (`retry_required`) | YES |
| Length Ratio | HARD_GATE | `quality_baseline.py:58-63` — `len(zh)/len(source)` | `min_length_ratio=0.35` (baseline), `0.18` (LTS) | Provider retry | YES |
| Paragraph Omission | HARD_GATE | `quality_baseline.py:96-133` — paragraph count ratio + corroboration | `translated_paragraphs < source_paragraphs * 0.5` + length/sentence corroboration | Provider retry | YES |
| Sentence Omission | HARD_GATE | `quality_baseline.py:134-147` — sentence count ratio | `translated_sentences < source_sentences * 0.5` | Provider retry | YES |
| Duplicate Paragraphs | HARD_GATE | `quality_baseline.py:76-81` — `Counter` on paragraphs | `max_duplicate_paragraphs=0` | Provider retry | YES |
| Duplicate Lines | HARD_GATE | `quality_baseline.py:82-87` — `Counter` on lines | `max_duplicate_lines=1` | Provider retry | YES |

### 5.2 Terminology Consistency

| Dimension | Gate Type | Evidence | Threshold | Failure Action | Prod Reachability |
|-----------|-----------|----------|-----------|----------------|-------------------|
| Locked Terms Missing | HARD_GATE | `terminology_guard.py:31-33` — `source_term in source and target_term not in translated` | Zero missing | Local repair (`apply_locked_terminology`) → if unresolved, provider retry | YES |
| Forbidden Variants | HARD_GATE | `terminology_guard.py:35-42` — `wrong_variant in translated` | Zero wrong variants | Local repair (replacement) | YES |
| Full-name Over-expansion | HARD_GATE | `terminology_guard.py:49-61` — detects given-name over-expansion into full name | Zero over-expansion | Local repair | YES |

### 5.3 Character Consistency

| Dimension | Gate Type | Evidence | Threshold | Failure Action | Prod Reachability |
|-----------|-----------|----------|-----------|----------------|-------------------|
| Character Names | HARD_GATE | Via locked terms (`terminology_guard.py`) + `character_memory_v2` persistence | Zero drift from locked terms | Local repair | YES |

### 5.4 Orthography / Formatting

| Dimension | Gate Type | Evidence | Threshold | Failure Action | Prod Reachability |
|-----------|-----------|----------|-----------|----------------|-------------------|
| Simplified Chinese | HARD_GATE | `quality_baseline.py:56-58` (via `TraditionalChineseNormalizer`), `normalization_result.simplified_residue_count == 0` | Zero tolerance | Local repair (`full_traditional_chinese_conversion`) | YES |
| Dialogue Quote Format | LOCAL_REPAIR | `quality_baseline.py:148-154` — detects `"`/`“`/`‘` vs `「」` | Convert to `「」` | Local repair (`normalize_dialogue_quotes`) | YES |

### 5.4 Structural Integrity

| Dimension | Gate Type | Evidence | Threshold | Failure Action | Prod Reachability |
|-----------|-----------|----------|-----------|----------------|-------------------|
| Paragraph Count | HARD_GATE | `quality_baseline.py:88-133` — ratio check | `translated_paragraphs / source_paragraphs >= 0.5` (corroborated) | Provider retry | YES |
| Sentence Count | HARD_GATE | `quality_baseline.py:134-147` — ratio check | `translated_sentences / source_sentences >= 0.5` | Provider retry | YES |

---

## 6. Gate State Machine

| State | Condition | Retry | Downstream |
|-------|-----------|-------|------------|
| `accepted` | All HARD_GATE pass; no `critical`/`high` severity issues | No | Output finalized |
| `accepted_with_warnings` | All HARD_GATE pass; only `low`/`medium` non-retry issues | No | Output finalized |
| `retry_required` | Any `critical`/`high` severity OR `retry_required=true` | **Yes** (AdaptiveRetryPolicy) | Provider retranslation |
| `rejected` | Any `rejected=true` (hallucination, added_detail) | No | Manual review |

**Evidence**: `quality_decision.py:28-37` (`decide_quality`), `unified_quality_gate.py:106-119` (maps to `accepted`/`retry_required`/`rejected`)

---

## 7. Severity Contract

| Severity | Canonical Codes | Gate Effect | Retry Trigger | Examples |
|----------|-----------------|-------------|---------------|----------|
| `critical` | `empty_output`, `too_short`, `hangul_residue` | Blocks `accepted` | **Yes** | Empty output, too short, Korean residue |
| `high` | `duplicate_paragraph`, `locked_term_missing`, `paragraph_omission_suspected`, `sentence_omission_suspected` | Blocks `accepted` | **Yes** | Duplicates, locked terms, omissions |
| `medium` | `duplicate_line`, `paragraph_structure_merged` (non-corroborated) | Warning only | No (unless `retry_required=true`) | Duplicate lines, merged paragraphs |
| `low` / `info` | `dialogue_quote_format` | Warning only | No | Dialogue quote format |

**Evidence**: `quality_issue.py:51-56` (`normalize_severity`), `quality_enforcement.py:45-48` (routing by severity)

---

## 8. Literary Naturalness / Reader Quality

| Field | Value |
|-------|-------|
| **Definition** | Translation reads naturally in target language; avoids machine prefaces, maintains appropriate Chinese density, minimizes Korean residue |
| **Evidence Source** | `ntpe_literary_evaluation.py:134-142` — `natural_chinese_proxy` (20pts max): `korean_hits`, `chinese_density`, `preface_penalty` |
| **Measurement** | Heuristic proxy: `korean_hits * 1.5`, `density_penalty` if `chinese_density < 0.45`, `preface_penalty` for `以下`/`翻譯如下`/`以下是` |
| **Threshold** | **UNDEFINED** — No deterministic threshold calibrated against human judgment |
| **Gate Type** | **OBSERVATIONAL_ONLY** |
| **PS-03 Weight** | 20/100 points |
| **Acceptance Impact** | **NO_PRODUCTION_EFFECT** — not in production pipeline |
| **Retry Eligibility** | No |
| **Production Reachability** | NO — PS-03 runs post-hoc on test corpus outputs only |
| **Calibration Evidence** | None — weights (20pts) arbitrary; no human evaluation correlation |
| **Status** | **OBSERVATIONAL_ONLY** |

**Rationale**: PS-03 `natural_chinese_proxy` is a heuristic proxy (korean residue count, Chinese density, preface detection). No calibration against human literary judgment exists. The 20-point weight is arbitrary. Cannot be promoted to HARD_GATE without calibration evidence.

---

## 9. Overall Literary Score / PS-03 Aggregate

| Field | Value |
|-------|-------|
| **Definition** | 100-point aggregate across 6 proxy metrics |
| **Evidence Source** | `ntpe_literary_evaluation.py:53-189` — `evaluate_translation_text()` |
| **Dimensions & Weights** | Plot Fidelity (30), Locked Names (20), Natural Chinese (20), Subject/Pronoun (15), Character Voice (10), Format/Punctuation (5) |
| **Thresholds** | ≥80 = success, ≥65 = warning, <65 = failed (arbitrary) |
| **Gate Type** | **OBSERVATIONAL_ONLY** |
| **Acceptance Impact** | **NO_PRODUCTION_EFFECT** — runs post-hoc on test corpus only |
| **Retry Eligibility** | No |
| **Production Reachability** | NO — not in translation pipeline |
| **Calibration Evidence** | None — weights arbitrary; 80/65 thresholds uncalibrated |
| **Status** | **OBSERVATIONAL_ONLY** |

**Rationale**: PS-03 is a post-hoc evaluation tool for test corpus regression tracking. Weights (30/20/20/15/10/5) and thresholds (80/65) are arbitrary with no human-evaluation calibration. The aggregate score cannot be used as a production acceptance gate.

---

## 10. Best Attempt Selection

| Field | Value |
|-------|-------|
| **Definition** | Select best translation across multiple retry attempts |
| **Evidence Source** | `core/translation_quality_v5/best_attempt.py:17-55` — `select_best_attempt()` |
| **Algorithm** | Rank by: (1) decision rank (accepted > accepted_with_warnings > retry_required > rejected), (2) quality score (higher better), (3) fewer blocking issues, (4) fewer total issues, (5) longer translation |
| **Production Integration** | **NOT_IMPLEMENTED** — function exists but **not called** in production pipeline (`Select-String` returns zero call sites) |
| **Gate Type** | **NOT_IMPLEMENTED** |
| **Production Reachability** | NO |
| **Key Limitation** | Scores not comparable across attempts (different source chunks, different baselines); no cross-attempt normalization; no quality floor |
| **Status** | **NOT_IMPLEMENTED** |

**Rationale**: The `select_best_attempt` function exists with a deterministic ranking algorithm but is **not called** in any production code path. Cross-attempt score comparability is undefined (different chunks = different baselines). Cannot authorize production use without: cross-attempt normalization, quality floor, tie handling, determinism proof.

---

## 11. Segment Recovery Quality Merge

| Field | Value |
|-------|-------|
| **Definition** | Re-translate only failing segments; merge recovered segments with successful ones |
| **Evidence Source** | `core/translation_quality_v5/segment_recovery.py` — `split_recovery_segments()`, `should_use_segment_recovery()` |
| **Trigger** | `NTPE_SEGMENT_COMPLETENESS_RECOVERY` env var (default enabled) + source ≥360 chars + completeness issue codes |
| **Segmentation** | Conservative: paragraph → sentence → character boundaries (target 280 chars, range 180-420) |
| **Production Integration** | **NOT_IMPLEMENTED** — functions exist but **not called** in production pipeline |
| **Merge Logic** | **NOT_IMPLEMENTED** — no segment result merging, ordering, duplicate prevention, or cross-segment continuity logic |
| **Gate Type** | **NOT_IMPLEMENTED** |
| **Production Reachability** | CONDITIONAL (env-gated, but not connected) |
| **Key Limitation** | No segment result merging strategy; no cross-segment consistency check; no boundary integrity guarantee |
| **Status** | **NOT_IMPLEMENTED** |

**Rationale**: Segment recovery functions exist (`split_recovery_segments`, `should_use_segment_recovery`) but are **not connected** to the production pipeline. No merge strategy exists for combining recovered segments with successful ones. Cannot authorize without: merge strategy, cross-segment consistency, boundary integrity guarantees.

---

## 12. Context Continuity

| Field | Value |
|-------|-------|
| **Definition** | Cross-chunk narrative/scene continuity via scene boundary detection, context selection, narrative engine |
| **Evidence Source** | `quality_context_scene_v72` flag in `production_submission_adapter.py:38` (default `False`), `translation_engine.py:70` |
| **Flag** | `quality_context_scene_v72: bool = False` (default off) |
| **Production Integration** | **FEATURE_GATED_OFF** — flag exists but default `False`; only active when explicitly set in package metadata |
| **Gate Type** | **FEATURE_GATED_OFF** |
| **Production Reachability** | CONDITIONAL (requires explicit opt-in via metadata) |
| **Retry Impact** | None (feature-gated off by default) |
| **Status** | **FEATURE_GATED_OFF** |

**Rationale**: The `quality_context_scene_v72` flag is explicitly default `False` in `production_submission_adapter.py:38`. Only activated when explicitly passed in package metadata. No production path enables it by default. Cannot be promoted without explicit feature-gate decision.

---

## 13. Reviewer / Editor / ACE

| Component | Status | Evidence | Production Reachability |
|-----------|--------|----------|------------------------|
| **ACE (Adaptive Context Engine)** | **TEST_ONLY** | `tests/integration/translation_engine_v700_stage0*_ace_*.py` — only tests `mode='disabled'|'shadow'|'active'` with fallback | NO |
| **Literary Reviewer** | **NOT_IMPLEMENTED** | No repository evidence (no class, no prompt, no fixture) | NO |
| **Literary Editor** | **NOT_IMPLEMENTED** | No repository evidence | NO |

**Rationale**: ACE exists only in test fixtures with `mode='disabled'|'shadow'|'active'` and fallback logic. No production integration path exists. Literary Reviewer/Editor have zero repository evidence. Explicitly excluded from this contract.

---

## 14. Retry Boundary (LOCKED — From S7-03/S7-06)

| Rule | Contract Value | Evidence |
|------|----------------|----------|
| Max Attempts | 5 (configurable via `max_attempts`) | `adaptive_retry_policy.py:195` |
| Provider Switch | After attempt 3 for `http_429`/`http_503`/`retry_exhausted` (if `allow_provider_switch=true`) | `adaptive_retry_policy.py:137-141` |
| Quality Retry: Chunk Halving | For `empty_output`, `too_short`, `hangul_residue`, `read_timeout` | `adaptive_retry_policy.py:235` |
| Quality Retry: Delay | 0s for quality failures; exponential/linear for provider errors | `adaptive_retry_policy.py:209-223` |
| Timeout Increase | +30s or 1.25× for timeouts | `adaptive_retry_policy.py:226-230` |
| No Real Translation in Decision | `provider_called: false`, `http_called: false`, `api_key_accessed: false` enforced | `adaptive_retry_policy.py:260-272`, `quality_*.py` `integration_status` |

**This boundary is LOCKED — S7-07 does not modify it.**

---

## 15. Production Reachability Summary

| Component | Reachability | Notes |
|-----------|--------------|-------|
| Fidelity Gates | YES | Core pipeline |
| Terminology Gates | YES | Core pipeline |
| Character Consistency | YES | Core pipeline |
| Orthography Gates | YES | Core pipeline |
| Structural Gates | YES | Core pipeline |
| Gate State Machine | YES | Unified Quality Gate (LTS) |
| Discipline Routing | YES | Production-integrated |
| Adaptive Retry | YES | Production-integrated |
| Literary Naturalness | NO | PS-03 post-hoc only |
| PS-03 Aggregate | NO | PS-03 post-hoc only |
| Best Attempt | NO | Implemented but not connected |
| Segment Recovery Merge | NO | Env-gated but not connected |
| Context Continuity | CONDITIONAL | Feature-gated off by default |
| ACE / Reviewer / Editor | NO | Test-only / not implemented |

---

## 16. Acceptance Impact Summary

| Dimension | Impact |
|-----------|--------|
| Fidelity Gates | RETRY |
| Terminology Gates | RETRY (after local repair) |
| Character Consistency | RETRY (after local repair) |
| Orthography Gates | RETRY (simplified Chinese) / LOCAL_REPAIR (dialogue quotes) |
| Structural Gates | RETRY |
| Literary Naturalness | NO_PRODUCTION_EFFECT |
| PS-03 Score | NO_PRODUCTION_EFFECT |
| Best Attempt | NOT_IMPLEMENTED |
| Segment Recovery | NOT_IMPLEMENTED |
| Context Continuity | CONDITIONAL (feature-gated) |

---

## 17. Undefined Areas Register

| Item | Current State | Why Undefined | Evidence Needed | Future Prerequisite |
|------|---------------|---------------|-----------------|---------------------|
| Literary Naturalness Threshold | OBSERVATIONAL | No deterministic measurement; heuristic proxy | Human evaluation correlation; determinism proof | QUALITY-CONTRACT-DESIGN task |
| Overall Literary Score | OBSERVATIONAL | Arbitrary weights (30/20/20/15/10/5); no calibration | Benchmark against human judgment | QUALITY-CONTRACT-DESIGN task |
| Best Attempt Selection | NOT_IMPLEMENTED | No cross-attempt comparison; score non-comparable | Attempt normalization; quality floor | QUALITY-CONTRACT-DESIGN task |
| Segment Recovery Quality Merge | NOT_IMPLEMENTED | No merge strategy; no cross-segment consistency | Merge strategy; consistency check | QUALITY-CONTRACT-DESIGN task |
| Context Continuity Gate | FEATURE_GATED_OFF | Feature-gated off (`quality_context_scene_v72=false`) | Cross-chunk metrics; scene boundary quality | Feature-gate decision task |
| Literary Reviewer | NOT_IMPLEMENTED | No component exists | Human evaluation protocol | OUT_OF_SCOPE |
| Literary Editor | NOT_IMPLEMENTED | No component exists | Edit operation definition | OUT_OF_SCOPE |
| ACE Production | TEST_ONLY | No production integration path | Active mode validation; fallback reliability | OUT_OF_SCOPE |

---

## 18. Evidence / Calibration Requirements for Future Promotion

For any OBSERVATIONAL item to become HARD_GATE, it must provide:

| Requirement | Status for Literary Naturalness | Status for PS-03 | Status for Best Attempt | Status for Segment Merge |
|-------------|--------------------------------|------------------|-------------------------|--------------------------|
| Deterministic definition | ❌ Heuristic proxy | ❌ Proxy aggregate | ✅ Deterministic rank | ❌ No merge logic |
| Representative dataset | ❌ Test corpus only | ❌ Test corpus only | ❌ No attempt dataset | ❌ No merge dataset |
| Known-good reference | ❌ No human baseline | ❌ No human baseline | ❌ No attempt baseline | ❌ No merge baseline |
| Failure examples | ✅ Korean residue, density | ✅ Low score cases | N/A | N/A |
| Human evaluation correlation | ❌ None | ❌ None | N/A | N/A |
| Threshold rationale | ❌ Arbitrary (20pts, density<0.45) | ❌ Arbitrary (80/65, weights) | N/A | N/A |
| Historical stability | ⚠️ Proxy only | ⚠️ Proxy only | N/A | N/A |
| FP/FN understanding | ⚠️ Limited | ⚠️ Limited | N/A | N/A |

**Policy**: DO NOT PROMOTE TO HARD_GATE without all rows ✅.

---

## 19. Quality Contract vs Quality Score

**Quality Contract** = Rules that determine what production may accept/retry/reject
- Deterministic gates
- Explicit thresholds
- Defined failure actions

**Quality Score** = Measurement/diagnostic signal
- Heuristic proxies (PS-03)
- Observational metrics
- No acceptance threshold without calibration

**Rule**: No automatic `score > threshold → acceptance` without full calibration evidence.

---

## 20. Non-Goals (Explicit)

| Non-Goal | Reason |
|----------|--------|
| Literary Naturalness scoring | Heuristic only; no deterministic threshold |
| Reader-quality / publication readiness | Human judgment required |
| Best Attempt selection across retries | Scores not comparable across attempts |
| Segment Recovery quality merge | Not implemented; no merge strategy |
| Cross-chunk context continuity | Feature-gated off |
| Literary Reviewer / Editor execution | Not implemented |
| ACE production activation | Test-only; fallback-only design |
| Model/Provider/Prompt changes for quality | Frozen per governance |

---

## 21. Regression Guarantees

This contract guarantees preservation of:

| Existing Contract | Guarantee |
|-------------------|-----------|
| S1-S4 EPUB contracts | ✅ Unchanged |
| S5 EPUB packaging/structure | ✅ Unchanged |
| S6 TXT/EPUB UI workflows | ✅ Unchanged |
| S6-02/03/04/05 acceptance | ✅ Unchanged (37/37 tests pass) |
| Model: `meta/llama-3.2-90b-vision-instruct` | ✅ Frozen |
| Provider: `nvidia` | ✅ Frozen |
| Retry boundary | ✅ Locked |

---

## 22. S7-07 Acceptance Criteria

| AC | Criterion | Status | Evidence |
|----|-----------|--------|----------|
| AC-01 | All production dimensions classified | ✅ | Section 5 table |
| AC-02 | Literary Naturalness explicitly bounded | ✅ | Section 8 (OBSERVATIONAL_ONLY) |
| AC-03 | PS-03 not falsely promoted | ✅ | Section 9 (OBSERVATIONAL_ONLY) |
| AC-03 | Best Attempt status clear | ✅ | Section 10 (NOT_IMPLEMENTED) |
| AC-04 | Segment Recovery status clear | ✅ | Section 11 (NOT_IMPLEMENTED) |
| AC-05 | Context Continuity status clear | ✅ | Section 12 (FEATURE_GATED_OFF) |
| AC-06 | Reviewer/Editor/ACE excluded | ✅ | Section 13 (TEST_ONLY/NOT_IMPLEMENTED) |
| AC-07 | Retry boundary unchanged | ✅ | Section 14 (LOCKED) |
| AC-08 | Model/Provider frozen | ✅ | Verified |
| AC-09 | No real translation execution | ✅ | 0 provider calls |
| AC-10 | No production modifications | ✅ | 0 production files changed |
| AC-11 | Contract artifact produced | ✅ | This document |
| AC-12 | Report artifact produced | ✅ | Companion report |
| AC-13 | No commit/push/tag | ✅ | Verified |

---

## 23. Final Verdict

```
S7_07_QUALITY_CONTRACT_V1_DEFINED_WITH_EXPLICIT_BOUNDARIES
```

### Summary

**Contract Defined For** (deterministic, production-integrated):
- 9 Fidelity/Completeness HARD_GATES
- 3 Terminology HARD_GATES + 1 LOCAL_REPAIR
- 1 Character Consistency HARD_GATE
- 2 Orthography Gates (1 HARD_GATE, 1 LOCAL_REPAIR)
- 2 Structural HARD_GATES
- Gate State Machine (4 states)
- Severity Contract (4 levels)
- Retry Boundary (LOCKED)

**Explicitly Bounded as Non-Production**:
- Literary Naturalness → OBSERVATIONAL_ONLY (PS-03 proxy, no calibration)
- PS-03 Aggregate → OBSERVATIONAL_ONLY (arbitrary weights/thresholds)
- Best Attempt Selection → NOT_IMPLEMENTED (exists but not connected)
- Segment Recovery Quality Merge → NOT_IMPLEMENTED (env-gated, no merge logic)
- Context Continuity → FEATURE_GATED_OFF (default false)
- Literary Reviewer/Editor/ACE → TEST_ONLY / NOT_IMPLEMENTED

**No Production Defects**. All existing production gates preserved. No arbitrary thresholds introduced. No unauthorized capability claims.

---

*End of Contract*

**Contract Path**: `artifacts/NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1.md`
**Design Complete**: `S7_07_QUALITY_CONTRACT_V1_DEFINED_WITH_EXPLICIT_BOUNDARIES`