# RM-8.5 Implementation Specification
## Cross-Chunk Semantic Quality Gate ??Minimal, Explicit, Backward-Compatible

---

### 1. SCOPE & PRINCIPLES

**Objective**: Add deterministic cross-chunk semantic validation checks to the RM-8.3 delivery validation gate. Consume existing RM-8.2 context/scene/narrative metadata from `chunk_records` to verify **narrative POV continuity** and **tense/voice consistency** only.

**Non-Objectives**:
- No new provider/LLM/network calls
- No re-translation, re-chunking, re-assembly, re-polishing
- No modification of RM-8.2 propagation logic
- No modification of RM-8.3 TXT Source of Truth
- No auto-fix/correction (detection only)
- No synthetic semantic score (0??00)
- No human review interfaces
- No RM-7/RM-8.1/RM-8.2/RM-8.3/RM-8.4 scope creep

| Principle | Decision |
|---|---|
| Detection | Pure Python regex/string analysis on final assembled text + RM-8.2 metadata |
| Classification | Extend existing `ValidationCheck` pattern (critical/major/minor/info) |
| Enforcement | Integrate into RM-8.3 weighted scoring (PASS ??70, no critical failures) |
| Metrics | **NO new dimension scores in QualityCertificate** ??use existing `checks` dictionary |
| Propagation | Validator ??DeliveryManifest (via existing `checks` in ValidationResult) |
| Compatibility | Feature-gated by existing `quality_delivery_v83` (default OFF) |
| Provider Cost | Zero additional requests |
| **Fail-Open** | **MANDATORY ??any error/unknown ??check passes, never fails delivery** |
| **Unknown Handling** | **`unknown` = "indeterminate, no false positive" ??explicitly defined per check** |

---

### 2. ARCHITECTURE OVERVIEW

```
RM-8.3 Delivery Pipeline (existing)
    ??    ?œâ? assembled_text (polished TXT body)
    ?œâ? chunk_records (with metadata.context_state from RM-8.2)
    ?œâ? locked_dictionary
    ?”â? options
            ??            ??validate_final_novel()  ??EXTENDED with 2 new checks
    ??    ?œâ? Existing 9 checks (paragraph, punctuation, korean, locked_terms, length, chinese, repeated, quote, empty)
    ??    ?”â? NEW Cross-Chunk Semantic Checks (2 total, both minor, FAIL-OPEN):
         ?œâ? narrative_pov_continuity         (minor, fail-open)
         ?”â? tense_voice_consistency          (minor, fail-open)
            ??            ??ValidationResult (extended with new checks in `checks` list)
    ??    ??QualityCertificate (UNCHANGED ??no new dimension scores)
    ??    ??DeliveryManifest (includes new checks via existing `checks` propagation)
```

**Zero New Modules** ??all changes within existing `core/translation_release/validator.py` only.

---

### 3. DATA STRUCTURES

#### 3.1 ValidationCheck (No Change ??Reuse Existing)

```python
# core/translation_release/validator.py ??existing, no modification needed
@dataclass(frozen=True)
class ValidationCheck:
    name: str
    passed: bool
    score: float
    details: dict[str, Any]
    severity: str  # "critical" | "major" | "minor" | "info"
```

#### 3.2 QualityCertificate ??NO CHANGES

```python
# core/translation_release/models.py ??NO MODIFICATIONS
# Existing QualityCertificate remains exactly as-is.
# New checks carried in ValidationResult.checks list only.
```

#### 3.3 RM-8.2 Metadata Schema (Reference ??Already Exists in chunk_records)

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
    "narrative": {                      # NarrativeState.to_prompt_context() ??RM-8.2 RUNTIME CONTRACT
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

### 4. CROSS-CHUNK SEMANTIC VALIDATION CHECKS (2 Checks Only)

All checks are **deterministic**, **pure functions**, **no side effects**, **no external calls**, **FAIL-OPEN**.

#### 4.1 Check 1: Narrative POV Continuity (Minor, FAIL-OPEN)

**Purpose**: Verify narrative perspective (POV) remains stable within scenes, only changes at explicit boundaries.

**Algorithm**:
```python
def _check_narrative_pov_continuity(text: str, chunk_records: list[dict]) -> ValidationCheck:
    """
    FAIL-OPEN: Any exception, missing data, or unknown state ??return passed=True, score=100.0

    1. For each chunk_record:
       - Extract narrative.perspective from context_state
       - Normalize: "first_person" | "second_person" | "third_person" | "unknown"
       - UNKNOWN handling: "unknown" = "indeterminate, no false positive" ??NEVER flag as violation

    2. For consecutive chunks within same scene (boundary.type == "same_scene"):
       - Flag if perspective changes without chapter/scene transition
       - Only flag when BOTH current AND next are KNOWN (not "unknown") AND different

    3. Allow perspective change ONLY at:
       - boundary.type == "chapter_transition"
       - boundary.type == "scene_transition" (with new scene_id)

    4. Score: 100 - (unauthorized_changes ? 25), min 0
    """
```

**Valid Perspectives** (from `NarrativeState.to_prompt_context()` ??RM-8.2 Runtime Contract):
- `first_person` ??ç¬¬ä?äººç¨±
- `second_person` ??ç¬¬ä?äººç¨±
- `third_person` ??ç¬¬ä?äººç¨±ï¼ˆä?ç´°å? limited / omniscientï¼?- `unknown` ??**?ªè???/ ?¡æ??¤å? ???Žç¢ºå®šç¾©?ºã€Œä??¯åˆ¤å®šï?ä¸ç”¢?Ÿèª¤?±ã€?*

**Severity**: `minor` ??POV shifts disorient readers but not catastrophic.

**FAIL-OPEN Behavior**:
- Missing `context_state` ??pass
- Missing `narrative` ??pass
- Missing `perspective` ??pass
- `perspective == "unknown"` on either side ??pass (no false positive)
- Any exception during check ??pass

---

#### 4.2 Check 2: Tense/Voice Consistency (Minor, FAIL-OPEN)

**Purpose**: Verify narrative tense and voice remain consistent within scenes.

**Algorithm**:
```python
def _check_tense_voice_consistency(text: str, chunk_records: list[dict]) -> ValidationCheck:
    """
    FAIL-OPEN: Any exception, missing data, or unknown state ??return passed=True, score=100.0

    1. For each chunk_record:
       - Extract narrative.tense, narrative.voice from context_state
       - Tense: "past" | "present" | "undetermined"
       - Voice: "neutral" | "dialogue_driven" | "descriptive" | "balanced"
       - UNKNOWN handling: "unknown" = "indeterminate, no false positive" ??NEVER flag as violation

    2. For consecutive chunks within same scene:
       - Flag tense change without transition (only when BOTH known and different)
       - Flag voice change without transition (only when BOTH known and different)

    3. Allow changes at chapter/scene transitions

    4. Score: 100 - (tense_violations ? 15 + voice_violations ? 10), min 0
    """
```

**Severity**: `minor` ??tense/voice drift breaks narrative immersion but not catastrophic.

**FAIL-OPEN Behavior**:
- Missing `context_state` ??pass
- Missing `narrative` ??pass
- Missing `tense` or `voice` ??pass
- `tense == "unknown"` or `voice == "unknown"` on either side ??pass (no false positive)
- Any exception during check ??pass

---

### 5. INTEGRATION POINTS

#### 5.1 `core/translation_release/validator.py` ??Main Changes

```python
# ADD new check functions (2 functions)
def _check_narrative_pov_continuity(text: str, chunk_records: list[dict]) -> ValidationCheck: ...
def _check_tense_voice_consistency(text: str, chunk_records: list[dict]) -> ValidationCheck: ...

# MODIFY validate_final_novel() ??register new checks
def validate_final_novel(...):
    checks: list[ValidationCheck] = []

    # ... existing 9 checks ...

    # NEW: Cross-Chunk Semantic Checks (FAIL-OPEN, minor severity)
    checks.append(_check_narrative_pov_continuity(text, chunk_records))
    checks.append(_check_tense_voice_consistency(text, chunk_records))

    # ... existing scoring logic (unchanged) ...
```

**NO CHANGES TO**:
- `core/translation_release/metadata.py` ??**NOT MODIFIED**
- `core/translation_release/models.py` ??**NOT MODIFIED**
- `core/translation_release/polish.py` ??NOT MODIFIED
- `core/translation_release/package.py` ??NOT MODIFIED
- `core/translation_release/delivery_pipeline.py` ??NOT MODIFIED

---

### 6. ACCEPTANCE TESTS

#### 6.1 Unit Tests (Extend Existing: `tests/unit/translation_release/test_validator.py`)

```python
import pytest
from core.translation_release.validator import (
    _check_narrative_pov_continuity,
    _check_tense_voice_consistency,
)

# Fixture: chunk_records with context_state simulating various scenarios
@pytest.fixture
def same_scene_chunks():
    return [
        {"metadata": {"context_state": {
            "scene_id": "scene_1", "chapter_id": "chapter_1",
            "boundary": {"type": "same_scene"},
            "narrative": {"perspective": "third_person", "voice": "balanced", "tense": "past", "emotional_tone": "neutral"}
        }}},
        {"metadata": {"context_state": {
            "scene_id": "scene_1", "chapter_id": "chapter_1",
            "boundary": {"type": "same_scene"},
            "narrative": {"perspective": "third_person", "voice": "balanced", "tense": "past", "emotional_tone": "neutral"}
        }}},
    ]

@pytest.fixture
def scene_transition_chunks():
    return [
        {"metadata": {"context_state": {
            "scene_id": "scene_1", "chapter_id": "chapter_1",
            "boundary": {"type": "scene_transition"},
            "narrative": {"perspective": "third_person", "voice": "balanced", "tense": "past", "emotional_tone": "neutral"}
        }}},
        {"metadata": {"context_state": {
            "scene_id": "scene_2", "chapter_id": "chapter_1",
            "boundary": {"type": "same_scene"},
            "narrative": {"perspective": "first_person", "voice": "dialogue_driven", "tense": "present", "emotional_tone": "tense"}
        }}},
    ]

@pytest.fixture
def unknown_perspective_chunks():
    """One chunk has unknown perspective ??must NOT flag as violation (fail-open, no false positive)."""
    return [
        {"metadata": {"context_state": {
            "scene_id": "scene_1", "chapter_id": "chapter_1",
            "boundary": {"type": "same_scene"},
            "narrative": {"perspective": "third_person", "voice": "balanced", "tense": "past"}
        }}},
        {"metadata": {"context_state": {
            "scene_id": "scene_1", "chapter_id": "chapter_1",
            "boundary": {"type": "same_scene"},
            "narrative": {"perspective": "unknown", "voice": "balanced", "tense": "past"}
        }}},
    ]

@pytest.fixture
def missing_context_chunks():
    """Missing context_state entirely ??must pass (fail-open)."""
    return [
        {"metadata": {"context_state": {
            "scene_id": "scene_1", "chapter_id": "chapter_1",
            "boundary": {"type": "same_scene"},
            "narrative": {"perspective": "third_person", "voice": "balanced", "tense": "past"}
        }}},
        {"metadata": {}},  # No context_state
    ]

def test_narrative_pov_continuity_passes_same_scene():
    text = "ä»–èµ°äº†é€²ä??‚\n\nä»–ç??°ä?å¥¹ã€?
    result = _check_narrative_pov_continuity(text, same_scene_chunks)
    assert result.passed is True
    assert result.score == 100.0
    assert result.severity == "minor"

def test_narrative_pov_continuity_fails_unauthorized_change():
    # Perspective changes within same scene (BOTH known and different)
    bad_chunks = [
        {"metadata": {"context_state": {"scene_id": "scene_1", "boundary": {"type": "same_scene"}, "narrative": {"perspective": "third_person"}}}},
        {"metadata": {"context_state": {"scene_id": "scene_1", "boundary": {"type": "same_scene"}, "narrative": {"perspective": "first_person"}}}},
    ]
    result = _check_narrative_pov_continuity("text", bad_chunks)
    assert result.passed is False
    assert result.score < 100.0
    assert result.severity == "minor"

def test_narrative_pov_continuity_allows_at_transition():
    # Perspective change at scene_transition is allowed
    result = _check_narrative_pov_continuity("text", scene_transition_chunks)
    assert result.passed is True
    assert result.score == 100.0

def test_narrative_pov_continuity_unknown_is_no_false_positive():
    """unknown perspective MUST NOT produce violation (fail-open, no false positive)."""
    result = _check_narrative_pov_continuity("text", unknown_perspective_chunks)
    assert result.passed is True
    assert result.score == 100.0
    assert result.details.get("unknown_skipped") is True

def test_narrative_pov_continuity_missing_context_is_fail_open():
    """Missing context_state MUST pass (fail-open)."""
    result = _check_narrative_pov_continuity("text", missing_context_chunks)
    assert result.passed is True
    assert result.score == 100.0

def test_tense_voice_consistency_passes_same_scene():
    text = "ä»–èµ°äº†é€²ä??‚\n\nä»–ç??°ä?å¥¹ã€?
    result = _check_tense_voice_consistency(text, same_scene_chunks)
    assert result.passed is True
    assert result.score == 100.0
    assert result.severity == "minor"

def test_tense_voice_consistency_fails_unauthorized_tense_change():
    # Tense changes within same scene (BOTH known and different)
    bad_chunks = [
        {"metadata": {"context_state": {"scene_id": "scene_1", "boundary": {"type": "same_scene"}, "narrative": {"tense": "past", "voice": "balanced"}}}},
        {"metadata": {"context_state": {"scene_id": "scene_1", "boundary": {"type": "same_scene"}, "narrative": {"tense": "present", "voice": "balanced"}}}},
    ]
    result = _check_tense_voice_consistency("text", bad_chunks)
    assert result.passed is False
    assert result.score < 100.0
    assert result.severity == "minor"

def test_tense_voice_consistency_fails_unauthorized_voice_change():
    # Voice changes within same scene (BOTH known and different)
    bad_chunks = [
        {"metadata": {"context_state": {"scene_id": "scene_1", "boundary": {"type": "same_scene"}, "narrative": {"tense": "past", "voice": "neutral"}}}},
        {"metadata": {"context_state": {"scene_id": "scene_1", "boundary": {"type": "same_scene"}, "narrative": {"tense": "past", "voice": "dialogue_driven"}}}},
    ]
    result = _check_tense_voice_consistency("text", bad_chunks)
    assert result.passed is False
    assert result.score < 100.0

def test_tense_voice_consistency_allows_at_transition():
    # Tense/voice change at scene_transition is allowed
    result = _check_tense_voice_consistency("text", scene_transition_chunks)
    assert result.passed is True
    assert result.score == 100.0

def test_tense_voice_consistency_unknown_is_no_false_positive():
    """unknown tense/voice MUST NOT produce violation (fail-open, no false positive)."""
    unknown_chunks = [
        {"metadata": {"context_state": {"scene_id": "scene_1", "boundary": {"type": "same_scene"}, "narrative": {"tense": "past", "voice": "balanced"}}}},
        {"metadata": {"context_state": {"scene_id": "scene_1", "boundary": {"type": "same_scene"}, "narrative": {"tense": "unknown", "voice": "unknown"}}}},
    ]
    result = _check_tense_voice_consistency("text", unknown_chunks)
    assert result.passed is True
    assert result.score == 100.0
    assert result.details.get("unknown_skipped") is True

def test_tense_voice_consistency_missing_context_is_fail_open():
    """Missing context_state MUST pass (fail-open)."""
    result = _check_tense_voice_consistency("text", missing_context_chunks)
    assert result.passed is True
    assert result.score == 100.0
```

---

### 7. FILE EDIT SUMMARY

| File | Priority | Change Type |
|---|---|---|
| `core/translation_release/validator.py` | P0 | ADD 2 `_check_*` functions; MODIFY `validate_final_novel()` to register them |
| `core/translation_release/metadata.py` | ??| **NO CHANGE** |
| `core/translation_release/models.py` | ??| **NO CHANGE** |
| `tests/unit/translation_release/test_validator.py` | P1 | EXTEND ??add tests for 2 new semantic checks |

**Total Implementation**: ~100 lines in 1 core file + tests.

**Files NOT Modified**:
- `context_intelligence.py` ??detection unchanged
- `boundary_detector.py` ??RM-8.2 unchanged
- `narrative_engine.py` ??RM-8.2 unchanged
- `context_scene_memory/*` ??RM-8.2 unchanged
- `txt_translation_runtime.py` ??no changes (feature flag already exists)
- `core/translation_release/metadata.py` ??**NO CHANGE**
- `core/translation_release/models.py` ??**NO CHANGE**
- No new modules, no new dependencies

---

### 8. ROLLOUT PLAN

| Phase | Action | Validation |
|---|---|---|
| **Phase 1** | Implement 2 `_check_*` functions in `validator.py` with FAIL-OPEN | `pytest tests/unit/translation_release/test_validator.py -k "pov or tense"` |
| **Phase 2** | Register checks in `validate_final_novel()` | Manual run on fixture; verify new checks appear in `ValidationResult.checks` |
| **Phase 3** | Full unit test suite | `pytest tests/unit/translation_release/test_validator.py -v` |
| **Phase 4** | Integration test with canary | Canary run with `quality_delivery_v83=True` |
| **Phase 5** | Full regression suite | All RM-7/8.1/8.2/8.3/8.4 tests PASS |
| **Phase 6** | Specification Review ??**then commit** | All tests pass; no production regression; `ntpe_validate.py` PASS |

---

### 9. COMPLIANCE CHECKLIST

| Constraint | Addressed By |
|---|---|
| No Provider/LLM calls | ??All checks pure Python, deterministic |
| No re-translation | ??Validation only on final assembled text |
| No re-chunk/assembly/polish | ??Read-only consumption of RM-8.3 output |
| No RM-8.3 TXT Source of Truth modification | ??`text` parameter is input only |
| No RM-7/RM-8.1/8.2/8.3/8.4 scope creep | ??Only extends `validator.py` |
| Feature-gated | ??Controlled by existing `quality_delivery_v83` (default OFF) |
| Backward compatible | ??When flag OFF: zero behavior change |
| Zero Provider Cost | ??No network requests in validation |
| Deterministic | ??Same input ??same `ValidationResult` |
| **FAIL-OPEN mandatory** | ??Any error/unknown ??check passes |
| **`unknown` = no false positive** | ??Explicitly defined and tested |
| **Only 2 checks (POV, tense/voice)** | ??Others removed per scope reduction |
| **Both minor severity** | ??Explicit in code and tests |
| **No QualityCertificate changes** | ??Existing `checks` dictionary carries results |
| **No metadata.py/models.py changes** | ??Confirmed in file edit summary |

---

### 10. NON-GOALS (LOCKED)

- ??New provider/LLM calls for semantic analysis
- ??Auto-fix/correction of detected issues
- ??Synthetic semantic quality score (0??00 aggregate)
- ??Human-in-the-loop review interfaces
- ??Modification of RM-8.2 context/scene/narrative propagation
- ??New chunking engine or re-chunking
- ??Modification of `TranslationEngine` core logic
- ??EPUB/PDF generation changes
- ??Modification of RM-8.3 polish/validator/delivery pipeline beyond specified extensions
- ??Learning/auto-adaptation from validation results
- ??Pronoun consistency check (removed)
- ??Speaker attribution stability check (removed)
- ??Emotional tone coherence check (removed)
- ??Cross-chunk entity consistency check (removed)
- ??QualityCertificate dimension score extensions (removed)
- ??metadata.py modifications (removed)

---

### 11. DEFINITION OF DONE

RM-8.5 **Core** is complete when:

1. **All unit tests pass** (2 new semantic checks + existing validator tests)
2. **FAIL-OPEN verified**: Missing data, exceptions, `unknown` values all produce `passed=True, score=100.0`
3. **`unknown` handling verified**: Explicit test confirms no false positive on `unknown`
4. **Integration tests pass** (semantic gate runs without crashing delivery pipeline)
5. **Canary runs** with `quality_delivery_v83=True` produce:
   - Extended `ValidationResult.checks` with 2 new entries
   - `DeliveryManifest` includes new checks via existing propagation
   - No regression in existing dimension scores
6. **Regression suite passes**: All RM-7, RM-8.1, RM-8.2, RM-8.3, RM-8.4 tests PASS
7. **No production behavior change** when `quality_delivery_v83=False` (default)
8. **Zero provider requests** in validation pipeline
9. **Static validation**: `python -m compileall` PASS, `ntpe_validate.py` PASS, `git diff --check` PASS
10. **Specification Consistency Audit CLEAR** ??commit authorized

---

### 12. MINIMAL ARCHITECTURE MODEL (Per Audit Requirement)

| Aspect | Definition |
|---|---|
| **Input** | 1. `text: str` ??RM-8.3 polished TXT body (final assembled novel)<br>2. `chunk_records: list[dict]` ??with `metadata.context_state` (RM-8.2 provenance: scene_id, chapter_id, boundary, narrative, selected_context_ids)<br>3. `locked_dictionary: dict[str, str]` ??baseline (unused by these 2 checks)<br>4. `options: TxtTranslationOptions` ??thresholds config |
| **Output** | 1. Extended `ValidationResult` with 2 new `ValidationCheck` entries in `checks` list<br>2. Updated `DeliveryManifest` (via existing `checks` propagation)<br>3. `QualityCertificate` **UNCHANGED** |
| **Ownership** | `core/translation_release/validator.py` ??single module, no new dependencies |
| **Provider/Network** | **Provider Requests = 0, Network Requests = 0** |
| **Source of Truth** | **Read-only** ??never modifies RM-8.3 TXT body |
| **Pipeline** | **No re-chunk, no re-assembly, no re-polish, no re-translate** |
| **EPUB Relationship** | **Independent** ??RM-8.4 consumes validated output; no reverse dependency |
| **Feature Flag** | `quality_delivery_v83` (existing) ??OFF = zero regression |
| **Fail-Open** | **MANDATORY** ??any error/unknown ??check passes, never fails delivery |
| **Unknown** | **Explicitly defined** = "indeterminate, no false positive" |

---

**End of Specification**
**Status**: Draft ??pending Specification Consistency Audit
**Next**: Audit ??CLEAR ??Implementation Authorization
