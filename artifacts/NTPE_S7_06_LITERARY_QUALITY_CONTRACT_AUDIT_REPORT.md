# NTPE S7-06 — Literary Quality Contract Design Audit Report

**Audit Date**: 2026-09-30
**Auditor**: Kilo (Automated)
**Scope**: Literary Quality Contract Design Audit per S7-06 mandate
**Baseline HEAD**: `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` (S7-04 commit)
**Branch**: `main`

---

## 1. Baseline & Repository State

| Metric | Value |
|--------|-------|
| Baseline HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` ✓ |
| Branch | `main` ✓ |
| Working Tree | 4 modified (pre-existing literary outputs), 25 untracked (pre-existing artifacts) |
| S7-04 Status | COMMIT COMPLETE (`feat(ui): repair EPUB Translation Studio execution`) |
| S7-05 Status | AUDIT COMPLETE (`S7_05_PRODUCTION_FLOW_AUDIT_CLEAR_WITH_FOLLOWUPS`) |

---

## 2. Existing Quality Components — Repository Evidence

### 2.1 Quality Runtime Core Pipeline (Production-Integrated)

| Component | File | Version | Status | Production Integration |
|-----------|------|---------|--------|------------------------|
| TranslationQualityBaseline | `core/translation_quality_v5/quality_baseline.py` | TE-v5.0 | **IMPLEMENTED** | ✅ Called by `TranslationQualityCorePipeline.run()` |
| CompletenessGuard | `core/translation_quality_v5/completeness_guard.py` | TE-v5.0 | **IMPLEMENTED** | ✅ Called by core pipeline |
| TerminologyConsistencyGuard | `core/translation_quality_v5/terminology_guard.py` | TE-v5.0 | **IMPLEMENTED** | ✅ Called by core pipeline |
| TraditionalChineseNormalizer | `core/translation_quality_v5/traditional_chinese_normalizer.py` | — | **IMPLEMENTED** | ✅ Called by core pipeline |
| TranslationQualityCorePipeline | `core/translation_quality_v5/quality_core_pipeline.py` | TE-v5.0 | **IMPLEMENTED** | ✅ Used by `QualityRepairPipeline` |

**Evidence**: `quality_core_pipeline.py:21-104` — `run()` executes baseline, completeness, terminology, normalization sequentially. Returns `accepted`, `quality_score`, `repair_actions`, `retry_required`. **Integration status**: `provider_called: false`, `real_translation_executed: false` enforced.

### 2.2 Quality Repair Pipeline (Production-Integrated)

| Component | File | Version | Status | Production Integration |
|-----------|------|---------|--------|------------------------|
| QualityRepairPipeline | `core/translation_quality_v5/quality_repair_pipeline.py` | TE-v5.1 | **IMPLEMENTED** | ✅ Orchestrates quality → repair → retry → rebuild |
| QualityRepairPlanner | `core/translation_quality_v5/quality_repair_planner.py` | — | **IMPLEMENTED** | ✅ Plans repair actions from quality result |
| QualityRetryOrchestrator | `core/translation_quality_v5/quality_retry_orchestrator.py` | TE-v5.1 | **IMPLEMENTED** | ✅ Uses `AdaptiveRetryPolicy` for retry decisions |
| QualityChunkRebuildPlanner | `core/translation_quality_v5/quality_chunk_rebuild_planner.py` | — | **IMPLEMENTED** | ✅ Rebuilds chunks for segment recovery |

**Evidence**: `quality_repair_pipeline.py:21-72` — `run()` chains quality → repair plan → retry decision → chunk rebuild. Returns `status` ∈ {`accepted`, `retry_planned`, `repair_required`}. **Integration status**: No provider/http/api_key access.

### 2.3 Quality Gate Contract & Decision (Contract-Only, Disabled by Default)

| Component | File | Version | Status | Production Integration |
|-----------|------|---------|--------|------------------------|
| QualityRuntimeGateContract | `core/translation_quality_v5/quality_runtime_gate_contract.py` | TE-v5.2 | **CONTRACT_DEFINED** | ❌ `default_mode: disabled`, `activation_mode: explicit_opt_in_only` |
| QualityRuntimeGateDecision | `core/translation_quality_v5/quality_runtime_gate_decision.py` | TE-v5.2 | **CONTRACT_DEFINED** | ❌ Not connected to production flow |
| Unified Quality Gate | `core/translation_quality_v5/unified_quality_gate.py` | TE-v5.3.1 | **IMPLEMENTED** | ✅ Called by `run_unified_quality_gate()` in LTS pipeline |

**Evidence**: `quality_runtime_gate_contract.py:10-44` — Explicitly `default_mode: disabled`, `activation_mode: explicit_opt_in_only`, `real_translation_allowed: false`. The unified gate (`unified_quality_gate.py:70-127`) merges v5 + legacy QA issues, calculates unified score, decides `accept`/`retry_required`/`reject`, enforces discipline.

### 2.4 Discipline / Enforcement (Production-Integrated)

| Component | File | Version | Status | Production Integration |
|-----------|------|---------|--------|------------------------|
| DisciplineQualityEnforcer | `core/translation_discipline/quality_enforcement.py` | 6.0.0-stage03 | **IMPLEMENTED** | ✅ Annotates issues with `discipline_route` (local_repair / provider_retry / warning) |
| UnifiedQualityGateAdapter | `core/translation_discipline/quality_adapter.py` | — | **IMPLEMENTED** | ✅ Maps issue codes to discipline rules |

**Evidence**: `quality_enforcement.py:39-48` — Routes issues: `local_repair` (naturalness, simplified_chinese, dialogue_format, paragraph_merged), `provider_retry` (empty_output, too_short, omission, hangul, duplicate, locked_term, semantic, hallucination), `warning` (else). **Decision preserved**: score/decision/accepted/retry_required untouched.

### 2.5 Retry Policy (Production-Integrated)

| Component | File | Version | Status | Production Integration |
|-----------|------|---------|--------|------------------------|
| AdaptiveRetryPolicy | `core/translation_reliability/adaptive_retry_policy.py` | TE-v4.0 | **IMPLEMENTED** | ✅ Used by `QualityRetryOrchestrator` |

**Evidence**: `adaptive_retry_policy.py:61-157` — Decides retry based on `outcome` (http_429, empty_output, too_short, hangul_residue, etc.), `attempt`, `max_attempts`, `timeout`. Returns `RetryDecision` with `retry`, `delay_seconds`, `next_timeout_seconds`, `next_chunk_size`, `rebuild_provider_session`, `switch_provider`. **No provider/http execution**.

### 2.6 Segment Recovery (Feature-Gated, Env-Controlled)

| Component | File | Version | Status | Production Integration |
|-----------|------|---------|--------|------------------------|
| Segment Recovery | `core/translation_quality_v5/segment_recovery.py` | 5.5.3.3 | **IMPLEMENTED** | ⚠️ Feature-gated via `NTPE_SEGMENT_COMPLETENESS_RECOVERY` env |

**Evidence**: `segment_recovery.py:16-43` — `segment_recovery_enabled()` checks env var (default enabled). `should_use_segment_recovery()` requires: enabled + source ≥360 chars + completeness issue codes. Splits source on paragraph/sentence boundaries for retranslation. **Not connected to default production flow** (env-gated).

### 2.7 Literary Evaluation (Post-Hoc Tooling, Not Production-Integrated)

| Component | File | Version | Status | Production Integration |
|-----------|------|---------|--------|------------------------|
| PS-03 Literary Evaluation | `ntpe_literary_evaluation.py` | 1.2-translation-engine-refactor-v1 | **TOOLING** | ❌ Post-hoc evaluation only, not in translation pipeline |

**Evidence**: `ntpe_literary_evaluation.py:89-189` — 6 metrics (plot_fidelity 30pts, locked_names 20pts, natural_chinese 20pts, subject_pronoun 15pts, character_voice 10pts, format_punctuation 5pts). Total 100pts. Thresholds: ≥80=success, ≥65=warning, <65=failed. **Not connected to translation runtime**; runs on test corpus outputs.

### 2.8 LTS Quality Validation (Release Gate, Not Runtime)

| Component | File | Version | Status | Production Integration |
|-----------|------|---------|--------|------------------------|
| LTS RC Quality | `lts/quality_validation.py` | 1.1-lts-rc-04 | **RELEASE_GATE** | ❌ Static validation only, no runtime execution |

**Evidence**: `quality_validation.py:100-136` — Static quality probe (no external API). Checks: korean residue detector, length ratio gate, repeated line detector, formatter normalization, QA failure/clean case detection. **Validation scope**: metadata only, does not modify runtime.

### 2.9 ACE / Literary Reviewer / Editor (Not Production-Integrated)

| Component | Status | Production Integration |
|-----------|--------|------------------------|
| ACE (Adaptive Context Engine) | **TEST_ONLY** | ❌ Tests only (`translation_engine_v700_stage0*_ace_*_test.py`) |
| Literary Reviewer | **NOT_IMPLEMENTED** | ❌ No repository evidence |
| Literary Editor | **NOT_IMPLEMENTED** | ❌ No repository evidence |

**Evidence**: ACE tests in `tests/integration/translation_engine_v700_stage0*_ace_*.py` — only `mode='disabled'|'shadow'|'active'` with fallback logic. No production activation. No `LiteraryReviewer` or `LiteraryEditor` classes found in repository.

---

## 3. Quality Dimension Classification

| Dimension | Definition | Evidence | Measurement | Threshold | Gate? | Failure Action |
|-----------|------------|----------|-------------|-----------|-------|----------------|
| **Fidelity / Completeness** | Source content fully translated; no omissions | `quality_baseline.py`: `empty_output`, `too_short`, `paragraph_omission_suspected`, `sentence_omission_suspected`, `duplicate_paragraph` | Deterministic: length_ratio, paragraph/sentence counts, duplicate detection | `min_length_ratio=0.35` (baseline), `0.18` (LTS); `max_hangul=0` | **YES** (HARD_GATE) | `retry_required` → provider retry |
| **Terminology Consistency** | Locked terms present; no wrong variants | `terminology_guard.py`: `locked_term_missing`, `wrong_variants`, `full_name_overexpansion` | Deterministic: exact string match against locked dict + forbidden variants | Zero tolerance for missing/wrong locked terms | **YES** (HARD_GATE) | `apply_locked_terminology` (local) or provider retry |
| **Character Consistency** | Character names consistent across chunks | `terminology_guard.py` (locked terms) + `character_memory_v2` | Deterministic: locked term enforcement | Zero tolerance | **YES** (HARD_GATE via locked terms) | `apply_locked_terminology` (local) |
| **Context Continuity** | Cross-chunk narrative/scene consistency | `context_scene_memory` (feature-gated `quality_context_scene_v72`) | Heuristic: scene boundary detection, context selection, narrative engine | **UNDEFINED** (feature-gated off) | **NO** (OBSERVATIONAL) | N/A |
| **Literary Naturalness** | Translation reads naturally in target language | PS-03 `natural_chinese_proxy` (korean_hits, chinese_density, preface detection) | Heuristic: proxy metrics (korean residue, density, preface patterns) | **UNDEFINED** (PS-03: 20pts max) | **NO** (OBSERVATIONAL) | N/A |
| **Output Discipline** | Formatting, punctuation, orthography rules | `quality_baseline.py`: `dialogue_quote_format`, `simplified_chinese`; `traditional_chinese_normalizer` | Deterministic: regex pattern matching | Zero simplified Chinese; dialogue quotes `「」` | **YES** (HARD_GATE for simplified Chinese; LOCAL_REPAIR for dialogue quotes) | `full_traditional_chinese_conversion` (local); `normalize_dialogue_quotes` (local) |
| **Structural Integrity** | Paragraph/sentence structure preserved | `quality_baseline.py`: paragraph/sentence counts, duplicate detection | Deterministic: counts, duplicate detection | `max_duplicate_paragraphs=0`, `max_duplicate_lines=1` | **YES** (HARD_GATE for omissions; LOCAL_REPAIR for format) | Provider retry for omissions; local repair for format |

---

## 4. Quality Gate Contract

### 4.1 Current Gate States

| Gate | Current State | Decision Mode | Default | Production Active |
|------|---------------|---------------|---------|-------------------|
| TE-v5 Quality Runtime Gate | **CONTRACT_DEFINED** | `accept`/`retry`/`reject` | **DISABLED** (`explicit_opt_in_only`) | ❌ No |
| Unified Quality Gate (v5.3.1) | **IMPLEMENTED** | `accept`/`accepted_with_warnings`/`retry_required`/`rejected` | Enabled in LTS pipeline | ✅ Yes (LTS) |
| Discipline Enforcement | **IMPLEMENTED** | Annotates routing only | Enabled | ✅ Yes |
| Segment Recovery | **IMPLEMENTED** | Source segment retranslation | Env-gated | ⚠️ Opt-in |

### 4.2 Gate State Contract (Unified Quality Gate)

| State | Condition | Semantics | Retry? | Production Action |
|-------|-----------|-----------|--------|-------------------|
| `accepted` | No merged issues | Quality pass | No | Continue |
| `accepted_with_warnings` | Only non-blocking issues (low/medium, no retry_required) | Quality pass with warnings | No | Continue |
| `retry_required` | Any critical/high severity OR any `retry_required=true` | Quality fail — needs retranslation | **Yes** | Provider retry via `AdaptiveRetryPolicy` |
| `rejected` | Any `rejected=true` issue | Quality fail — cannot auto-recover | No | Manual review |

**Evidence**: `quality_decision.py:28-37` — `decide_quality()` returns `retry_required` if any `critical`/`high` severity OR `retry_required=true`. `unified_quality_gate.py:106-119` — maps decision to `accepted`/`retry_required`/`rejected`.

### 4.3 Gate Severity Contract

| Severity | Canonical | Retry Implication | Examples |
|----------|-----------|-------------------|----------|
| `critical` | Blocks acceptance → `retry_required` | **Yes** (provider retry) | `empty_output`, `too_short`, `hangul_residue` |
| `high` | Blocks acceptance → `retry_required` | **Yes** (provider retry) | `duplicate_paragraph`, `locked_term_missing`, `paragraph_omission_suspected`, `sentence_omission_suspected` |
| `medium` | Warning only (unless `retry_required=true`) | No (unless flagged) | `duplicate_line`, `paragraph_structure_merged` (non-corroborated) |
| `low` / `info` | Warning only | No | `dialogue_quote_format` |

---

## 5. Retry Boundary Contract

### 5.1 Quality Gate → Retry Decision Flow

```
Quality Gate Decision
        ↓
   retry_required?
        ↓ Yes
AdaptiveRetryPolicy.decide(outcome, attempt, max_attempts, timeout, chunk_size)
        ↓
RetryDecision { retry, delay, next_timeout, next_chunk_size, rebuild_session, switch_provider }
```

### 5.2 Retryable Outcomes (from AdaptiveRetryPolicy)

| Outcome | Category | Retry? | Delay | Chunk Size Adjustment |
|---------|----------|--------|-------|----------------------|
| `empty_output` | Quality | Yes | 0s | Halved |
| `too_short` | Quality | Yes | 0s | Halved |
| `hangul_residue` | Quality | Yes | 0s | Halved |
| `duplicate_output` | Quality | Yes | 0s | Unchanged |
| `http_429` / `http_503` | Provider | Yes | Exponential backoff | Unchanged |
| `read_timeout` / `connect_timeout` | Provider | Yes | Linear backoff | Halved |
| `connection_error` / `ssl_error` | Provider | Yes | 2×base | Unchanged |
| `retry_exhausted` | Limit | Consider provider switch | — | — |

**Evidence**: `adaptive_retry_policy.py:35-59` (RETRYABLE_OUTCOMES), `209-237` (delay/chunk_size logic).

### 5.3 Retry Boundary Rules (LOCKED)

1. **Quality Gate decides `retry_required`** → Retry orchestrator executes
2. **Retry does NOT modify quality score/decision** — only plans next attempt
3. **Max attempts enforced** — `max_attempts` (default 5) hard stop
4. **Provider switch allowed only after `provider_switch_after_attempt` (default 3)** and for `http_429`/`http_503`/`retry_exhausted`
5. **No real translation in retry decision** — `provider_called: false` in metadata

---

## 6. Best Attempt Boundary Contract

### 6.1 Current State

| Aspect | Status | Evidence |
|--------|--------|----------|
| Multiple attempt tracking | **IMPLEMENTED** | `attempt` field in retry decision, `runtime_state` tracks attempt count |
| Best attempt selection | **NOT_AUTHORIZED** | No `select_best_attempt` in production flow; `quality_repair_pipeline` returns last `quality_result` |
| Attempt comparison | **OBSERVATIONAL** | `calculate_unified_score()` exists but not used for cross-attempt selection |
| Quality score comparability | **UNDEFINED** | Scores across attempts not normalized; different source chunks may have different baselines |

**Evidence**: `quality_repair_pipeline.py:31-72` — Returns `quality_result` from current attempt, not best across attempts. `quality_decision.py:21-25` — `calculate_unified_score()` sums penalties but no cross-attempt comparison logic in production flow.

### 6.2 Best Attempt Contract (UNDEFINED)

| Requirement | Status | Notes |
|-------------|--------|-------|
| Cross-attempt score normalization | **UNDEFINED** | Different chunks = different baselines |
| Dimension weighting | **UNDEFINED** | `calculate_unified_score()` uses fixed penalties |
| Tie handling | **UNDEFINED** | Not specified |
| Minimum acceptable quality floor | **UNDEFINED** | No floor defined |

**Cannot authorize Best Attempt implementation until these are defined.**

---

## 7. Segment Recovery Boundary Contract

### 7.1 Current State

| Aspect | Status | Evidence |
|--------|--------|----------|
| Source segmentation | **IMPLEMENTED** | `segment_recovery.py:46-93` — splits on paragraph/sentence boundaries |
| Trigger conditions | **IMPLEMENTED** | `should_use_segment_recovery()` — env-gated, source ≥360 chars, completeness issues |
| Re-translation execution | **NOT_CONNECTED** | No production flow calls segment recovery for retranslation |
| Segment result merging | **NOT_IMPLEMENTED** | No logic to merge recovered segments back |

**Evidence**: `segment_recovery.py` provides segmentation logic and metadata but **no integration** with `QualityRepairPipeline` or `TranslationRuntime`.

### 7.2 Segment Recovery Contract (PARTIALLY DEFINED)

| Rule | Status |
|------|--------|
| Only for completeness issues (`empty_output`, `too_short`, `paragraph_omission`, `sentence_omission`) | ✅ Defined in `_COMPLETENESS_CODES` |
| Source ≥360 chars required | ✅ Defined |
| Conservative splitting (paragraph→sentence→char) | ✅ Implemented |
| No source text discarded | ✅ Preserved order |
| **Segment retranslation execution** | **NOT_AUTHORIZED** |
| **Segment result merging** | **NOT_DEFINED** |
| **Cross-segment consistency** | **UNDEFINED** |

---

## 8. Reviewer / Editor / ACE Boundary

| Component | Status | Production Contract |
|-----------|--------|---------------------|
| ACE (Adaptive Context Engine) | **TEST_ONLY** | `mode='disabled'|'shadow'|'active'` with fallback; no production activation |
| Literary Reviewer | **NOT_IMPLEMENTED** | No repository evidence |
| Literary Editor | **NOT_IMPLEMENTED** | No repository evidence |
| Quality Runtime | **IMPLEMENTED** | `TranslationQualityCorePipeline` + `QualityRepairPipeline` |

**ACE Evidence**: `translation_engine_v700_stage02_ace_runtime_integration_test.py` — only tests `mode='disabled'|'shadow'|'active'` with fallback. No production integration path.

**Conclusion**: Reviewer/Editor/ACE **explicitly excluded** from this contract. Quality Runtime = `TranslationQualityCorePipeline` + `QualityRepairPipeline` + `DisciplineQualityEnforcer`.

---

## 9. Undefined Policy Register

| Item | Current State | Why Undefined | Evidence Needed | Future Decision |
|------|---------------|---------------|-----------------|-----------------|
| Literary Naturalness Threshold | PS-03 proxy only (20pts) | No deterministic measurement; heuristic proxy | Human evaluation correlation; determinism proof | Requires QUALITY-CONTRACT-DESIGN |
| Overall Literary Score | PS-03 100pt aggregate | Arbitrary weights (30/20/20/15/10/5); no calibration | Benchmark against human judgment | Requires QUALITY-CONTRACT-DESIGN |
| Best Attempt Selection | Not in production flow | No cross-attempt comparison; score non-comparable | Attempt normalization method; floor definition | Requires QUALITY-CONTRACT-DESIGN |
| Retry Threshold (quality-specific) | Uses provider retry policy | Quality retry uses same policy as provider errors | Quality-specific retry limits; quality floor | Requires QUALITY-CONTRACT-DESIGN |
| Segment Recovery Quality Floor | Not defined | No merging logic; no cross-segment consistency | Segment merge strategy; consistency check | Requires QUALITY-CONTRACT-DESIGN |
| Literary Reviewer | Not implemented | No component exists | Human evaluation protocol | OUT_OF_SCOPE (future) |
| Literary Editor | Not implemented | No component exists | Edit operation definition | OUT_OF_SCOPE (future) |
| Context Continuity Gate | Feature-gated off | `quality_context_scene_v72=false` by default | Cross-chunk metrics; scene boundary quality | Feature-gate decision |
| ACE Production Activation | Test-only | No production integration path | Active mode validation; fallback reliability | OUT_OF_SCOPE (future) |

---

## 10. QUALITY_CONTRACT_V1

### 10.1 Scope

This contract covers **deterministic, machine-verifiable quality gates** currently implemented and production-integrated in the NTPE translation pipeline.

**In Scope**:
- Fidelity/Completeness (length, omissions, duplicates)
- Terminology Consistency (locked terms, forbidden variants)
- Character Consistency (via locked terms + character memory)
- Output Discipline (simplified Chinese, dialogue quotes, formatting)
- Structural Integrity (paragraph/sentence counts, duplicates)

**Out of Scope** (Unresolved / Requires Separate Design):
- Literary Naturalness / Reader Quality
- Context Continuity (cross-chunk narrative)
- Best Attempt Selection
- Segment Recovery Quality Floor
- Literary Reviewer / Editor
- ACE Production Activation

### 10.2 Quality Dimensions (Contract)

| Dimension | Gate Type | Measurement | Threshold | Failure Action |
|-----------|-----------|-------------|-----------|----------------|
| Fidelity: Empty Output | HARD_GATE | `translated.strip() == ""` | Zero tolerance | Provider retry |
| Fidelity: Length Ratio | HARD_GATE | `len(zh) / len(source)` | `min_length_ratio=0.35` (baseline) / `0.18` (LTS) | Provider retry |
| Fidelity: Paragraph Omission | HARD_GATE | `translated_paragraphs < source_paragraphs * 0.5` + corroboration | Corroborated: retry | Provider retry |
| Fidelity: Sentence Omission | HARD_GATE | `translated_sentences < source_sentences * 0.5` | Retry | Provider retry |
| Fidelity: Duplicates | HARD_GATE | `duplicate_paragraphs > 0` / `duplicate_lines > 1` | Retry | Provider retry |
| Terminology: Locked Terms | HARD_GATE | `target_term in translated` for all `source_term in source` | Zero missing | Local repair → Provider retry |
| Terminology: Forbidden Variants | HARD_GATE | `wrong_variant in translated` | Zero wrong | Local repair |
| Character Consistency | HARD_GATE | Via locked terms + character memory | Zero drift | Local repair |
| Orthography: Simplified Chinese | HARD_GATE | `any(ch in SIMPLIFIED_HINTS)` | Zero tolerance | Local repair (conversion) |
| Formatting: Dialogue Quotes | LOCAL_REPAIR | `zh_dialogue_count >= 2` if source has dialogue | Convert to `「」` | Local repair |
| Structural: Paragraph Count | HARD_GATE | `translated_paragraphs / source_paragraphs ≥ 0.5` | Retry if corroborated | Provider retry |
| Structural: Sentence Count | HARD_GATE | `translated_sentences / source_sentences ≥ 0.5` | Retry | Provider retry |

### 10.3 Gate State Contract

| State | Condition | Retry | Downstream |
|-------|-----------|-------|------------|
| `accepted` | All HARD_GATE pass; no critical/high issues | No | Output finalized |
| `accepted_with_warnings` | HARD_GATE pass; only low/medium non-retry issues | No | Output finalized |
| `retry_required` | Any HARD_GATE fail (critical/high) OR `retry_required=true` | Yes (AdaptiveRetryPolicy) | Provider retranslation |
| `rejected` | `rejected=true` issue (hallucination, added_detail) | No | Manual review |

### 10.4 Severity Contract

| Severity | Gate Effect | Retry Trigger | Examples |
|----------|-------------|---------------|----------|
| `critical` | Blocks `accepted` | **Yes** | `empty_output`, `too_short`, `hangul_residue` |
| `high` | Blocks `accepted` | **Yes** | `duplicate_paragraph`, `locked_term_missing`, `omission_suspected` |
| `medium` | Warning only | No (unless `retry_required=true`) | `duplicate_line`, `paragraph_structure_merged` (non-corroborated) |
| `low` / `info` | Warning only | No | `dialogue_quote_format` |

### 10.5 Retry Boundary Contract

| Rule | Contract |
|------|----------|
| Quality Gate `retry_required` → AdaptiveRetryPolicy | Mandatory |
| Max attempts | 5 (configurable via `max_attempts`) |
| Provider switch | After 3 attempts for `http_429`/`http_503`/`retry_exhausted` (if `allow_provider_switch=true`) |
| Chunk size reduction | Halved for `empty_output`, `too_short`, `hangul_residue`, `read_timeout` |
| Timeout increase | +30s or 1.25× for timeouts |
| No real translation in retry decision | `provider_called: false` enforced |

### 10.6 Explicit Non-Goals (Current Contract)

| Non-Goal | Reason |
|----------|--------|
| Literary Naturalness scoring | Heuristic only; no deterministic threshold |
| Reader-quality / publication readiness | Human judgment required |
| Best Attempt selection across retries | Scores not comparable across attempts |
| Segment Recovery quality merge | Not implemented; no merge strategy |
| Cross-chunk context continuity | Feature-gated off (`quality_context_scene_v72=false`) |
| Literary Reviewer / Editor execution | Not implemented |
| ACE production activation | Test-only; fallback-only design |
| Model/Provider/Prompt changes for quality | Frozen per S7 governance |

---

## 11. Future Test Contract

| Test Type | Required Coverage | Status |
|-----------|-------------------|--------|
| **UNIT** | Quality dimension evaluators (baseline, completeness, terminology, normalizer) | ✅ Existing |
| **UNIT** | Gate decision logic (`decide_quality`, `AdaptiveRetryPolicy.decide`) | ✅ Existing |
| **UNIT** | Discipline routing (`_route_for_issue`) | ✅ Existing |
| **UNIT** | Segment splitting (`split_recovery_segments`) | ✅ Existing |
| **CONTRACT** | Gate state semantics (`accepted`/`retry_required`/`rejected`) | ✅ Existing |
| **CONTRACT** | Retry decision schema validation | ✅ Existing |
| **INTEGRATION** | Quality → Repair → Retry → Rebuild pipeline | ✅ Existing (`quality_repair_pipeline_test.py`) |
| **INTEGRATION** | Unified Quality Gate + Discipline enforcement | ✅ Existing |
| **ACCEPTANCE** | Real novel translation + human literary evaluation | **NOT_AUTHORIZED** (requires real translation) |
| **ACCEPTANCE** | Cross-chunk context continuity | **FEATURE_GATED** (off by default) |

---

## 12. Production Integration Status Summary

| Component | Status | Evidence |
|-----------|--------|----------|
| TranslationQualityCorePipeline | ✅ PRODUCTION_INTEGRATED | Called by LTS pipeline |
| QualityRepairPipeline | ✅ PRODUCTION_INTEGRATED | Chains quality→repair→retry→rebuild |
| Unified Quality Gate | ✅ PRODUCTION_INTEGRATED (LTS) | Called in `run_unified_quality_gate()` |
| Discipline Enforcement | ✅ PRODUCTION_INTEGRATED | Annotates all merged issues |
| Adaptive Retry Policy | ✅ PRODUCTION_INTEGRATED | Used by QualityRetryOrchestrator |
| Quality Runtime Gate (TE-v5.2) | ⚠️ CONTRACT_ONLY | `default_mode: disabled` |
| Segment Recovery | ⚠️ FEATURE_GATED | Env var `NTPE_SEGMENT_COMPLETENESS_RECOVERY` |
| PS-03 Literary Evaluation | ❌ TOOLING_ONLY | Post-hoc, not in pipeline |
| LTS RC Quality | ❌ RELEASE_GATE | Static validation only |
| ACE / Reviewer / Editor | ❌ NOT_IMPLEMENTED / TEST_ONLY | No production path |

---

## 13. Validation Checklist (AC-01 through AC-14)

| AC | Criterion | Status | Evidence |
|----|-----------|--------|----------|
| AC-01 | Baseline verified | ✅ | HEAD = `5b41e3d` |
| AC-02 | Existing implementation evidence | ✅ | All components mapped with file:line refs |
| AC-03 | Production boundary clear | ✅ | Table in Section 12 |
| AC-04 | Quality dimensions classified | ✅ | Section 3 table |
| AC-05 | No invented thresholds | ✅ | All thresholds from code; UNDEFINED where absent |
| AC-06 | Retry boundary separated | ✅ | Section 5 |
| AC-07 | Best Attempt status clear | ✅ | Section 6 (UNDEFINED) |
| AC-08 | Segment Recovery status clear | ✅ | Section 7 (PARTIALLY DEFINED) |
| AC-09 | Reviewer/Editor excluded | ✅ | Section 8 |
| AC-10 | Model/Provider frozen | ✅ | `meta/llama-3.2-90b-vision-instruct` / `nvidia` |
| AC-11 | Test contract defined | ✅ | Section 11 |
| AC-12 | Scope compliance | ✅ | 0 production modifications |
| AC-13 | Artifact produced | ✅ | This report |
| AC-14 | No commit/push/tag | ✅ | Verified |

---

## 14. Final Verdict

```
S7_06_QUALITY_CONTRACT_DEFINED_WITH_UNDEFINED_AREAS
```

### Rationale

**Contract Defined For** (deterministic, production-integrated):
- Fidelity/Completeness gates (length, omissions, duplicates) — HARD_GATE
- Terminology/Character consistency — HARD_GATE + LOCAL_REPAIR
- Output Discipline (simplified Chinese, dialogue quotes) — HARD_GATE / LOCAL_REPAIR
- Structural Integrity — HARD_GATE
- Gate State Machine (`accepted`/`accepted_with_warnings`/`retry_required`/`rejected`)
- Retry Boundary (AdaptiveRetryPolicy) — fully specified
- Discipline Routing (local_repair / provider_retry / warning)

**Undefined Areas Requiring Separate Design Task** (cannot authorize implementation):
- Literary Naturalness / Reader Quality — heuristic only (PS-03)
- Overall Literary Score — arbitrary weights, no calibration
- Best Attempt Selection — no cross-attempt comparison
- Segment Recovery Quality Merge — not implemented
- Context Continuity — feature-gated off
- Literary Reviewer / Editor / ACE — not implemented

**No Production Defects Identified**. Existing quality pipeline operates within defined contract boundaries. All production-integrated components enforce `provider_called: false`, `real_translation_executed: false`.

---

*End of Audit Report*

**Report Path**: `artifacts/NTPE_S7_06_LITERARY_QUALITY_CONTRACT_AUDIT_REPORT.md`
**Audit Complete**: `S7_06_QUALITY_CONTRACT_DEFINED_WITH_UNDEFINED_AREAS`