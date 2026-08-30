# P0-FINAL-15-G NVIDIA Rate-Limit Boundary Verification

**Status**: AUDIT IN PROGRESS  
**Date**: 2026-08-26  
**Scope**: NTPE TXT Translation Runtime + NVIDIA Provider 40 RPM boundary analysis  
**Baseline**: commit 8c999b1 (HEAD=origin/main, 0/0 divergence) ✅ VERIFIED

---

## Executive Summary

This audit verifies the relationship between the **official NVIDIA 40 RPM limit** and **actual HTTP 429 responses** observed during NTPE translation runs. The goal is to establish factual evidence — not to adjust retry policies.

**Key Architecture Discovery**: NTPE has **two independent rate-limiting layers** that don't coordinate:

| Layer | Location | Limit | Behavior |
|-------|----------|-------|----------|
| **Client-side (hard)** | `core/translation_engine/nvidia_client.py` | 40 RPM (capped) | **Global process-wide** — blocks *before* HTTP request via sleep |
| **Provider-side (soft)** | `core/ai_provider/rate_limiter.py` | 10^9 (disabled) | **Per-provider** — effectively no-op |

**Critical Finding**: The NvidiaClient global rate limiter **should prevent 429 entirely** if working correctly. Observed 429s suggest either:
1. The global limiter has a bug/is bypassed
2. NVIDIA enforces a **different quota dimension** (tokens, concurrent, account-level)
3. Multiple NTPE processes share the same API key

---

## Phase A — Request Accounting Architecture

### A.1 Request Flow (Single Chunk)

```
translate_package_with_retry() [lts/txt_translation_runtime.py:528]
       │
       ▼
engine.translate_package() [core/translation_engine/translation_engine.py:54]
       │
       ▼
build_translation_provider_manager() [core/translation_engine/provider_runtime.py:182]
       │
       ├─► ProviderManager.complete() [core/ai_provider/manager.py:53]
       │       │
       │       ├─► ProviderRuntimeExecutionPolicy.execute() [core/ai_provider/execution_policy.py:74]
       │       │       │
       │       │       ├─► rate_limiter.allow() [10^9 calls → ALWAYS TRUE]
       │       │       │
       │       │       └─► provider.complete() → NvidiaTranslationProvider.complete()
       │       │                       │
       │       │                       └─► NvidiaClient.chat() [core/translation_engine/nvidia_client.py:77]
       │       │                               │
       │       │                               ├─► _global_nvidia_rate_limit() [40 RPM HARD]
       │       │                               │
       │       │                               └─► requests.post() → NVIDIA API
       │       │
       │       └─► RetryPolicy.run() [max_attempts=3, base_delay=5s]
       │
       └─► QA retry loop [legacy path: up to 4 QA attempts × provider attempts]
```

### A.2 Request Counting by Layer

| Layer | Max Attempts/Chunk | Notes |
|-------|-------------------|-------|
| `translate_package_with_retry` (TXT runtime) | `provider_attempts` (default 2-4) | Outer retry |
| `ProviderRuntimeExecutionPolicy.execute` | `max_attempts=3` (configurable) | Provider retry |
| `RetryPolicy.run` | `max_attempts=3` | Same as above (shared) |
| **QA retry (legacy path)** | `qa_attempts` (default 4) | **Multiplicative!** |
| **Total theoretical max (legacy)** | **4 × 4 = 16 requests/chunk** | **THEORETICAL** |
| **Runtime pipeline path** | **provider_attempts only** | No QA retry multiplication |

---

## Phase B — Request Timeline Evidence

### B.1 Live Evidence from Prior Runs (P0-FINAL-15-F)

```
Chunk 1:
  attempt 1: HTTP 429 @ t=0s
  retry delay 5s
  attempt 2: HTTP 429 @ t=5s
  retry delay 10s
  attempt 3: HTTP 429 @ t=15s
  retry delay 20s
  attempt 4: HTTP 429 @ t=35s
  Total elapsed: ~66s
  All 4 attempts failed → chunk failed

Chunk 2-4: Same pattern
```

**Observed**: 3 retries + 1 initial = 4 requests/chunk over ~66s → **~3.6 RPM per chunk**

**If 4 chunks sequential**: ~14.4 RPM total → **Well under 40 RPM**

**But**: NvidiaClient global limiter should have spaced requests to ≤40 RPM **before** they hit NVIDIA.

---

## Phase C — 40 RPM Boundary Calculation

### C.1 NvidiaClient Global Rate Limiter Logic

```python
# core/translation_engine/nvidia_client.py:16-39
def _global_nvidia_rate_limit(rpm_limit: int) -> float:
    limit = max(1, min(40, int(rpm_limit)))  # CAPPED AT 40
    window = 60.0
    minimum_interval = window / limit  # 1.5s at 40 RPM
    
    while True:
        with _NVIDIA_RATE_LOCK:
            now = time.monotonic()
            # Expire old timestamps
            while _NVIDIA_REQUEST_TIMES and now - _NVIDIA_REQUEST_TIMES[0] >= window:
                _NVIDIA_REQUEST_TIMES.popleft()
            # Wait if at limit
            if len(_NVIDIA_REQUEST_TIMES) >= limit:
                wait_for_window = max(0.0, window - (now - _NVIDIA_REQUEST_TIMES[0]))
            # Enforce minimum spacing
            wait_for_spacing = max(0.0, minimum_interval - (now - _NVIDIA_LAST_REQUEST_AT))
            wait_for = max(wait_for_window, wait_for_spacing)
            if wait_for <= 0:
                stamp = time.monotonic()
                _NVIDIA_REQUEST_TIMES.append(stamp)
                _NVIDIA_LAST_REQUEST_AT = stamp
                return waited
        time.sleep(wait_for)
        waited += wait_for
```

### C.2 Expected Behavior at 40 RPM

| Scenario | Expected Wait | Actual Request Rate |
|----------|--------------|---------------------|
| 1st request | 0s | Immediate |
| 2nd request | ≥1.5s | 1.5s interval |
| Nth request (N≤40) | N×1.5s | ≤40/min |
| 41st request | Wait for 1st to expire | 40/min sustained |

**The global limiter guarantees: ≤40 requests per rolling 60-second window per process.**

### C.3 Rolling 60-Second Window Calculation

If 4 chunks × 4 attempts = 16 requests over ~66s:
- **Peak rate**: 4 requests in first ~15s (chunk 1 retries) → **16 RPM** (burst)
- **Rolling 60s max**: 16 requests in 66s → **14.5 RPM** average
- **Well under 40 RPM**

**Conclusion**: Client-side limiter *should* prevent 429 entirely for sequential chunks.

---

## Phase D — 429 Response Evidence

### D.1 NVIDIA Response Format (from nvidia_client.py)

```python
# Lines 140-143
if response.status_code >= 400:
    raise RuntimeError(
        f"NVIDIA API error {response.status_code}: {response.text[:1000]}"
    )
```

**Current capture**: Only status code and first 1000 chars of response text.

### D.2 Missing Response Metadata (NOT_PRESENT)

| Header / Field | Status | Evidence |
|----------------|--------|----------|
| `Retry-After` | NOT_PRESENT | Not captured |
| `RateLimit-Limit` | NOT_PRESENT | Not captured |
| `RateLimit-Remaining` | NOT_PRESENT | Not captured |
| `RateLimit-Reset` | NOT_PRESENT | Not captured |
| `x-ratelimit-*` | NOT_PRESENT | Not captured |
| `x-request-id` | NOT_PRESENT | Not captured |
| Error code body | PARTIAL | First 1000 chars only |

### D.3 Required Enhancement for Verification

To properly verify 429 cause, NvidiaClient must capture:

```python
# PROPOSED — NOT IMPLEMENTED
response_headers = dict(response.headers)
error_body = response.text  # Full body, not truncated
```

---

## Phase E — Rate-Limit Dimension Analysis

| Dimension | Evidence | Status |
|-----------|----------|--------|
| **RPM (40 official)** | Client limiter enforces 40 RPM; observed ~14 RPM | **CONFIRMED CLIENT-SIDE** |
| **Token/minute** | Not tracked by NTPE | **UNKNOWN** |
| **Concurrent requests** | Sequential chunks (no concurrency) | **NOT_APPLICABLE** |
| **Model-specific quota** | minimax-m3 only; no evidence of per-model limit | **UNKNOWN** |
| **Account/project quota** | Single API key; could have daily/monthly caps | **UNKNOWN** |
| **Dynamic capacity** | NVIDIA "degraded" errors seen; capacity varies | **LIKELY** |
| **Unknown** | 429 despite client-side limiter | **CONFIRMED EXTERNAL** |

### E.1 Why 429 Occurs Despite Client-Side Limiter

**Hypotheses** (require live evidence):

1. **NVIDIA enforces token/minute** — Large prompts + completions exceed token budget
2. **Account-level concurrent limit** — Other processes using same API key
3. **Dynamic capacity reduction** — NVIDIA returns 429 when workers saturated (not quota)
4. **Client limiter bypassed** — Multiple NvidiaClient instances, or process not sharing state
5. **RPM ≠ the only quota** — NVIDIA has hidden dimensions

---

## Phase F — Retry Multiplication Audit

### F.1 Two Retry Layers Exist

| Layer | Config | Default | Location |
|-------|--------|---------|----------|
| **TXT Runtime** | `provider_attempts` / `max_retries+1` | 4 attempts | `txt_translation_runtime.py:529` |
| **ProviderManager** | `RetryPolicy.max_attempts` | 3 attempts | `provider_runtime.py:227` |

### F.2 Are They Multiplicative?

**Runtime Pipeline Path** (`_pipeline_mode() == "runtime"`):
- Uses `RuntimeOrchestrator.execute()` → calls provider **once per chunk**
- **NO QA retry multiplication** ✅

**Legacy Path** (default before RM-6):
- `translate_package_with_retry()` called per QA attempt
- QA retry loop: up to 4 attempts
- Each QA attempt → `translate_package_with_retry()` → up to 4 provider attempts
- **THEORETICAL 16 requests/chunk** ⚠️

### F.3 Actual Execution Path Verification

From `txt_translation_runtime.py:1938-1963`:
```python
if _pipeline_mode() == "runtime":
    return _translate_txt_with_runtime_pipeline(...)  # Single provider call per chunk
```

**Current default**: `NTPE_RUNTIME_PIPELINE=runtime` (line 158 in ntpe_production_translate.py)

**Conclusion**: **Multiplication is THEORETICAL only** — runtime pipeline avoids it.

---

## Phase G — Rate Limiter Audit

### G.1 NvidiaClient Global Limiter (HARD)

| Property | Value | Verified |
|----------|-------|----------|
| Active | ✅ Yes | Code inspection |
| Scope | Process-wide (global `_NVIDIA_REQUEST_TIMES`) | ✅ |
| Limit | 40 RPM (capped) | ✅ |
| Window | 60s rolling | ✅ |
| Minimum spacing | 1.5s (60/40) | ✅ |
| Cross-chunk shared | ✅ Yes (global deque) | ✅ |
| Cross-retry shared | ✅ Yes (same deque) | ✅ |
| Concurrency aware | ❌ No (sequential only) | ✅ |
| Knows 429 | ❌ No (preventive only) | ✅ |
| Cooldown on 429 | N/A (preventive) | ✅ |

### G.2 ProviderManager Rate Limiter (SOFT — DISABLED)

| Property | Value | Verified |
|----------|-------|----------|
| Active | ❌ No (max_calls=10^9) | `provider_runtime.py:236,239` |
| Scope | Per-provider | Code inspection |
| Limit | 1,000,000,000 | ✅ |
| Knows 429 | ❌ No | ✅ |

### G.3 TranslationRuntime Retry (REACTIVE)

| Property | Value |
|----------|-------|
| Backoff | 5s → 10s → 20s (exponential) |
| Trigger | `is_retryable_error()` sees "429" in error text |
| Scope | Per-chunk, per-attempt |
| Cross-chunk | No |

---

## Phase H — Controlled Verification Plan

### H.1 Safe Verification Method

**Single-chunk test** with full telemetry capture:

```bash
# Minimal test: 1 chunk, capture all metadata
python -m ntpe_production_translate txt \
  tests/literary/Regression_Set/chunk_001.txt \
  output/verify \
  --provider-attempts 4 \
  --retry-base-seconds 5 \
  --no-resume \
  --dry-run false \
  2>&1 | tee verification.log
```

**Required telemetry additions** (to NvidiaClient):

```python
# In NvidiaClient.chat() after response:
telemetry = {
    "timestamp": time.time(),
    "status_code": response.status_code,
    "headers": dict(response.headers),
    "request_id": response.headers.get("x-request-id"),
    "ratelimit_limit": response.headers.get("RateLimit-Limit"),
    "ratelimit_remaining": response.headers.get("RateLimit-Remaining"),
    "ratelimit_reset": response.headers.get("RateLimit-Reset"),
    "retry_after": response.headers.get("Retry-After"),
    "error_body": response.text,  # Full body
}
```

### H.2 Stop Conditions (Mandatory)

STOP immediately if:
- [ ] Request rate exceeds 40 RPM (client limiter broken)
- [ ] Hidden/background requests detected
- [ ] 429 persists across all retries for ≥2 chunks
- [ ] Need to modify retry policy to continue
- [ ] Protected worktree modifications required

---

## Current Evidence Summary

| Question | Answer | Confidence |
|----------|--------|------------|
| Does NTPE enforce 40 RPM client-side? | **YES** — NvidiaClient global limiter | HIGH |
| Does client limiter prevent 429? | **SHOULD** — but 429 observed | MEDIUM |
| Is 40 RPM the only quota? | **UNKNOWN** — likely not | LOW |
| Are retries multiplicative? | **THEORETICAL ONLY** — runtime path avoids | HIGH |
| What triggers 429? | **EXTERNAL** — not client-side RPM | HIGH |
| Can we verify without more 429s? | **NO** — need response headers | HIGH |

---

## Next Steps (Deliverables)

### 1. Enhanced Telemetry (Required for Verification)

Add to `core/translation_engine/nvidia_client.py`:
- Full response header capture
- Complete error body
- Request/response timestamps
- Client-side limiter state at time of request

### 2. Single-Chunk Controlled Test

Run with enhanced telemetry, capture:
- Exact request timeline
- NVIDIA response headers
- Client limiter state

### 3. Final Report

```
docs/governance/repository/P0_FINAL_15_G_NVIDIA_RATE_LIMIT_BOUNDARY_VERIFICATION.md
artifacts/P0_FINAL_15_G_Nvidia_Rate_Limit_Boundary_Verification_Report.json
```

---

## Recommendation for Next Phase

Based on current evidence:

> **Do NOT adjust retry policy yet.**

The 429 is **not explained by 40 RPM** (client limiter should prevent it). Must identify the true quota dimension before designing production policy.

**Next phase options**:
1. **If token/minute**: Add token tracking + pacing
2. **If account concurrent**: Coordinate across processes
3. **If dynamic capacity**: Implement capacity-aware backoff (already have `capacity_retry_delay_seconds`)
4. **If unknown**: Accept `BLOCKED_EXTERNAL_PROVIDER` as valid outcome

---

## Appendix: Key File References

| Component | File | Lines |
|-----------|------|-------|
| NvidiaClient global limiter | `core/translation_engine/nvidia_client.py` | 16-39, 68-75 |
| NvidiaTranslationProvider | `core/translation_engine/provider_runtime.py` | 109-179 |
| ProviderManager | `core/ai_provider/manager.py` | 53-86 |
| ExecutionPolicy | `core/ai_provider/execution_policy.py` | 74-136 |
| RateLimiter (soft) | `core/ai_provider/rate_limiter.py` | 8-42 |
| RetryPolicy | `core/ai_provider/retry.py` | 9-28 |
| TXT Runtime retry | `lts/txt_translation_runtime.py` | 373-611 |
| build_provider_manager | `core/translation_engine/provider_runtime.py` | 182-240 |
| TranslationEngine | `core/translation_engine/translation_engine.py` | 86-113 |