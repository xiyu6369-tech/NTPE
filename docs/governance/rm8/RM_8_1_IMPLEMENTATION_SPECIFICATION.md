# RM-8.1 IMPLEMENTATION SPECIFICATION
## Literary Quality Enforcement — Minimal, Explicit, Backward-Compatible

---

### 1. SCOPE & PRINCIPLES

**Objective**: Formalize, observe, and verify the *existing* literary quality capability.  
**Non-Objective**: Build new detectors, new gates, new pipelines, or new scores.

| Principle | Decision |
|---|---|
| Detection | Reuse `_NATURALNESS_PATTERNS` + `detect_unnatural_phrases()` unchanged |
| Classification | Extract literary-relevant hits from existing `naturalness_hits` |
| Enforcement | Reuse `naturalness_guard_policy = "literary_retry"` + `quality_profile` |
| Metrics | Add explicit counters (hits/errors/warnings/passed/codes) — no synthetic score |
| Propagation | Thread metrics through QA report → runtime result → `ProductionOutcome` |
| Compatibility | Zero behavior change for existing `literary_retry` / `warn` / `fail` / `off` |
| Provider Cost | Zero additional provider requests |

---

### 2. ARCHITECTURE OVERVIEW

```
Translation
    ↓
context_intelligence.detect_unnatural_phrases()
    ↓
naturalness_hits  (unchanged)
    ↓
classify_literary_quality_hits()          ← NEW (pure function)
    ↓
RuntimeQAPolicy.analyze_runtime_quality()
    ├─ naturalness_guard_policy = "literary_retry"
    │     + quality_profile ∈ {literary, novel, premium, quality}
    │     → severity = "error"            (unchanged)
    └─ otherwise
          → severity = "warning"          (unchanged)
    ↓
QA Report (+ literary_quality_* metrics)  ← NEW fields only
    ↓
txt_translation_runtime.py retry loop     (unchanged logic)
    ↓
ProductionOutcome                         ← NEW fields propagated
    ↓
Manifest / Report                         ← NEW fields visible
```

---

### 3. DETECTION — NO CHANGES

**File**: `core/translation_engine/context_intelligence.py`

- `_NATURALNESS_PATTERNS` (6 patterns, lines 56–82) — **UNCHANGED**
- `detect_unnatural_phrases()` (lines 180–194) — **UNCHANGED**
- Returns: `List[Dict[code, phrase, message, guidance]]`

---

### 4. CLASSIFICATION — NEW PURE FUNCTION

**File**: `core/translation_runtime/runtime_qa.py` (add near `_naturalness_severity`)

```python
_LITERARY_QUALITY_CODES = {
    "NATURALNESS_HUMAN",
    "NATURALNESS_REDUNDANT_COUNTING",
    "NATURALNESS_OBSERVATORY_VISITOR",
    "NATURALNESS_ENTANGLED",
    "NATURALNESS_SIGH_OF_RELIEF",
}

def classify_literary_quality_hits(naturalness_hits: list[dict]) -> dict:
    """
    Split naturalness_hits into literary-quality vs other.
    Pure function, no side effects, deterministic.
    """
    lit = [h for h in naturalness_hits if h.get("code") in _LITERARY_QUALITY_CODES]
    other = [h for h in naturalness_hits if h.get("code") not in _LITERARY_QUALITY_CODES]
    return {
        "literary_quality_hits": lit,
        "other_naturalness_hits": other,
        "literary_quality_hit_count": len(lit),
        "literary_quality_error_count": 0,   # filled by caller after severity applied
        "literary_quality_warning_count": 0, # filled by caller after severity applied
    }
```

**Called from**: `analyze_runtime_quality()` after `naturalness_hits` are collected, before severity application.

---

### 5. ENFORCEMENT — NO NEW POLICY, NO NEW GATE

| Existing Policy | Quality Profile | Severity for Literary Hits | QA `passed` | Chunk Saved |
|---|---|---|---|---|
| `literary_retry` | literary / novel / premium / quality | `error` | `False` | No (if `qa_fail_policy != "warn"`) |
| `literary_retry` | other | `warning` | `True` | Yes |
| `warn` | any | `warning` | `True` | Yes |
| `fail` | any | `error` | `False` | No |
| `off` | any | — (not flagged) | `True` | Yes |

**No new `literary_quality` policy value added.**  
**No new QA gate inserted.**  
Behavior of `literary_retry` preserved exactly.

---

### 6. METRICS — EXPLICIT COUNTERS, NO SCORE

**Added to QA report `metrics` dict** (inside `analyze_runtime_quality`):

```python
qa_report["metrics"].update({
    "literary_quality_hits": lit_classification["literary_quality_hit_count"],
    "literary_quality_errors": lit_error_count,      # severity == "error"
    "literary_quality_warnings": lit_warning_count,  # severity == "warning"
    "literary_quality_passed": lit_error_count == 0,
    "literary_quality_issue_codes": [h["code"] for h in lit_classification["literary_quality_hits"]],
})
```

**State table** (replaces Audit's incorrect "zero when warning"):

| Policy / Profile | hits | errors | warnings | passed |
|---|---:|---:|---:|---|
| `off` | 0 | 0 | 0 | true |
| `warn` + literary profile | 3 | 0 | 3 | true |
| `literary_retry` + literary profile | 3 | 3 | 0 | false |
| `literary_retry` + non-literary profile | 3 | 0 | 3 | true |
| `fail` | 3 | 3 | 0 | false |

**Detection ≠ Enforcement**. Metrics always reflect *what was detected*; `passed` reflects *enforcement outcome*.

---

### 7. PROPAGATION TO PRODUCTION OUTCOME

**File**: `core/adaptive_context_production_rollout/outcome.py`

Add to `ProductionOutcome` (extend `__init__`, `to_dict`, `from_dict`):

```python
# New fields
literary_quality_hits: int = 0
literary_quality_errors: int = 0
literary_quality_warnings: int = 0
literary_quality_passed: bool = True
literary_quality_issue_codes: list[str] = field(default_factory=list)
```

**File**: `core/adaptive_context_production_rollout/quality_bridge.py`

In `collect_production_outcome()`: copy new metrics from runtime QA reports into `ProductionOutcome` accumulator.

---

### 8. MANIFEST / REPORT VISIBILITY

Final translation manifest (generated in `txt_translation_runtime.py` or downstream) must include:

```json
{
  "literary_quality": {
    "hits": 2,
    "errors": 1,
    "warnings": 1,
    "passed": false,
    "issue_codes": ["NATURALNESS_HUMAN", "NATURALNESS_REDUNDANT_COUNTING"]
  }
}
```

`ntpe_literary_evaluation.py` can now report literary quality explicitly via these fields.

---

### 9. ACCEPTANCE GATES (MINIMUM VERIFIABLE CRITERIA)

| # | Gate | Verification |
|---|---|---|
| 1 | Detection works | Existing `_NATURALNESS_PATTERNS` produce `naturalness_hits` with literary codes |
| 2 | Classification correct | `classify_literary_quality_hits()` splits hits by code set accurately |
| 3 | Warning mode | `naturalness_guard_policy=warn` + literary profile → hits>0, errors=0, warnings>0, passed=true, chunk saved |
| 4 | Literary retry | `naturalness_guard_policy=literary_retry` + literary profile → hits>0, errors>0, warnings=0, passed=false, chunk NOT saved (if `qa_fail_policy=retry/fail`) |
| 5 | Clean translation | hits=0 → errors=0, warnings=0, passed=true |
| 6 | Metrics propagation | QA report → runtime result → `ProductionOutcome` → manifest all contain identical literary_quality_* fields |
| 7 | Backward compatibility | All existing unit/integration tests pass unchanged; `literary_retry` behavior identical |
| 8 | Provider invariance | Zero additional provider calls in any configuration |

---

### 10. FILES TO MODIFY (MINIMAL SET)

| File | Change Type |
|---|---|
| `core/translation_runtime/runtime_qa.py` | Add `classify_literary_quality_hits()`, extend `analyze_runtime_quality()` metrics |
| `core/adaptive_context_production_rollout/outcome.py` | Add 5 fields to `ProductionOutcome` |
| `core/adaptive_context_production_rollout/quality_bridge.py` | Propagate metrics in `collect_production_outcome()` |
| `lts/txt_translation_runtime.py` | Ensure manifest includes literary_quality block (downstream consumer) |
| Tests | Add unit tests for classification + policy behavior matrix |

**Files NOT modified**:
- `context_intelligence.py` (detection unchanged)
- `translation_engine.py` (provider flow unchanged)
- No new files, no new modules, no new policies

---

### 11. NON-GOALS (LOCKED)

- ❌ New `literary_quality` policy value
- ❌ `literary_quality_score` (synthetic 0–100)
- ❌ New detector patterns
- ❌ New QA gate / retry engine
- ❌ LLM judge / external model calls
- ❌ RM-8.2 cross-chunk continuity
- ❌ RM-8.3 output/delivery gates
- ❌ Refactoring `runtime_qa.py` or `txt_translation_runtime.py` beyond metric fields
- ❌ Human-in-the-loop review interfaces

---

### 12. ROLLOUT STRATEGY

1. Implement classification + metrics (Phase 1 above)
2. Run full test suite → **all pass** (regression gate)
3. Deploy behind `naturalness_guard_policy` config (existing knob)
4. Shadow/canary observe `literary_quality_*` in manifests
5. Promote to production default when metrics stable

---

**Status**: Ready for implementation.  
**Dependencies**: RM-7 complete (entity/consistency/review/learning).  
**Next**: Codex implements per this specification.