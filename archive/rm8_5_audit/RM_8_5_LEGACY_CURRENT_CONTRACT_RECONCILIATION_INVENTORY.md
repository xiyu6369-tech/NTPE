# RM-8.5 Legacy / Current Contract Reconciliation Inventory

**Date**: 2026-08-14  
**Status**: READ-ONLY INVENTORY — NO MODIFICATIONS MADE  
**Baseline Commit**: 3199039 (RM-8.5 Phase 1 completed)

---

## 1. Executive Summary

This inventory systematically compares **Runtime**, **Governance**, **Specification**, **Tests**, and **Implementation** across all contract surfaces in the NTPE repository. The goal is to identify the **single authoritative contract** at each layer and expose drift.

### Key Findings

| Layer | Authority | Drift Detected? | Critical Issues |
|-------|-----------|-----------------|-----------------|
| **Runtime Contract** | `core/translation_runtime/runtime_contract.py` + `core/translation_runtime/runtime.py` | ������ YES | Pipeline version mismatch: `1.2-professional-stage-14.2` vs RM-8.x series |
| **Governance Baseline** | `docs/governance/repository/REPOSITORY_GOVERNANCE_BASELINE.md` | �� CLEAR | Single source of truth established at commit 806ac7c |
| **RM-8.5 Phase 1 Spec** | `docs/governance/rm8/RM_8_5_IMPLEMENTATION_SPECIFICATION.md` | ������ YES | Enum values in spec differ from actual `NarrativeState.to_prompt_context()` runtime contract |
| **RM-8.5 Phase 2 Spec** | `docs/governance/rm8/RM_8_5_PHASE2_IMPLEMENTATION_SPECIFICATION.md` | ��� BLOCKED | `[THIRD STRUCTURAL GATE]` is a **placeholder**, not an existing gate; Category A candidates �� "3 gates + 2 signals" |
| **Phase 1 Implementation** | `core/translation_release/validator.py` (commit 3199039) | ������ YES | Fixed enum drift from commit 84a46cd; now matches spec |
| **Tests** | `tests/unit/translation_release/test_validator.py` | �� ALIGNED | Tests use production-shaped fixtures matching `NarrativeState.to_prompt_context()` |
| **AI Governance** | Distributed across RM-5.6.1, Repository Baseline, RM-8.x specs | ��� GAPS | No single document defines "AI must read X before modifying Y"; commit/push protocol implicit |

### Critical Drift: Enum Value Mismatch

The **most significant contract drift** is between what the **runtime actually produces** (`NarrativeState.to_prompt_context()`) and what **specifications assume**:

| Field | Runtime Contract (Actual) | RM-8.5 Spec (Phase 1) | Commit 84a46cd (Wrong) | Commit 3199039 (Fixed) |
|-------|---------------------------|------------------------|------------------------|------------------------|
| `perspective` | `first_person` \| `second_person` \| `third_person` \| `unknown` | �� Match | ��� `third_person_limited` \| `third_person_omniscient` | �� Match |
| `voice` | `neutral` \| `dialogue_driven` \| `descriptive` \| `balanced` | �� Match | ��� `formal` \| `casal` \| `literary` \| `mixed` | �� Match |
| `tense` | `past` \| `present` \| `undetermined` | �� Match | ��� `future` \| `mixed` | �� Match |

**Commit 3199039 corrected this drift** — the implementation now matches the specification and the actual runtime contract.

---

## 2. Current Runtime Source-of-Truth Map

### 2.1 Translation Runtime Contract (Authoritative)

**File**: `core/translation_runtime/runtime_contract.py:19-112`

```python
# Canonical runtime contract — additive, backward-compatible
REQUIRED_ENTRYPOINTS: tuple[str, ...] = (
    "translate_package_file", "translate_package", "translate_txt", "translate_batch",
    "main_txt", "main_batch", "analyze_quality", "checkpoint", "checkpoint_error",
    "checkpoint_completed", "recovery_summary", "create_session", "list_sessions",
    "translate_package_file_session", "describe_pipeline", "validate_pipeline",
    "execute_pipeline", "save_pipeline_manifest", "bind_ai_provider_manager",
    "register_ai_provider", "complete_provider_prompt", "stream_provider_prompt",
    "discover_provider_models", "detect_provider_capabilities", "provider_health_check",
    "provider_manifest", "provider_config_manifest", "validate_provider_credentials",
    "save_provider_config_template",
)

OFFICIAL_PIPELINE: tuple[str, ...] = (
    "Encoding", "Chunk", "Context", "Glossary", "Character Memory",
    "Prompt Builder", "AI Provider", "QA", "Taiwan Formatter", "Output",
)

RUNTIME_CAPABILITIES: tuple[RuntimeCapability, ...] = (
    RuntimeCapability("package_translation", True, "..."),
    RuntimeCapability("txt_translation", True, "..."),
    RuntimeCapability("batch_translation", True, "..."),
    RuntimeCapability("encoding_normalization", True, "..."),
    RuntimeCapability("chunking", True, "..."),
    RuntimeCapability("taiwan_formatter", True, "..."),
    RuntimeCapability("lts_compatibility", True, "..."),
    RuntimeCapability("provider_boundary", True, "..."),
    RuntimeCapability("qa_boundary", True, "..."),
    RuntimeCapability("runtime_recovery", True, "..."),
    RuntimeCapability("translation_session", True, "..."),
    RuntimeCapability("translation_pipeline", True, "..."),
    RuntimeCapability("ai_provider_framework", True, "..."),
    RuntimeCapability("provider_runtime_binding", True, "..."),
    RuntimeCapability("provider_config_layer", True, "..."),
)
```

**Version**: `1.2-professional-stage-14.2` (from `core/translation_runtime/runtime.py:34`)

### 2.2 Translation Request/Response Models (RM-6.2.2)

**File**: `core/translation_runtime/models.py:43-125`

```python
@dataclass(frozen=True)
class TranslationRequest:
    prompt: str
    metadata: Dict[str, Any]  # Includes context_state from RM-8.2
    runtime_snapshot: Dict[str, Any]
    snapshot_id: str
    prompt_hash: str
    section_count: int
    token_count: int
    build_timestamp: str
    version: str = "rm-6.2.2"

@dataclass(frozen=True)
class TranslationResponse:
    prompt: str
    request: TranslationRequest
    version: str = "rm-6.2.2"
```

### 2.3 Runtime Pipeline Switch (RM-6.4.2)

**Control**: `NTPE_RUNTIME_PIPELINE` env var (`runtime` | `legacy`, default: `runtime`)

- **Runtime Mode**: Uses `RuntimeOrchestrator` → `KnowledgeRuntime` → `PromptBuilder` → `TranslationRuntimeAdapter` → `TranslationEngine.translate_package_from_request()`
- **Legacy Mode**: Uses `lts/txt_translation_runtime.py` chunk loop directly

### 2.4 RM-8.2 Context State Serialization (Actual Runtime Output)

**Composed in**: `lts/txt_translation_runtime.py:784-791`

```python
context_state_metadata = {
    "context_selection_fingerprint": selection.fingerprint,        # str (SHA256)
    "scene_id": current_scene_id,                                   # str
    "scene_version": context_store.get_scene(current_scene_id).scene_version,  # int
    "narrative": narrative_context,                                 # dict from NarrativeState.to_prompt_context()
    "boundary": boundary.to_dict(),                                 # dict from BoundaryResult
    "selected_context_ids": tuple(r.item_id for r in selection.selected_records),  # tuple[str]
}
```

**What IS Serialized in chunk_records**:
- `scene_id`, `scene_version`, `chapter_id` ��
- `boundary.type` ∈ {`same_scene`, `scene_transition`, `chapter_transition`, `unknown_transition`} ��
- `narrative.perspective` ∈ {`first_person`, `second_person`, `third_person`, `unknown`} ��
- `narrative.voice` ∈ {`neutral`, `dialogue_driven`, `descriptive`, `balanced`} ��
- `narrative.tense` ∈ {`past`, `present`, `undetermined`} ��
- `narrative.emotional_tone` ∈ {`neutral`, `tense`, `calm`, `joyful`, `sad`, `angry`, `fearful`, `mixed`} ��

**What is NOT Serialized** (Critical Gaps per Audit):
- Actual `TERMINOLOGY_STATE` values (source_term → translated_term) ���
- `SceneMemoryRecord.active_speaker` ���
- `SceneMemoryRecord.participants` ���
- `SceneMemoryRecord.point_of_view` ���
- `SceneMemoryRecord.unresolved_references` ���
- Per-chunk translation text ���

### 2.5 RM-8.3 Delivery Pipeline Contract

**Feature Flag**: `quality_delivery_v83` (default: `False`)

**Entry Point**: `core/translation_release/delivery_pipeline.py:90` → `run_delivery_pipeline()`

**Immutable Outputs**:
- `DeliveryResult` (status, output_path, manifest_path, qc_certificate_path, epub_path?, pdf_path?)
- `DeliveryManifest` (frozen dataclass with all pipeline metadata)
- `QualityCertificate` (6 dimension scores + `checks` dict)

**Validation Gate**: `validate_final_novel()` in `core/translation_release/validator.py:28`

---

## 3. Historical Architecture Map

### 3.1 Document Classification

| Document | Classification | Superseded By | Notes |
|----------|----------------|---------------|-------|
| `REPOSITORY_GOVERNANCE_BASELINE.md` | **CURRENT** | — | Master authority; commit 806ac7c |
| `ROOT_POLICY.md` | **CURRENT** | — | Root allowlist enforced by `ntpe_validate.py` |
| `TOOLS_POLICY.md` | **CURRENT** | — | 7 tool categories under `tools/` |
| `ARCHIVE_POLICY.md` | **CURRENT** | — | Archive is read-only; no prod/test imports |
| `DIRECTORY_OWNERSHIP.md` | **CURRENT** | — | Cross-directory import boundaries |
| `RM_5_ARCHITECTURE_BASELINE.md` | **HISTORICAL** | RM-6+ Runtime | Frozen at RM-4; describes pre-RM-5 architecture |
| `RM_5_3_RUNTIME_CONTEXT_INTEGRATION.md` | **HISTORICAL** | RM-6 Runtime | TQI V72 Adapter integration (completed) |
| `RM_5_6_1_ROOT_HYGIENE.md` | **HISTORICAL** | Repository Baseline | Root hygiene rules now in Baseline |
| `RM_6_4_2_PRODUCTION_RUNTIME_SWITCH.md` | **CURRENT** | — | Runtime switch mechanism; env var controlled |
| `RM_8_1_IMPLEMENTATION_SPECIFICATION.md` | **HISTORICAL** | RM-8.2+ | Literary quality enforcement (merged) |
| `RM_8_2_IMPLEMENTATION_SPECIFICATION.md` | **CURRENT** | — | Cross-chunk context; feature-gated `quality_context_scene_v72` |
| `RM_8_3_IMPLEMENTATION_SPECIFICATION.md` | **CURRENT** | — | Polish + Delivery; feature-gated `quality_delivery_v83` |
| `RM_8_4_IMPLEMENTATION_SPECIFICATION.md` | **CURRENT** | — | Reader Structure / EPUB; `ReaderChapterMap` from RM-8.3 TXT |
| `RM_8_5_IMPLEMENTATION_SPECIFICATION.md` | **CURRENT** | — | Cross-chunk semantic gates (2 gates implemented) |
| `RM_8_5_PHASE2_IMPLEMENTATION_SPECIFICATION.md` | **SUPERSEDED** | — | Specifies 3 gates + 2 signals; **3rd gate is placeholder** |
| `RM_8_5_SPEC_CONSISTENCY_AUDIT.md` | **CURRENT** | — | Audit that blocked 4/6 gates; authorized 2 gates |
| `NTPE_REPOSITORY_STATUS_REPORT.md` | **HISTORICAL** | Repository Baseline | Pre-baseline status report |

### 3.2 RM Evolution Timeline

```
RM-3.1  → Repository Governance Baseline (806ac7c)
RM-4    → Freeze
RM-5    → Architecture Baseline, Runtime Context Integration (TQI V72), Root Hygiene
RM-6    → Runtime Pipeline (Orchestrator, Knowledge, Prompt, Adapter, Session, Checkpoint, Trace)
RM-6.4.2 → Production Runtime Switch (NTPE_RUNTIME_PIPELINE env var)
RM-7    → Entity Resolution, Review, Knowledge Evolution
RM-8.1  → Literary Quality Enforcement
RM-8.2  → Cross-Chunk Context/Scene/Narrative (feature-gated)
RM-8.3  → Polish + Delivery Pipeline (quality_delivery_v83)
RM-8.4  → ReaderChapterMap + Optional EPUB (Reader Structure Layer)
RM-8.5  → Cross-Chunk Semantic Gates (2 gates: POV continuity, Tense/Voice consistency)
```

---

## 4. Contract Authority / Precedence Model

### 4.1 Precedence Hierarchy (Highest → Lowest)

```
1. PRODUCTION RUNTIME CODE (Source of Truth)
   └─ core/translation_runtime/*.py
   └─ lts/txt_translation_runtime.py (actual serialization)
   └─ core/translation_release/*.py (actual validation)

2. REPOSITORY GOVERNANCE BASELINE
   └─ REPOSITORY_GOVERNANCE_BASELINE.md (master)
   └─ ROOT_POLICY.md, TOOLS_POLICY.md, ARCHIVE_POLICY.md, DIRECTORY_OWNERSHIP.md

3. IMPLEMENTATION SPECIFICATIONS (Authoritative for their RM)
   └─ RM_8_2_IMPLEMENTATION_SPECIFICATION.md
   └─ RM_8_3_IMPLEMENTATION_SPECIFICATION.md
   └─ RM_8_4_IMPLEMENTATION_SPECIFICATION.md
   └─ RM_8_5_IMPLEMENTATION_SPECIFICATION.md (as revised post-audit)

4. SPECIFICATION CONSISTENCY AUDITS
   └─ RM_8_5_SPEC_CONSISTENCY_AUDIT.md (binds RM-8.5 scope)

5. TESTS (Verify contracts; do not define them)
   └─ tests/unit/translation_release/test_validator.py
   └─ tests/unit/translation_runtime/test_boundary_detector.py

6. HISTORICAL / SUPERSEDED DOCUMENTS
   └─ RM_5_ARCHITECTURE_BASELINE.md
   └─ RM_8_5_PHASE2_IMPLEMENTATION_SPECIFICATION.md (3rd gate = placeholder)
```

### 4.2 Key Principle

> **Runtime wins over Specification.**  
> Specifications describe *intent*; runtime code proves *behavior*.  
> When they conflict, the runtime contract (actual serialized data, actual enum values, actual function signatures) is the authoritative contract.

---

## 5. Runtime vs Governance vs Specification vs Tests Drift Matrix

### 5.1 Enum Drift (RESOLVED in commit 3199039)

| Contract Element | Runtime (Actual) | Spec (RM-8.5) | Commit 84a46cd | Commit 3199039 | Tests |
|------------------|------------------|---------------|----------------|----------------|-------|
| `perspective` values | `first_person`, `second_person`, `third_person`, `unknown` | �� Match | ��� `third_person_limited`, `third_person_omniscient` | �� Fixed | �� Match |
| `voice` values | `neutral`, `dialogue_driven`, `descriptive`, `balanced` | �� Match | ��� `formal`, `casual`, `literary`, `mixed` | �� Fixed | �� Match |
| `tense` values | `past`, `present`, `undetermined` | �� Match | ��� `future`, `mixed` | �� Fixed | �� Match |
| `boundary.type` values | `same_scene`, `scene_transition`, `chapter_transition`, `unknown_transition`, `manual_boundary` | �� Match | �� Match | �� Match | �� Match |

### 5.2 Feature Flag Contract

| Flag | Default | Runtime Behavior | Spec | Tests |
|------|---------|------------------|------|-------|
| `quality_delivery_v83` | `False` | Gate skipped; 9 checks only | �� Feature-gated | �� Verified: 9 checks when OFF, 11 when ON |
| `quality_context_scene_v72` | `False` | RM-8.2 context injection skipped | �� Feature-gated | Not directly tested in validator tests |

### 5.3 Validation Gate Contract

| Check | Severity (Runtime) | Severity (Spec) | Fail-Open? | Tests Verify |
|-------|-------------------|-----------------|------------|--------------|
| `paragraph_structure` | `critical` | `critical` | N/A | �� |
| `punctuation_consistency` | `major` | `major` | N/A | �� |
| `korean_residue_global` | `critical` | `critical` | N/A | �� |
| `locked_term_compliance` | `major` | `major` | N/A | �� |
| `length_ratio_global` | `major`/`info` | `major` | N/A | �� |
| `chinese_char_ratio` | `minor` | `minor` | N/A | �� |
| `repeated_lines_global` | `minor` | `minor` | N/A | �� |
| `quote_balance` | `minor` | `minor` | N/A | �� |
| `empty_content` | `info` | `info` | N/A | �� |
| `narrative_pov_continuity` | `minor` | `minor` | �� FAIL-OPEN | �� All scenarios |
| `tense_voice_consistency` | `minor` | `minor` | �� FAIL-OPEN | �� All scenarios |

### 5.4 Data Structure Contracts

| Structure | Runtime Production | Spec | Tests | Drift |
|-----------|-------------------|------|-------|-------|
| `ValidationCheck` | name, passed, score, details, severity | �� Match | �� Match | None |
| `ValidationResult` | overall_passed, overall_score, checks, failed_critical, failed_major | �� Match | �� Match | None |
| `QualityCertificate` | 6 dimension scores + `checks` dict | **NO NEW DIMENSIONS** | �� Uses existing `checks` | None (spec compliant) |
| `DeliveryManifest` | Full pipeline metadata | �� Match | Not directly tested | None |

### 5.5 Boundary Semantics Contract

| Aspect | Runtime (`boundary_detector.py`) | Spec (RM-8.2, RM-8.5) | Tests |
|--------|----------------------------------|------------------------|-------|
| `SAME_SCENE` | Default (confidence 1.0) | �� | �� |
| `SCENE_TRANSITION` | Explicit markers only (`***`, `第N節`, `Scene N`) | �� Conservative | �� |
| `CHAPTER_TRANSITION` | Explicit markers only (`第N章`, `Chapter N`) | �� Conservative | �� |
| `UNKNOWN_TRANSITION` | Heuristics (location/time/speaker) — NO auto scene_id | �� Conservative | �� Verified: `scene_id is None` |
| Auto scene_id generation | **REMOVED** (line 154: `# REMOVED: _generate_scene_id()`) | �� Explicit only | �� Test: `test_no_auto_scene_id_generation` |

---

## 6. RM-8.5 Phase 1 Contract Findings

### 6.1 Scope as Implemented (Commit 3199039)

**Authorized by**: `RM_8_5_SPEC_CONSISTENCY_AUDIT.md` Section 11 (CLEAR → Phase 1)

**Two Gates Implemented**:
1. `narrative_pov_continuity` — Minor, FAIL-OPEN, unknown = no false positive
2. `tense_voice_consistency` — Minor, FAIL-OPEN, unknown = no false positive

### 6.2 Contract Compliance Verification

| Requirement | Spec | Implementation | Tests | Status |
|-------------|------|----------------|-------|--------|
| Only 2 checks | �� | �� 2 functions added | �� | PASS |
| Both minor severity | �� | �� `severity="minor"` | �� Asserted | PASS |
| FAIL-OPEN mandatory | �� | �� try/except → pass | �� Exception, missing, unknown all pass | PASS |
| `unknown` = no false positive | �� | �� Explicit skip logic | �� `unknown_skipped` in details | PASS |
| Feature-gated (`quality_delivery_v83`) | �� | �� Guarded by flag | �� 9 vs 11 checks verified | PASS |
| No QualityCertificate changes | �� | �� Uses existing `checks` dict | �� | PASS |
| No metadata.py/models.py changes | �� | �� No modifications | �� | PASS |
| Zero provider/network calls | �� | �� Pure Python | �� | PASS |
| Deterministic | �� | �� Same input → same output | �� | PASS |

### 6.3 Implementation Drift from Spec (Minor)

| Spec Section | Spec Says | Implementation Does | Impact |
|--------------|-----------|---------------------|--------|
| `narrative_pov_continuity` Score | `100 - (unauthorized_changes × 25)` | �� Matches | None |
| `tense_voice_consistency` Score | `100 - (tense_violations × 15 + voice_violations × 10)` | �� Matches | None |
| `narrative_pov_continuity` unknown handling | "NEVER flag as violation" | �� Skips comparison | None |
| `tense_voice_consistency` unknown handling | "NEVER flag as violation" | �� Skips comparison | None |
| Missing narrative data | Not explicitly specified | �� Treated as `unknown_skipped = True` | Slightly more permissive (good) |

---

## 7. RM-8.5 Phase 2 Specification Drift Findings

### 7.1 Category A Candidates vs Phase 2 Spec — FUNDAMENTAL MISMATCH

**RM-8.5 Spec Consistency Audit (Section 10)** authorized **only 2 structural gates**:
- `narrative_pov_continuity`
- `tense_voice_consistency`

**Phase 2 Specification claims** (Section 2 Architecture Overview):
> "STRUCTURAL GATES (Phase 2 registration): narrative_pov_continuity, tense_voice_consistency, **[THIRD STRUCTURAL GATE]**"

### 7.2 `[THIRD STRUCTURAL GATE]` — EXPLICIT JUDGMENT

**Classification**: **PLACEHOLDER / FUTURE SPECULATION** — NOT an existing gate

**Evidence**:
1. Audit Section 9: Only 2 gates have "viable data" → `CONDITIONAL PASS`
2. Audit Section 10: "Authorized Scope" lists only 2 gates
3. Phase 2 Spec Section 4.1.3: "Status: Not implemented in RM-8.5 Phase 2. Specification provided for completeness and future planning."
4. Proposed candidate `cross_chunk_entity_consistency` requires serializing full `TERMINOLOGY_STATE` → **NOT in chunk_records** (Audit Section 1.3)

**Verdict**: The `[THIRD STRUCTURAL GATE]` is a **documentation placeholder** for potential future RM (RM-8.6+), not a current contract element. It must not be treated as an existing gate.

### 7.3 Diagnostic Signals — NOT REGISTERED (Correct)

| Signal | Phase 2 Spec | Implementation Status | Correct? |
|--------|--------------|----------------------|----------|
| `pronoun_consistency` | Specified (Section 4.2.1) | **NOT registered** in `validate_final_novel()` | �� Correct — Audit BLOCKED |
| `emotional_tone_coherence` | Specified (Section 4.2.2) | **NOT registered** in `validate_final_novel()` | �� Correct — Audit BLOCKED |

**Test Verification**: `test_diagnostic_signals_not_registered()` explicitly asserts these are NOT in `ValidationResult.checks`.

### 7.4 Phase 2 Spec Compliance Issues

| Issue | Severity | Detail |
|-------|----------|--------|
| Claims "3 structural gates" | **HIGH** | Only 2 exist; 3rd is placeholder |
| "Category A candidates" mismatch | **HIGH** | Audit authorized 2; Spec implies 3+ |
| Diagnostic signals in architecture diagram | **MEDIUM** | Shows in diagram but correctly not registered |
| Severity for diagnostic signals = `info` | **LOW** | Spec says `info`; correct for non-gates |

---

## 8. AI Governance Gap Analysis

### 8.1 Current Governance Documents Reviewed

| Document | AI Rules Present? | What It Covers |
|----------|-------------------|----------------|
| `REPOSITORY_GOVERNANCE_BASELINE.md` | ��� No | Repository structure, migration principles, validation |
| `ROOT_POLICY.md` | ��� No | Root allowlist, forbidden patterns |
| `TOOLS_POLICY.md` | ��� No | Tool categories, cross-tool rules |
| `DIRECTORY_OWNERSHIP.md` | ��� No | Directory ownership, import boundaries |
| `ARCHIVE_POLICY.md` | ��� No | Archive lifecycle, read-only rule |
| `RM_5_6_1_ROOT_HYGIENE.md` | ������ Partial | `.clinerules` update; prohibits root test_*.py etc. |
| `RM_8_5_IMPLEMENTATION_SPECIFICATION.md` | ������ Partial | "Specification Consistency Audit CLEAR → commit authorized" |
| `RM_8_5_SPEC_CONSISTENCY_AUDIT.md` | ������ Partial | Audit process; "Audit CLEAR → implementation authorized" |

### 8.2 Missing AI Governance Rules (Explicit Gaps)

| Required Rule | Current Status | Gap |
|---------------|----------------|-----|
| **AI must read CURRENT contracts before modifying** | ��� Not documented | No single "AI_READ_FIRST.md" listing authoritative contracts |
| **Which documents are NOT runtime contracts** | ��� Not documented | Historical specs (RM-5, RM-8.5 Phase 2 placeholder) not marked |
| **Root hygiene for AI** | ������ In `.clinerules` | Not in governance baseline; `.clinerules` not versioned in repo |
| **Artifact placement rules** | ������ Partial | `artifacts/` in Directory Ownership; no AI-specific guidance |
| **Implementation authorization protocol** | ������ Implicit | "Audit CLEAR → commit authorized" but no formal gate |
| **Specification consistency audit requirement** | �� Exists | RM-8.5 audit pattern established; should be generalized |
| **Commit / push / tag protocol** | ��� Not documented | No rules on when AI may commit/push/tag |

### 8.3 Implicit Protocol (Discovered from History)

From git history and audit documents, the **de facto protocol** is:
1. Specification written → Specification Consistency Audit → **CLEAR** → Implementation Authorized
2. Implementation → Unit Tests → Canary → Regression Suite → **ntpe_validate.py PASS** → **compileall PASS** → **git diff --check PASS**
3. **ChatGPT Acceptance Review** (human) → Commit authorized

**This protocol is not codified in any governance document.**

---

## 9. Required Reconciliation Actions

### 9.1 Immediate (Contract Unification)

| Action | Priority | Owner | Description |
|--------|----------|-------|-------------|
| **Publish "AI Contract Reference" document** | P0 | Governance | Single file listing: Current Runtime Contract, Current Specs, Forbidden Historical Docs |
| **Mark RM_8_5_PHASE2_IMPLEMENTATION_SPECIFICATION.md as SUPERSEDED/PLACEHOLDER** | P0 | Governance | Add banner: "3rd gate = placeholder; only 2 gates authorized per Audit" |
| **Version the `.clinerules` in repo** | P1 | Governance | Add `.clinerules` to repo (or `docs/governance/ai_rules.md`) with root hygiene, artifact placement |
| **Codify commit/push/tag protocol** | P1 | Governance | Document: "No commit without Audit CLEAR + ntpe_validate PASS + compileall PASS + human review" |

### 9.2 Contract Corrections (No Code Changes — Documentation Only)

| Document | Correction | Reason |
|----------|------------|--------|
| `RM_8_5_PHASE2_IMPLEMENTATION_SPECIFICATION.md` | Change "3 structural gates" → "2 structural gates registered; 3rd reserved for future" | Prevents future implementation drift |
| `RM_8_5_PHASE2_IMPLEMENTATION_SPECIFICATION.md` | Clarify diagnostic signals are "specified for future/informational only" | Already correct in implementation; doc should match |
| `RM_8_5_SPEC_CONSISTENCY_AUDIT.md` | Add "This audit binds RM-8.5 scope permanently" | Makes audit authority explicit |

### 9.3 Test Contract Verification

| Test Area | Action | Status |
|-----------|--------|--------|
| Enum value tests | Add `test_enum_values_match_runtime_contract()` | Not yet present |
| Feature flag behavior | Already verified in `TestRM85FeatureFlag` | �� PASS |
| FAIL-OPEN behavior | Already verified in `TestRM85SemanticChecks` | �� PASS |
| Production-shaped fixtures | Already in `TestRM85ProductionShapedFixtures` | �� PASS |

---

## 10. Explicit Non-Actions

The following are **NOT required** and **NOT recommended** based on this inventory:

| Non-Action | Reason |
|------------|--------|
| ��� Do NOT implement 3rd structural gate | No data in chunk_records; Audit BLOCKED; placeholder only |
| ��� Do NOT register diagnostic signals as gates | Audit BLOCKED (high false-positive, insufficient data) |
| ��� Do NOT modify QualityCertificate schema | Spec explicitly forbids; `checks` dict sufficient |
| ��� Do NOT modify metadata.py / models.py | Spec explicitly forbids; no need |
| ��� Do NOT change RM-8.2 serialization | Would break RM-8.3/8.4/8.5; only additive changes allowed |
| ��� Do NOT modify production runtime code | This is READ-ONLY inventory |
| ��� Do NOT archive or delete historical specs | Archive Policy: read-only, frozen with SHA-256 |
| ��� Do NOT auto-generate scene_id from heuristics | Boundary detector explicitly REMOVED `_generate_scene_id()` |

---

## 11. Recommendation: Should RM-8.5 Phase 2 Continue?

### 11.1 Current Contract State

**CLEAR for Phase 1** (2 gates implemented, tested, FAIL-OPEN verified).

**BLOCKED for Phase 2 as currently specified** because:
- The specification describes **3 structural gates** but only **2 exist**
- The `[THIRD STRUCTURAL GATE]` is a **placeholder**, not a current contract element
- Category A candidates �� "3 gates + 2 signals" — this is a specification error

### 11.2 Decision Matrix

| Option | Assessment |
|--------|------------|
| **Proceed with Phase 2 as-written** | ��� **REJECT** — Would implement a non-existent 3rd gate |
| **Revise Phase 2 Spec to match Audit (2 gates only), then proceed** | �� **RECOMMENDED** — Aligns spec with actual authorized scope |
| **Defer Phase 2 until RM-8.6 when 3rd gate data exists** | ������ **ACCEPTABLE** — If no immediate need for registration |

### 11.3 Recommended Path

1. **Revise `RM_8_5_PHASE2_IMPLEMENTATION_SPECIFICATION.md`**:
   - Change "3 structural gates" → "2 structural gates"
   - Mark `[THIRD STRUCTURAL GATE]` as "Future placeholder (RM-8.6+)"
   - Clarify diagnostic signals are "not registered, informational only"

2. **Re-run Specification Consistency Audit** on revised spec

3. **If Audit CLEAR** → Authorize Phase 2 implementation (registration only, ~20 lines)

4. **Phase 2 Scope** (per revised spec):
   - Register the 2 existing check functions in `validate_final_novel()` under `quality_delivery_v83` guard
   - Add registration tests (already specified in Phase 2 spec Section 6.1)
   - Verify diagnostic signals are NOT registered (test in Section 6.2)

---

## 12. Appendix: Key Contract References

### 12.1 Runtime Contract Files (Source of Truth)

| Contract | File | Line Range |
|----------|------|------------|
| Runtime Entry Points | `core/translation_runtime/runtime_contract.py` | 42-72 |
| Official Pipeline | `core/translation_runtime/runtime_contract.py` | 73-84 |
| Runtime Capabilities | `core/translation_runtime/runtime_contract.py` | 86-102 |
| TranslationRequest/Response | `core/translation_runtime/models.py` | 43-125 |
| TranslationRuntime Facade | `core/translation_runtime/runtime.py` | 26-247 |
| Context State Serialization | `lts/txt_translation_runtime.py` | 784-791 |
| Boundary Detection | `core/translation_runtime/boundary_detector.py` | 63-136 |
| Narrative State (to_prompt_context) | `core/intelligence/narrative_state.py` | (external) |

### 12.2 Governance Contract Files

| Contract | File |
|----------|------|
| Repository Baseline | `docs/governance/repository/REPOSITORY_GOVERNANCE_BASELINE.md` |
| Root Policy | `docs/governance/repository/ROOT_POLICY.md` |
| Tools Policy | `docs/governance/repository/TOOLS_POLICY.md` |
| Directory Ownership | `docs/governance/repository/DIRECTORY_OWNERSHIP.md` |
| Archive Policy | `docs/governance/repository/ARCHIVE_POLICY.md` |

### 12.3 Specification Contract Files (Current)

| Spec | File | Status |
|------|------|--------|
| RM-8.2 Cross-Chunk Context | `docs/governance/rm8/RM_8_2_IMPLEMENTATION_SPECIFICATION.md` | CURRENT |
| RM-8.3 Polish + Delivery | `docs/governance/rm8/RM_8_3_IMPLEMENTATION_SPECIFICATION.md` | CURRENT |
| RM-8.4 Reader Structure | `docs/governance/rm8/RM_8_4_IMPLEMENTATION_SPECIFICATION.md` | CURRENT |
| RM-8.5 Semantic Gates (Phase 1) | `docs/governance/rm8/RM_8_5_IMPLEMENTATION_SPECIFICATION.md` | CURRENT |
| RM-8.5 Phase 2 | `docs/governance/rm8/RM_8_5_PHASE2_IMPLEMENTATION_SPECIFICATION.md` | **SUPERSEDED — NEEDS REVISION** |
| RM-8.5 Audit | `docs/governance/rm8/RM_8_5_SPEC_CONSISTENCY_AUDIT.md` | CURRENT (BINDING) |

### 12.4 Test Contract Files

| Test | File |
|------|------|
| Validator Tests | `tests/unit/translation_release/test_validator.py` |
| Boundary Detector Tests | `tests/unit/translation_runtime/test_boundary_detector.py` |
| Delivery Pipeline Tests | `tests/unit/translation_release/test_delivery_pipeline.py` |

---

## 13. Conclusion

**The Current Contract is now uniquely identifiable** after this inventory:

1. **Runtime Contract** = Actual production code in `core/translation_runtime/`, `lts/txt_translation_runtime.py`, `core/translation_release/`
2. **Governance Contract** = `REPOSITORY_GOVERNANCE_BASELINE.md` + 4 policy docs
3. **Specification Contract** = RM-8.2, RM-8.3, RM-8.4, RM-8.5 (Phase 1) specs + **RM-8.5 Audit (binding)**
4. **Test Contract** = Unit tests using production-shaped fixtures matching `NarrativeState.to_prompt_context()`

**Critical Drift Resolved**: Enum value mismatch between runtime and spec was **fixed in commit 3199039**.

**Remaining Specification Error**: `RM_8_5_PHASE2_IMPLEMENTATION_SPECIFICATION.md` claims 3 structural gates; only 2 exist. **Must be revised before any Phase 2 implementation**.

**AI Governance Gap**: No single document tells AI agents "read these contracts first; ignore these historical docs; follow this commit protocol." This should be codified.

---

**END OF INVENTORY**  
**READ-ONLY — NO MODIFICATIONS MADE**  
**Awaiting Acceptance Review**