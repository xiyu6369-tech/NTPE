# P3A2_DEEPSEEK_V4_COMPATIBILITY_PROBE — Phase 3A.2 DeepSeek V4 Availability Probe

## Phase Objective

Evaluate DeepSeek V4 candidate models on the **PRE-MINIMAX-RECONSTRUCTED-BASELINE** 
to confirm which candidates are actually connectable, callable, and produce 
NTPE Translation Contract-compliant output on the NVIDIA provider.

## Baseline Lock

- **HEAD**: `af5cbc091424849134c28ef931ce78d31ea0dc7d`
- **Expected**: `af5cbc0`
- **Match**: True
- **origin/main**: `8c999b1219f65a6afaeaf0062e6c43f72691c188`
- **Divergence**: 0/1
- **Branch**: main
- **Baseline Integrity**: PASS
- **Git Status**: `?? artifacts/P3A1_RECONSTRUCTED_BASELINE_CLOSURE.json; ?? docs/governance/repository/P3A1_RECONSTRUCTED_BASELINE_CLOSURE.md; ?? tools/one_shots/p3a2_deepseek_v4_probe.py`
- **Git Diff Stat**: ``

## Environment

- **Python**: 3.14.6
- **Timestamp**: 2026-08-30T15:00:45.988549Z
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY (present: True)

## Candidate Models

| Candidate | Model ID | Variant | Catalog | Family | Type | Context | Source Evidence | Notes |
|-----------|----------|---------|---------|--------|------|---------|-----------------|-------|
| DeepSeek V4 Pro (0813) | `deepseek-ai/deepseek-v4-pro-0813` | pro-0813 | UNKNOWN | DeepSeek V4 | General Purpose LLM | 128K+ context, reasoning capable | NVIDIA catalog (DeepSeek hosted); v4-pro dated variant | DS-V4-PRO - Primary candidate; dated variant for stability |
| DeepSeek V4 Flash (0731) | `deepseek-ai/deepseek-v4-flash-0731` | flash-0731 | UNKNOWN | DeepSeek V4 | Lightweight LLM | 128K+ context, optimized for speed | NVIDIA catalog (DeepSeek hosted); v4-flash dated variant | DS-V4-FLASH - Primary candidate; flash variant for throughput |
| DeepSeek V4 Pro (base) | `deepseek-ai/deepseek-v4-pro` | pro | UNKNOWN | DeepSeek V4 | General Purpose LLM | 128K+ context, reasoning capable | NVIDIA catalog (DeepSeek hosted); base v4-pro variant | DS-V4-PRO-BASE - Secondary candidate; only if primary unavailable |
| DeepSeek V4 Flash (base) | `deepseek-ai/deepseek-v4-flash` | flash | UNKNOWN | DeepSeek V4 | Lightweight LLM | 128K+ context, optimized for speed | NVIDIA catalog (DeepSeek hosted); base v4-flash variant | DS-V4-FLASH-BASE - Secondary candidate; only if primary unavailable |

## Layer Results

### Layer 0 — Baseline Integrity

| HEAD Commit | Expected | Match | Clean |
|-------------|----------|-------|-------|
| af5cbc091424 | af5cbc0 | True | True |

### Layer 1 — Catalog / Identity

| Model | Provider | Catalog Status | Family | Type | Context | Evidence | Result |
|-------|----------|----------------|--------|------|---------|----------|--------|
| deepseek-ai/deepseek-v4-pro-0813 | NVIDIA | AVAILABLE | DeepSeek V4 | General Purpose LLM | 128K+ context, reasoning capable | NVIDIA catalog (DeepSeek hosted); v4-pro dated variant | PASS |
| deepseek-ai/deepseek-v4-flash-0731 | NVIDIA | AVAILABLE | DeepSeek V4 | Lightweight LLM | 128K+ context, optimized for speed | NVIDIA catalog (DeepSeek hosted); v4-flash dated variant | PASS |
| deepseek-ai/deepseek-v4-pro | NVIDIA | AVAILABLE | DeepSeek V4 | General Purpose LLM | 128K+ context, reasoning capable | NVIDIA catalog (DeepSeek hosted); base v4-pro variant | PASS |
| deepseek-ai/deepseek-v4-flash | NVIDIA | AVAILABLE | DeepSeek V4 | Lightweight LLM | 128K+ context, optimized for speed | NVIDIA catalog (DeepSeek hosted); base v4-flash variant | PASS |

### Layer 2 — NVIDIA Endpoint Availability

| Model | HTTP Status | Category | Latency (ms) | Request Accepted | Response Present | Retry-After | Rate Limit Headers |
|-------|-------------|----------|--------------|------------------|------------------|-------------|-------------------|
| deepseek-ai/deepseek-v4-pro-0813 | 408 | TIMEOUT | 60321 | False | False | None | None |
| deepseek-ai/deepseek-v4-flash-0731 | 408 | TIMEOUT | 60109 | False | False | None | None |
| deepseek-ai/deepseek-v4-pro | 410 | GONE | 137 | True | True | None | None |
| deepseek-ai/deepseek-v4-flash | 410 | GONE | 120 | True | True | None | None |

### Layer 3 — Minimal Generation

| Model | HTTP Status | Success | Latency (ms) | Input Tokens | Output Tokens | Finish Reason | Output Complete | Preview |
|-------|-------------|---------|--------------|--------------|---------------|---------------|-----------------|---------|

### Layer 4 — NTPE Contract Probe

| Model | Fixture | Type | HTTP | Success | Latency | Contract Pass | Checks |
|-------|---------|------|------|---------|---------|---------------|--------|

## Final Classification

| Model | Name | Verdict | Failure Reason | Recommendations |
|-------|------|---------|----------------|-----------------|
| deepseek-ai/deepseek-v4-pro-0813 | DeepSeek V4 Pro (0813) | **TIMEOUT_BLOCKED** | Timeout at Layer 2: Timeout: HTTPSConnectionPool(host='integrate.api.nvidia.com', port=443): Read timed out. (read timeout=60) | — |
| deepseek-ai/deepseek-v4-flash-0731 | DeepSeek V4 Flash (0731) | **TIMEOUT_BLOCKED** | Timeout at Layer 2: Timeout: HTTPSConnectionPool(host='integrate.api.nvidia.com', port=443): Read timed out. (read timeout=60) | — |
| deepseek-ai/deepseek-v4-pro | DeepSeek V4 Pro (base) | **MODEL_EOL_OR_RETIRED** | Model/endpoint retired at Layer 2: HTTP 410: {"type":"about:blank","title":"Gone","status":410,"detail":"The model 'deepseek-ai/deepseek-v4-pro' has reached its end of life on 2026-08-07T09:00:00Z and is no longer available."}
 | — |
| deepseek-ai/deepseek-v4-flash | DeepSeek V4 Flash (base) | **MODEL_EOL_OR_RETIRED** | Model/endpoint retired at Layer 2: HTTP 410: {"type":"about:blank","title":"Gone","status":410,"detail":"The model 'deepseek-ai/deepseek-v4-flash' has reached its end of life on 2026-08-07T09:00:00Z and is no longer available."}
 | — |

## Compatibility Matrix

| Candidate | Provider | Model ID | Catalog | Endpoint | Generation | Contract | Verdict |
|-----------|----------|----------|---------|----------|------------|----------|---------|
| deepseek-ai/deepseek-v4-pro-0813 | NVIDIA | deepseek-ai/deepseek-v4-pro-0813 | PASS | FAIL (TIMEOUT) | FAIL | N/A | **TIMEOUT_BLOCKED** |
| deepseek-ai/deepseek-v4-flash-0731 | NVIDIA | deepseek-ai/deepseek-v4-flash-0731 | PASS | FAIL (TIMEOUT) | FAIL | N/A | **TIMEOUT_BLOCKED** |
| deepseek-ai/deepseek-v4-pro | NVIDIA | deepseek-ai/deepseek-v4-pro | PASS | FAIL (GONE) | FAIL | N/A | **MODEL_EOL_OR_RETIRED** |
| deepseek-ai/deepseek-v4-flash | NVIDIA | deepseek-ai/deepseek-v4-flash | PASS | FAIL (GONE) | FAIL | N/A | **MODEL_EOL_OR_RETIRED** |

## Summary

- **Phase Verdict**: **P3A2_PARTIAL**
- **Baseline Integrity**: PASS
- **AVAILABLE_COMPATIBLE**: 0 — None
- **AVAILABLE_PARTIAL**: 0 — None
- **AVAILABLE_INCOMPATIBLE**: 0 — None
- **PROVIDER_UNAVAILABLE**: 0 — None
- **MODEL_NOT_FOUND**: 0 — None
- **MODEL_EOL_OR_RETIRED**: 2 — deepseek-ai/deepseek-v4-pro, deepseek-ai/deepseek-v4-flash
- **RATE_LIMIT_BLOCKED**: 0 — None
- **TIMEOUT_BLOCKED**: 2 — deepseek-ai/deepseek-v4-pro-0813, deepseek-ai/deepseek-v4-flash-0731

## Phase 3A (Previous) Candidates Comparison

| Phase 3A Candidate | Provider | Verdict |
|--------------------|----------|---------|
| meta/llama-3.2-90b-vision-instruct | NVIDIA | AVAILABLE_PARTIAL |
| nvidia/riva-translate-4b-instruct-v2 | NVIDIA | AVAILABLE_PARTIAL |
| meta/llama-3.3-70b-instruct | NVIDIA | AVAILABLE_INCOMPATIBLE (EOL/410) |
| minimaxai/minimax-m3 | MiniMax | AVAILABLE_INCOMPATIBLE (429) |
| nvidia/llama-3.1-nemotron-70b-instruct | NVIDIA | PROVIDER_UNAVAILABLE (404) |

## DeepSeek V4 Specific Observations

### DeepSeek V4 Pro (0813) (deepseek-ai/deepseek-v4-pro-0813)

- **Endpoint Status**: HTTP 408 (TIMEOUT)
- **Latency**: 60321ms

### DeepSeek V4 Flash (0731) (deepseek-ai/deepseek-v4-flash-0731)

- **Endpoint Status**: HTTP 408 (TIMEOUT)
- **Latency**: 60109ms

### DeepSeek V4 Pro (base) (deepseek-ai/deepseek-v4-pro)

- **Endpoint Status**: HTTP 410 (GONE)
- **Latency**: 137ms

### DeepSeek V4 Flash (base) (deepseek-ai/deepseek-v4-flash)

- **Endpoint Status**: HTTP 410 (GONE)
- **Latency**: 120ms

## Recommended for Phase 3B


## Excluded from Phase 3B

- **deepseek-ai/deepseek-v4-pro-0813**: Timeout at Layer 2: Timeout: HTTPSConnectionPool(host='integrate.api.nvidia.com', port=443): Read timed out. (read timeout=60)
- **deepseek-ai/deepseek-v4-flash-0731**: Timeout at Layer 2: Timeout: HTTPSConnectionPool(host='integrate.api.nvidia.com', port=443): Read timed out. (read timeout=60)
- **deepseek-ai/deepseek-v4-pro**: Model/endpoint retired at Layer 2: HTTP 410: {"type":"about:blank","title":"Gone","status":410,"detail":"The model 'deepseek-ai/deepseek-v4-pro' has reached its end of life on 2026-08-07T09:00:00Z and is no longer available."}

- **deepseek-ai/deepseek-v4-flash**: Model/endpoint retired at Layer 2: HTTP 410: {"type":"about:blank","title":"Gone","status":410,"detail":"The model 'deepseek-ai/deepseek-v4-flash' has reached its end of life on 2026-08-07T09:00:00Z and is no longer available."}


## Compliance

- ✅ No credential leakage (only credential_source recorded)
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ No prompt/contract modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ No git commit/push/reset/clean/checkout
- ✅ Production model unchanged
- ✅ Provider runtime unchanged
- ✅ Translation contract unchanged
- ✅ Controlled request budget (no parallel/burst)
- ✅ Evidence saved to artifacts/p3a2_deepseek_probe/ only
- ✅ Existing Phase 3A candidates NOT re-run

## Phase Boundary

**Phase 3A.2 COMPLETE — STOP**

Do NOT:
- Select default model
- Modify default model
- Modify provider config
- Modify prompt
- Modify runtime
- Modify tests
- Commit
- Push
- Proceed to production migration

Next step: Human review of **P3A + P3A.2** compatibility evidence to decide Phase 3B candidate set.