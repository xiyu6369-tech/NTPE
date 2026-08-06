# RM-6.3.0 — Translation Engine Integration Acceptance Report

**Date:** 2026-08-06
**Phase:** RM-6.3.0
**Principle:** Minimal Invasive Integration

---

## 1. Objective

Integrate `TranslationRuntimeAdapter` into the Translation Engine entry point.
Replace direct prompt construction with `TranslationRequest`.  
Do not change translation behavior or provider interaction.

---

## 2. Files Modified

| File | Change | Lines |
|---|---|---|
| `core/translation_engine/translation_engine.py` | Added `translate_package_from_request()` method (132 lines) + helper methods | +183 / -6 |

## 3. Files Created

| File | Purpose |
|---|---|
| `tests/integration/translation_engine_rm630_adapter_integration_test.py` | Golden Regression, Prompt Hash, Provider Parity, Output Compatibility, Error handling, Lifecycle traceability (7 tests) |

## 4. Integration Architecture

```
MergedRuntime → PromptBuilder → PromptAssembly
    → TranslationRuntimeAdapter.prepare → TranslationRequest
        → TranslationEngine.translate_package_from_request()
            → build_translation_provider_manager()
                → NvidiaTranslationProvider.complete()
                    → NvidiaClient.chat()
```

### Key Design Decisions

1. **New method, not replacement.** `translate_package(dict)` is untouched. `translate_package_from_request(TranslationRequest)` is additive.
2. **Deferred import.** `TranslationRequest` is imported inside the method body to avoid a circular dependency (`translation_engine` ↔ `translation_runtime`).
3. **No prompt construction in Engine.** System prompt, user prompt, model profile, and source metadata ALL come from `TranslationRequest.metadata` — the Engine never drills into prompt sections.
4. **Same Provider API.** `ProviderRequest`, `ProviderManager.complete()`, and `NvidiaClient.chat()` are unchanged.

---

## 5. TranslationRequest Lifecycle

```
1. PromptAssembly (sections in fixed order)
2. TranslationRuntimeAdapter.prepare() → TranslationRequest
   - Flattens sections into single prompt string
   - Computes SHA-256 deterministic prompt_hash
   - Approximates token count
   - Captures build_timestamp, section_count, runtime_snapshot
3. TranslationEngine.translate_package_from_request() consumes it
4. Engine returns result with prompt_hash, snapshot_id, request_version
5. Cache stores {result, translation, request.to_dict(), runtime_snapshot}
```

**Same assembly + same snapshot_id → same prompt_hash** (verified).

---

## 6. Validation Results

| Validation | Status |
|---|---|
| `python -m compileall core` | PASS (2899 files) |
| `python ntpe_validate.py` | ALL PASS |
| `git diff --check` | Clean (no whitespace errors) |
| `pytest` (7 new integration tests) | 7/7 PASS |
| `pytest` (9 existing Engine/runtime tests) | 9/9 PASS (0 regressions) |

---

## 7. Output Compatibility

The `translate_package_from_request()` result dict contains every required key
from the legacy `translate_package()` path plus additional traceability fields:

Required (same as legacy):
- `status`, `package_id`, `translated_at`, `output_path`, `cache_path`, `qa`, `provider`

New (RM-6.3.0):
- `prompt_hash`, `snapshot_id`, `request_version`

---

## 8. Provider Requests

Provider interaction is identical — the same `NvidiaTranslationProvider.complete()` receives a `ProviderRequest` with the same fields.

Additional metadata passed in `ProviderRequest.metadata` for governance:
- `prompt_hash`, `snapshot_id`, `section_count`, `token_count`

Provider runtime marker changed from `translation_engine_v3` → `translation_engine_v3_rm630` for auditability.

---

## 9. Network Requests

1 request per translation (verified in `test_rm630_single_provider_call`).
No extra network calls added.

---

## 10. Translation Quality Regression

Cannot be verified offline (requires NVIDIA API). The Golden Regression test verifies:
- Same input structure → same output structure
- Same provider metadata → same provider call fields
- Same QA check results

No behavioral changes to translation output format.

---

## 11. Appendix: Test Coverage

| Test | What it Verifies |
|---|---|
| `test_rm630_golden` | Full end-to-end: TranslationRequest → translate → output + cache |
| `test_rm630_prompt_hash_deterministic` | Same assembly → same hash; different snapshot → different hash |
| `test_rm630_provider_parity` | ProviderRequest fields match expected values |
| `test_rm630_output_structure` | Output dict has all required keys + QA-compatible |
| `test_rm630_single_provider_call` | Exactly 1 network request per translation |
| `test_rm630_error_graceful_degrade` | Exceptions are caught, failure dict returned |
| `test_rm630_lifecycle` | Request ids, timestamps, token counts preserved full lifecycle |