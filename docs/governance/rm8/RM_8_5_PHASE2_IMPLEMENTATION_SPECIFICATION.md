# RM-8.5 Phase 2 Implementation Specification
## Registration of Cross-Chunk Semantic Checks and Specification of 2 Structural Gates + 2 Diagnostic Signals

---

### 1. SCOPE & PRINCIPLES

**Objective**: Register the two validated cross-chunk semantic checks (narrative_pov_continuity, tense_voice_consistency) into the RM-8.3 delivery validation pipeline via `validate_final_novel()`, and fully specify the algorithms, legal states, FAIL-OPEN behavior, boundary semantics, unknown/undetermined handling, test matrix, and prohibited derivations for the complete set of 2 structural gates and 2 diagnostic signals identified in the RM-8.5 Specification Consistency Audit.

**Non-Objectives**:
- No modification of `validator.py`, `tests`, or RM-8.2~8.4 production code (this specification is for documentation and future implementation guidance only)
- No new provider/LLM/network calls
- No re-translation, re-chunking, re-assembly, re-polishing
- No modification of RM-8.2 propagation logic
- No modification of RM-8.3 TXT Source of Truth
- No auto-fix/correction (detection only)
- No synthetic semantic score (0–100)
- No human review interfaces
- No RM-7/RM-8.1/RM-8.2/RM-8.3/RM-8.4 scope creep

| Principle | Decision |
|---|---|
| Detection | Pure Python regex/string analysis on final assembled text + RM-8.2 metadata (where available) |
| Classification | Extend existing `ValidationCheck` pattern (critical/major/minor/info) |
| Enforcement | Integrate into RM-8.3 weighted scoring (PASS ≥ 70, no critical failures) — **only structural gates affect score** |
| Metrics | **NO new dimension scores in QualityCertificate** — use existing `checks` dictionary |
| Propagation | Validator → DeliveryManifest (via existing `checks` in ValidationResult) |
| Compatibility | Feature-gated by existing `quality_delivery_v83` (default OFF) |
| Provider Cost | Zero additional requests |
| **Fail-Open** | **MANDATORY — any error/unknown → check passes, never fails delivery** |
| **Unknown Handling** | **`unknown` = "indeterminate, no false positive" — explicitly defined per check** |

---

### 2. ARCHITECTURE OVERVIEW

```
RM-8.3 Delivery Pipeline (existing)
    │
    ├─ assembled_text (polished TXT body)
    ├─ chunk_records (with metadata.context_state from RM-8.2)
    ├─ locked_dictionary
    └─ options
            │
            ��� ��
validate_final_novel()  ← EXTENDED to register 2 structural checks (Phase 2)
    │
    ├─ Existing 9 checks (paragraph, punctuation, korean, locked_terms, length, chinese, repeated, quote, empty)
    │
    ├─ STRUCTURAL GATES (Phase 2 registration — EXACTLY 2):
    │     ├─ narrative_pov_continuity         (minor, fail-open)
    │     └─ tense_voice_consistency          (minor, fail-open)
    │
    └─ DIAGNOSTIC SIGNALS (specified only, NOT registered in Phase 2):
          ├─ pronoun_consistency              (diagnostic, fail-open) — RM-8.6+ future scope
          └─ emotional_tone_coherence         (diagnostic, fail-open) — RM-8.6+ future scope
             │
             ��
ValidationResult (extended with new checks in `checks` list — **only 2 structural gates added in Phase 2**)
    │
    ��� ��
QualityCertificate (UNCHANGED — no new dimension scores)
    │
    ��� ��
DeliveryManifest (includes new checks via existing `checks` propagation)
```

**Zero New Modules** — all changes within existing `core/translation_release/validator.py` only (registration only).

---

### 3. DATA STRUCTURES

#### 3.1 ValidationCheck (No Change — Reuse Existing)

```python
# core/translation_release/validator.py — existing, no modification needed
@dataclass(frozen=True)
class ValidationCheck:
    name: str
    passed: bool
    score: float
    details: dict[str, Any]
    severity: str  # "critical" | "major" | "minor" | "info"
```

#### 3.2 QualityCertificate — NO CHANGES

```python
# core/translation_release/models.py — NO MODIFICATIONS
# Existing QualityCertificate remains exactly as-is.
# New checks carried in ValidationResult.checks list only.
```

#### 3.3 RM-8.2 Metadata Schema (Reference — Already Exists in chunk_records)

```python
# Each chunk_record.metadata.context_state contains:
{
    "scene_id": str,                    # e.g., "scene_3"
    "scene_version": int,               # e.g., 2
    "chapter_id": str,                  # e.g., "chapter_1"
    "boundary": {                       # BoundaryResult.to_dict()
        "type": "same_scene" | "scene_transition" | "chapter_transition" | "unknown_transition",
        "scene_id": str | None,
        "chapter_id": str | None,
        "confidence": float,
        "metadata": dict
    },
    "narrative": {                      # NarrativeState.to_prompt_context() — RM-8.2 RUNTIME CONTRACT
        "perspective": str,             # "first_person" | "second_person" | "third_person" | "unknown"
        "voice": str,                   # "neutral" | "dialogue_driven" | "descriptive" | "balanced"
        "tense": str,                   # "past" | "present" | "undetermined"
        "emotional_tone": str,          # e.g., "tense" (NOT USED by RM-8.5)
        "focus": str,                   # e.g., "mode=narration_heavy; scene_transitions=2"
        "transitions": list[str],       # e.g., ["nar_1", "nar_2"]
        "metadata": {"updates": int}
    },
    "context_selection_fingerprint": str,
    "selected_context_ids": tuple[str, ...]
}
```

---

### 4. GATE SPECIFICATIONS

#### 4.1 Structural Gates (Affect ValidationResult score)

##### 4.1.1 Gate 1: Narrative POV Continuity (Minor, FAIL-OPEN)

**Purpose**: Verify narrative perspective (POV) remains stable within scenes, only changes at explicit boundaries.

**Algorithm**:
```python
def _check_narrative_pov_continuity(text: str, chunk_records: list[dict]) -> ValidationCheck:
    """
    FAIL-OPEN: Any exception, missing data, or unknown state → return passed=True, score=100.0

    1. For each chunk_record:
       - Extract narrative.perspective from context_state
       - Normalize: "first_person" | "second_person" | "third_person" | "unknown"
       - UNKNOWN handling: "unknown" = "indeterminate, no false positive" → NEVER flag as violation

    2. For consecutive chunks within same scene (boundary.type == "same_scene"):
       - Flag if perspective changes without chapter/scene transition
       - Only flag when BOTH current AND next are KNOWN (not "unknown") AND different

    3. Allow perspective change ONLY at:
       - boundary.type == "chapter_transition"
       - boundary.type == "scene_transition" (with new scene_id)

    4. Score: 100 - (unauthorized_changes × 25), min 0
    """
```

**Valid Perspectives** (from `NarrativeState.to_prompt_context()` — RM-8.2 Runtime Contract):
- `first_person` — 第一人稱
- `second_person` — 第二人稱
- `third_person` — 第三人稱（不細分 limited / omniscient）
- `unknown` — **未�識別 / 無法判定 — 明確定義為「不可判定，不�產生�誤報」**

**Severity**: `minor` — POV shifts disorient readers but not catastrophic.

**FAIL-OPEN Behavior**:
- Missing `context_state` → pass
- Missing `narrative` → pass
- Missing `perspective` → pass
- `perspective == "unknown"` on either side → pass (no false positive)
- Any exception during check → pass

**Test Matrix**:
| Scenario | Expected | Reason |
|---|---|---|
| Same scene, same POV | PASS | No change |
| Same scene, POV change (both known) | FAIL | Unauthorized change |
| Same scene, POV change (one unknown) | PASS | Unknown = no false positive |
| Same scene, missing context_state | PASS | Fail-open |
| Scene transition, POV change | PASS | Allowed at boundary |
| Chapter transition, POV change | PASS | Allowed at boundary |
| Exception during check | PASS | Fail-open |

**Prohibited Derivations**:
- Do not use `active_speaker` or `participants` (not in chunk_records)
- Do not attempt to disambiguate `unknown` perspectives
- Do not modify severity to `major` without audit clearance
- Do not fail-closed on missing data

##### 4.1.2 Gate 2: Tense/Voice Consistency (Minor, FAIL-OPEN)

**Purpose**: Verify narrative tense and voice remain consistent within scenes.

**Algorithm**:
```python
def _check_tense_voice_consistency(text: str, chunk_records: list[dict]) -> ValidationCheck:
    """
    FAIL-OPEN: Any exception, missing data, or unknown state → return passed=True, score=100.0

    1. For each chunk_record:
       - Extract narrative.tense, narrative.voice from context_state
       - Tense: "past" | "present" | "undetermined" (default from NarrativeState)
       - Voice: "neutral" | "dialogue_driven" | "descriptive" | "balanced"
       - UNKNOWN handling: "unknown" = "indeterminate, no false positive" → NEVER flag as violation

    2. For consecutive chunks within same scene:
       - Flag tense change without transition (only when BOTH known and different)
       - Flag voice change without transition (only when BOTH known and different)

    3. Allow changes at chapter/scene transitions

    4. Score: 100 - (tense_violations × 15 + voice_violations × 10), min 0
    """
```

**Severity**: `minor` — tense/voice drift breaks narrative immersion but not catastrophic.

**FAIL-OPEN Behavior**:
- Missing `context_state` → pass
- Missing `narrative` → pass
- Missing `tense` or `voice` → pass
- `tense == "undetermined"` or `voice == "unknown"` on either side → pass (no false positive)
- Any exception during check → pass

**Test Matrix**:
| Scenario | Expected | Reason |
|---|---|---|
| Same scene, same tense/voice | PASS | No change |
| Same scene, tense change (both known) | FAIL | Unauthorized change |
| Same scene, voice change (both known) | FAIL | Unauthorized change |
| Same scene, one unknown | PASS | Unknown = no false positive |
| Same scene, missing context_state | PASS | Fail-open |
| Scene/chapter transition, change | PASS | Allowed at boundary |
| Exception during check | PASS | Fail-open |

**Prohibited Derivations**:
- Do not use `emotional_tone` or `focus` for this check
- Do not attempt to infer tense/voice from text
- Do not modify severity to `major` without audit clearance
- Do not fail-closed on missing data

##### 4.1.3 [THIRD STRUCTURAL GATE] — Reserved for RM-8.6+ Future Scope (NOT Part of RM-8.5 Phase 2)

**Classification**: **Future placeholder only** — NOT a Phase 2 structural gate.

**Rationale**: Per RM-8.5 Specification Consistency Audit (Section 9 and 10), only two gates (`narrative_pov_continuity` and `tense_voice_consistency`) have sufficient data and reliability to be structural gates in RM-8.5. The audit explicitly authorized **only 2 structural gates**.

**Proposed Candidate** (for future RM versions, e.g., RM-8.6+): `cross_chunk_entity_consistency` would require serializing full `TERMINOLOGY_STATE` values (source_term → translated_term mappings) into `chunk_records`, which is **not currently available** (Audit Section 1.3).

**Algorithm Template** (for future reference only — NOT implemented in RM-8.5):
```python
def _check_future_structural_gate(text: str, chunk_records: list[dict]) -> ValidationCheck:
    """
    FAIL-OPEN: Any exception, missing data, or unknown state → return passed=True, score=100.0
    [To be implemented in future RM when sufficient data is available in chunk_records]
    """
```

**Status**: **Explicitly NOT part of RM-8.5 Phase 2**. Documented here solely for forward-planning traceability. Any future implementation requires a new Specification Consistency Audit and Implementation Authorization for the respective RM version.

---

#### 4.2 Diagnostic Signals (Informational only, do not affect ValidationResult score)

##### 4.2.1 Diagnostic Signal 1: Pronoun Consistency (Fail-Open)

**Purpose**: Detect pronoun category shifts within scenes as a potential indicator of perspective errors (informational only).

**Algorithm**:
```python
def _check_pronoun_consistency(text: str, chunk_records: list[dict]) -> ValidationCheck:
    """
    FAIL-OPEN: Any exception → return passed=True, score=100.0

    1. Split `text` by chunk boundaries (using `chunk_records` boundary data)
    2. For each chunk, count pronoun categories in last 200 chars:
       - Categories: 第一人稱 (我/我們), 第二人稱 (你/�妳/您/你們), 第三人稱 (他/她/它/�祂/�牠/他們/她們/�牠們/�祂們), 其他
    3. For consecutive chunks within same scene:
       - Flag if pronoun category distribution shifts significantly (e.g., >30% change in any category)
       - Only flag when BOTH chunks have sufficient text (>50 chars) for analysis
    4. Score: 100 - (shift_penalty × 50), min 0
    """
```

**Valid Pronoun Categories**: Derived from standard Chinese pronouns in final assembled text.

**Severity**: `info` — pronoun shifts are common in literary style (quoted dialogue, perspective shifts, etc.).

**FAIL-OPEN Behavior**:
- Missing `context_state` → pass
- Missing boundary data → pass (use sequential chunks)
- Any exception during check → pass

**Test Matrix**:
| Scenario | Expected | Reason |
|---|---|---|
| Same scene, similar pronoun distribution | PASS | No significant shift |
| Same scene, major pronoun shift | FAIL | Potential perspective error (informational) |
| Same scene, insufficient text | PASS | Insufficient for analysis |
| Exception during check | PASS | Fail-open |

**Prohibited Derivations**:
- Do not treat as a gate that fails delivery
- Do not attempt to resolve coreference without entity data
- Do not modify severity to `minor` or `major` without audit clearance
- Do not fail-closed on missing data

##### 4.2.2 Diagnostic Signal 2: Emotional Tone Coherence (Fail-Open)

**Purpose**: Detect abrupt emotional tone shifts within scenes as a potential indicator of narrative inconsistency (informational only).

**Algorithm**:
```python
def _check_emotional_tone_coherence(text: str, chunk_records: list[dict]) -> ValidationCheck:
    """
    FAIL-OPEN: Any exception, missing data, or unknown state → return passed=True, score=100.0

    1. For each chunk_record:
       - Extract narrative.emotional_tone from context_state
       - Valid values: "neutral" | "tense" | "calm" | "joyful" | "sad" | "angry" | "fearful" | "mixed"
       - UNKNOWN handling: "unknown" = "indeterminate, no false positive" → NEVER flag as violation

    2. For consecutive chunks within same scene:
       - Define tone distance matrix (e.g., neutral��↔tense=1, neutral��↔calm=1, joyful��↔sad=3)
       - Flag if tone distance > threshold (e.g., >2) without chapter/scene transition
       - Only flag when BOTH chunks have KNOWN tone (not "unknown")

    3. Allow tone changes at chapter/scene transitions

    4. Score: 100 - (tone_violations × 20), min 0
    """
```

**Valid Emotional Tones**: From `NarrativeState.to_prompt_context()` — RM-8.2 Runtime Contract.

**Severity**: `info` — tone shifts are legitimate literary devices (contrast, irony, scene mood changes).

**FAIL-OPEN Behavior**:
- Missing `context_state` → pass
- Missing `narrative` or `emotional_tone` → pass
- `emotional_tone == "unknown"` on either side → pass (no false positive)
- Any exception during check → pass

**Test Matrix**:
| Scenario | Expected | Reason |
|---|---|---|
| Same scene, similar tone | PASS | No significant shift |
| Same scene, tone shift within threshold | PASS | Acceptable drift |
| Same scene, tone shift beyond threshold | FAIL | Abrupt shift (informational) |
| Same scene, one unknown tone | PASS | Unknown = no false positive |
| Scene/chapter transition, any shift | PASS | Allowed at boundary |
| Exception during check | PASS | Fail-open |

**Prohibited Derivations**:
- Do not treat as a gate that fails delivery
- Do not attempt to infer emotional tone from text
- Do not modify severity to `minor` or `major` without audit clearance
- Do not fail-closed on missing data

---

### 5. INTEGRATION POINTS

#### 5.1 `core/translation_release/validator.py` — Phase 2 Changes (Registration Only)

```python
# Phase 2: Register the two structural gates in validate_final_novel()
# (The check functions themselves were implemented in Phase 1)

def validate_final_novel(...):
    checks: list[ValidationCheck] = []

    # ... existing 9 checks ...

    # NEW: Cross-Chunk Semantic Checks (STRUCTURAL GATES ONLY - Phase 2 registration — EXACTLY 2)
    # Only execute when quality_delivery_v83 is enabled (feature-gated)
    if getattr(options, "quality_delivery_v83", False):
        checks.append(_check_narrative_pov_continuity(text, chunk_records))
        checks.append(_check_tense_voice_consistency(text, chunk_records))
        # Note: [THIRD STRUCTURAL GATE] is reserved for RM-8.6+ future scope — NOT part of Phase 2
        #       Diagnostic signals (pronoun_consistency, emotional_tone_coherence) are specified
        #       for informational use only and NOT registered in ValidationResult

    # ... existing scoring logic (unchanged) ...
```

**NO CHANGES TO**:
- `core/translation_release/metadata.py` — **NOT MODIFIED**
- `core/translation_release/models.py` — **NOT MODIFIED**
- `core/translation_release/polish.py` — NOT MODIFIED
- `core/translation_release/delivery_pipeline.py` — NOT MODIFIED
- Any RM-8.2~8.4 production code

---

### 6. ACCEPTANCE TESTS

#### 6.1 Unit Tests (Extend Existing: `tests/unit/translation_release/test_validator.py`)

**Note**: Unit tests for the two structural gates were already written in Phase 1. Phase 2 requires tests to verify the registration (i.e., that the checks appear in `ValidationResult` when `quality_delivery_v83=True`).

```python
def test_validate_final_novel_registers_structural_gates_when_feature_enabled():
    """Phase 2: Verify structural gates are registered when quality_delivery_v83=True"""
    options = TxtTranslationOptions()
    options.quality_delivery_v83 = True

    # Minimal valid inputs
    text = "他走了進來。\n\n他看到了她。"
    chunk_records = [
        {"metadata": {"context_state": {
            "scene_id": "scene_1", "chapter_id": "chapter_1",
            "boundary": {"type": "same_scene"},
            "narrative": {"perspective": "third_person", "voice": "balanced", "tense": "past"}
        }}},
        {"metadata": {"context_state": {
            "scene_id": "scene_1", "chapter_id": "chapter_1",
            "boundary": {"type": "same_scene"},
            "narrative": {"perspective": "third_person", "voice": "balanced", "tense": "past"}
        }}},
    ]

    result = validate_final_novel(text, {}, chunk_records, {}, options)

    # Check that the two structural gates are present
    check_names = {c.name for c in result.checks}
    assert "narrative_pov_continuity" in check_names
    assert "tense_voice_consistency" in check_names

    # Check that they are minor severity and have valid scores
    for check in result.checks:
        if check.name in ("narrative_pov_continuity", "tense_voice_consistency"):
            assert check.severity == "minor"
            assert 0.0 <= check.score <= 100.0
```

#### 6.2 Diagnostic Signal Tests (Informational)

```python
def test_diagnostic_signals_not_registered():
    """Phase 2: Verify diagnostic signals are NOT registered in ValidationResult"""
    options = TxtTranslationOptions()
    options.quality_delivery_v83 = True  # Feature flag on

    text = "他走了進來。\n\n他看到了她。"
    chunk_records = [
        {"metadata": {"context_state": {
            "scene_id": "scene_1", "chapter_id": "chapter_1",
            "boundary": {"type": "same_scene"},
            "narrative": {"perspective": "third_person", "voice": "balanced", "tense": "past"}
        }}},
        {"metadata": {"context_state": {
            "scene_id": "scene_1", "chapter_id": "chapter_1",
            "boundary": {"type": "same_scene"},
            "narrative": {"perspective": "third_person", "voice": "balanced", "tense": "past"}
        }}},
    ]

    result = validate_final_novel(text, {}, chunk_records, {}, options)

    # Diagnostic signals should NOT be in ValidationResult.checks
    check_names = {c.name for c in result.checks}
    assert "pronoun_consistency" not in check_names
    assert "emotional_tone_coherence" not in check_names
```

---

### 7. FILE EDIT SUMMARY

| File | Priority | Change Type |
|---|---|---|
| `core/translation_release/validator.py` | P0 | **Phase 2**: Register 2 structural gate functions in `validate_final_novel()` (guarded by `quality_delivery_v83`) |
| `core/translation_release/metadata.py` | — | **NO CHANGE** |
| `core/translation_release/models.py` | — | **NO CHANGE** |
| `tests/unit/translation_release/test_validator.py` | P1 | EXTEND — add tests for registration (diagnostic signals NOT registered) |
| **Total Implementation**: ~20 lines in 1 core file + tests. |

**Files NOT Modified** (as per constraints):
- No changes to `validator.py` check functions (already implemented in Phase 1)
- No changes to `metadata.py` or `models.py`
- No changes to RM-8.2~8.4 production code
- No new modules

---

### 8. ROLLOUT PLAN

| Phase | Action | Validation |
|---|---|---|
| **Phase 1** | Implement 2 `_check_*` functions in `validator.py` with FAIL-OPEN | `pytest tests/unit/translation_release/test_validator.py -k "pov or tense"` |
| **Phase 2** | Register 2 checks in `validate_final_novel()` (this specification — EXACTLY 2 gates) | Manual run on fixture; verify 2 new checks appear in `ValidationResult.checks` |
| **Phase 3** | Full unit test suite | `pytest tests/unit/translation_release/test_validator.py -v` |
| **Phase 4** | Integration test with canary | Canary run with `quality_delivery_v83=True` |
| **Phase 5** | Full regression suite | All RM-7/8.1/8.2/8.3/8.4 tests PASS |
| **Phase 6** | Specification Review → **then commit** | All tests pass; no production regression; `ntpe_validate.py` PASS |

---

### 9. COMPLIANCE CHECKLIST

| Constraint | Addressed By |
|---|---|
| No Provider/LLM calls | � ✅ All checks pure Python, deterministic |
| No re-translation | � ✅ Validation only on final assembled text |
| No re-chunk/assembly/polish | � ✅ Read-only consumption of RM-8.3 output |
| No RM-8.3 TXT Source of Truth modification | � ✅ `text` parameter is input only |
| No RM-7/RM-8.1/8.2/8.3/8.4 scope creep | � ✅ Only extends `validator.py` (registration only) |
| Feature-gated | � ✅ Controlled by existing `quality_delivery_v83` (default OFF) |
| Backward compatible | � ✅ When flag OFF: zero behavior change |
| Zero Provider Cost | � ✅ No network requests in validation |
| Deterministic | � ✅ Same input → same `ValidationResult` |
| **FAIL-OPEN mandatory** | � ✅ Any error/unknown → check passes |
| **`unknown` = no false positive** | � ✅ Explicitly defined and tested |
| **EXACTLY 2 structural gates registered in Phase 2** | � ✅ Narrative POV continuity, tense/voice consistency — [THIRD STRUCTURAL GATE] is RM-8.6+ future scope |
| **Both structural gates minor severity** | � ✅ Explicit in code and tests |
| **No QualityCertificate changes** | � ✅ Existing `checks` dictionary carries results |
| **No metadata.py/models.py changes** | � ✅ Confirmed in file edit summary |
| **Diagnostic signals specified but not registered** | � ✅ Informational only, fail-open |

---

### 10. NON-GOALS (LOCKED)

- �� ❌ New provider/LLM calls for semantic analysis
- �� ❌ Auto-fix/correction of detected issues
- �� ❌ Synthetic semantic quality score (0–100 aggregate)
- �� ❌ Human-in-the-loop review interfaces
- �� ❌ Modification of RM-8.2 context/scene/narrative propagation
- �� ❌ New chunking engine or re-chunking
- �� ❌ Modification of `TranslationEngine` core logic
- �� ❌ EPUB/PDF generation changes
- �� ❌ Modification of RM-8.3 polish/validator/delivery pipeline beyond specified extensions
- �� ❌ Learning/auto-adaptation from validation results
- �� ❌ Pronoun consistency check (removed from structural gates — diagnostic only)
- �� ❌ Speaker attribution stability check (insufficient data — blocked)
- �� ❌ Emotional tone coherence check (diagnostic only)
- �� ❌ Cross-chunk entity consistency check (insufficient data — blocked)
- �� ❌ QualityCertificate dimension score extensions (removed)
- �� ❌ metadata.py modifications (removed)
- �� ❌ **Any modification to `validator.py`, `tests`, or RM-8.2~8.4 production code in this phase**

---

### 11. DEFINITION OF DONE

RM-8.5 **Phase 2** is complete when:

1. **Registration verified**: `validate_final_novel()` includes `_check_narrative_pov_continuity` and `_check_tense_voice_consistency` in `ValidationResult.checks` when `quality_delivery_v83=True`
2. **Feature gate respected**: When `quality_delivery_v83=False` (default), the two structural checks are NOT executed (zero behavior change)
3. **All unit tests pass**: Including new registration tests and existing validator tests
4. **FAIL-OPEN verified**: Missing data, exceptions, `unknown` values all produce `passed=True, score=100.0` for structural gates
5. **`unknown` handling verified**: Explicit test confirms no false positive on `unknown` for structural gates
6. **No production behavior change** when `quality_delivery_v83=False` (default)
7. **Zero provider requests** in validation pipeline
8. **Static validation**: `python -m compileall` PASS, `ntpe_validate.py` PASS, `git diff --check` PASS
9. **Specification Consistency Audit CLEAR** for Phase 2 → implementation authorized

---

### 12. MINIMAL ARCHITECTURE MODEL (Per Audit Requirement)

| Aspect | Definition |
|---|---|
| **Input** | 1. `text: str` — RM-8.3 polished TXT body (final assembled novel)<br>2. `chunk_records: list[dict]` — with `metadata.context_state` (RM-8.2 provenance: scene_id, chapter_id, boundary, narrative, selected_context_ids)<br>3. `locked_dictionary: dict[str, str]` — baseline (unused by these 2 checks)<br>4. `options: TxtTranslationOptions` — thresholds config |
| **Output** | 1. Extended `ValidationResult` with 2 new `ValidationCheck` entries in `checks` list (**structural gates only**)<br>2. Updated `DeliveryManifest` (via existing `checks` propagation)<br>3. `QualityCertificate` **UNCHANGED** |
| **Ownership** | `core/translation_release/validator.py` — single module, no new dependencies |
| **Provider/Network** | **Provider Requests = 0, Network Requests = 0** |
| **Source of Truth** | **Read-only** — never modifies RM-8.3 TXT body |
| **Pipeline** | **No re-chunk, no re-assembly, no re-polish, no re-translate** |
| **EPUB Relationship** | **Independent** — RM-8.4 consumes validated output; no reverse dependency |
| **Feature Flag** | `quality_delivery_v83` (existing) — OFF = zero regression |
| **Fail-Open** | **MANDATORY** — any error/unknown → check passes, never fails delivery |
| **Unknown** | **Explicitly defined** = "indeterminate, no false positive" |

---

**End of Specification**
**Status**: Draft — pending Specification Consistency Audit
**Next**: Audit → CLEAR → Implementation Authorization
