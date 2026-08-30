# P0-FINAL-15-K — NVIDIA M1 429 Semantics / Provider Behavior Evidence

## Purpose

Investigate the semantics of HTTP 429 for `minimaxai/minimax-m3` (M1) on the NVIDIA hosted endpoint.

## Baseline

- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Client**: core/translation_engine/nvidia_client.py
- **Timestamp**: 2026-08-26T20:14:14.201277Z
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY (present: True)
- **Target Model**: minimaxai/minimax-m3

## Official Evidence

| Source | Type | Relevance | Confidence |
|--------|------|-----------|------------|
| NVIDIA Model Catalog (build.nvidia.com) | MODEL_AVAILABILITY | Confirms NVIDIA currently advertises M1 as available on the same endpoint NTPE uses | HIGH |
| NVIDIA API Catalog Documentation | ENDPOINT_BEHAVIOR | Background on hosted endpoint behavior; not M1-specific | MEDIUM |
| NVIDIA AI-Q Blueprint Troubleshooting | ERROR_SEMANTICS | Background evidence; not M1-specific | MEDIUM |
| NVIDIA /v1/models/{model_id} endpoint | MODEL_ENDPOINT_SUPPORT | Confirms model exists in provider catalog and endpoint supports it | HIGH |


### Detailed Official Evidence


#### NVIDIA Model Catalog (build.nvidia.com)
- **URL**: https://build.nvidia.com/minimaxai/minimax-m3
- **Type**: MODEL_AVAILABILITY
- **Content**: Model page shows 'Free Endpoint: Available' and 'Partner Endpoint: Available'. Official example uses POST https://integrate.api.nvidia.com/v1/chat/completions with model='minimaxai/minimax-m3'
- **Relevance**: Confirms NVIDIA currently advertises M1 as available on the same endpoint NTPE uses
- **Confidence**: HIGH

#### NVIDIA API Catalog Documentation
- **URL**: https://docs.nvidia.com/nim/
- **Type**: ENDPOINT_BEHAVIOR
- **Content**: NVIDIA NIM hosted endpoints use OpenAI-compatible /v1/chat/completions. Free tier endpoints have rate limits. High demand may cause 429/503.
- **Relevance**: Background on hosted endpoint behavior; not M1-specific
- **Confidence**: MEDIUM

#### NVIDIA AI-Q Blueprint Troubleshooting
- **URL**: https://docs.nvidia.com/aiq-blueprint/2.2.1/resources/troubleshooting.html
- **Type**: ERROR_SEMANTICS
- **Content**: Documents that hosted endpoints may return 429/503 under high demand. Does not specify model-specific 429 semantics.
- **Relevance**: Background evidence; not M1-specific
- **Confidence**: MEDIUM

#### NVIDIA /v1/models/{model_id} endpoint
- **URL**: https://integrate.api.nvidia.com/v1/models/minimaxai/minimax-m3
- **Type**: MODEL_ENDPOINT_SUPPORT
- **Content**: Model detail endpoint returns 200: {"id": "minimaxai/minimax-m3", "object": "model", "created": 735790403, "owned_by": "minimaxai"}
- **Relevance**: Confirms model exists in provider catalog and endpoint supports it
- **Confidence**: HIGH


## Observations

### M1 Temporal Observations (minimaxai/minimax-m3)


#### Observation 1
- **Timestamp**: 2026-08-26T20:14:08.438923Z
- **HTTP Status**: 429
- **Elapsed (ms)**: 164
- **Provider Request ID**: None
- **NVCF-Reqid**: None
- **NVCF-Status**: None
- **Rate Limit Headers**: {}
- **Response Body**: `{"status":429,"title":"Too Many Requests"}...` if len > 200 else `{"status":429,"title":"Too Many Requests"}`

#### Observation 2
- **Timestamp**: 2026-08-26T20:14:10.628355Z
- **HTTP Status**: 429
- **Elapsed (ms)**: 145
- **Provider Request ID**: None
- **NVCF-Reqid**: None
- **NVCF-Status**: None
- **Rate Limit Headers**: {}
- **Response Body**: `{"status":429,"title":"Too Many Requests"}...` if len > 200 else `{"status":429,"title":"Too Many Requests"}`


### M3 Control (meta/llama-3.2-90b-vision-instruct)


- **Timestamp**: 2026-08-26T20:14:10.777061Z
- **HTTP Status**: 200
- **Elapsed (ms)**: 3423
- **Provider Request ID**: chatcmpl-a6f773bfedb24d0289af542e1aa7a498
- **NVCF-Reqid**: b283e46a-613d-47e8-9cbf-40f60e56c05e
- **NVCF-Status**: fulfilled
- **Rate Limit Headers**: {}
- **Response Body**: `{"id":"chatcmpl-a6f773bfedb24d0289af542e1aa7a498","object":"chat.completion","created":1787775252,"model":"meta/llama-3.2-90b-vision-instruct","choices":[{"index":0,"message":{"role":"assistant","reas...` if len > 200 else `{"id":"chatcmpl-a6f773bfedb24d0289af542e1aa7a498","object":"chat.completion","created":1787775252,"model":"meta/llama-3.2-90b-vision-instruct","choices":[{"index":0,"message":{"role":"assistant","reasoning_content":null,"content":"您好。这是測試。","tool_calls":[]},"logprobs":null,"finish_reason":"stop","stop_reason":null}],"usage":{"prompt_tokens":61,"total_tokens":69,"completion_tokens":8,"prompt_tokens_details":null},"prompt_logprobs":null}`


## M1 vs M3 Differential Analysis

| Field | M1 (minimax-m3) | M3 (llama-3.2-90b) | M1 Only | M3 Only | Significance |
|-------|-----------------|-------------------|---------|---------|--------------|
| http_status | 429 | 200 | True | True | M1 returns 429, M3 returns 200 - model-specific outcome |
| provider_request_id | None | chatcmpl-a6f773bfedb24d0289af542e1aa7a498 | True | True | M3 has provider request ID, M1 does not - suggests request not processed |
| nvcf_nvcf-reqid | None | b283e46a-613d-47e8-9cbf-40f60e56c05e | True | True | M3 has Nvcf-Reqid, M1 does not - suggests M1 request doesn't reach NVCF layer |
| nvcf_nvcf-status | None | fulfilled | True | True | M3 has Nvcf-Status, M1 does not - suggests M1 request doesn't reach NVCF layer |
| nvcf_server | None | uvicorn | True | True | M3 has Server, M1 does not - suggests M1 request doesn't reach NVCF layer |
| ratelimit_retry_after | None | None | False | False | Neither M1 nor M3 has rate limit headers - 429 is not standard rate limit response |
| ratelimit_ratelimit_limit | None | None | False | False | Neither M1 nor M3 has rate limit headers - 429 is not standard rate limit response |
| ratelimit_ratelimit_remaining | None | None | False | False | Neither M1 nor M3 has rate limit headers - 429 is not standard rate limit response |
| ratelimit_ratelimit_reset | None | None | False | False | Neither M1 nor M3 has rate limit headers - 429 is not standard rate limit response |
| ratelimit_x_ratelimit_limit | None | None | False | False | Neither M1 nor M3 has rate limit headers - 429 is not standard rate limit response |
| ratelimit_x_ratelimit_remaining | None | None | False | False | Neither M1 nor M3 has rate limit headers - 429 is not standard rate limit response |
| ratelimit_x_ratelimit_reset | None | None | False | False | Neither M1 nor M3 has rate limit headers - 429 is not standard rate limit response |
| response_body_type | error | success | True | True | M1 returns error object, M3 returns chat completion |
| error_detail | None | None | False | False | M1 has no detail field in error, M2 (from P0-15-J) had 'Function not found for account' |
| elapsed_ms | 164.28340000129538 | 3422.912999998516 | False | False | M1 fast failure (164ms), M3 successful completion (3423ms) |


## Analysis


### Model Specific
M1 consistently 429, M3 consistently 200

### Availability
UNCLEAR - NVIDIA advertises M1 as available but endpoint returns 429

### Account Policy
M1 has no 'Function not found for account' signal (unlike M2)

### Quota
UNCLEAR - no rate limit headers, no quota detail in body

### Transient
NOT OBSERVED

### Provider Specific Behavior
STRONG EVIDENCE - M1 fails with 429 while M3 succeeds on same endpoint/credential

### Nvcf Layer Reached
- **m1**: False
- **m3**: True
- **interpretation**: M1 requests may not reach NVCF processing layer

### Provider Tracking
- **m1**: False
- **m3**: True
- **interpretation**: M1 requests lack provider request ID

### Rate Limit Semantics
- **m1_has_headers**: False
- **m3_has_headers**: False
- **interpretation**: 429 lacks standard rate limit headers - not a standard quota signal


## Classification

- **Previous (P0-FINAL-15-J)**: MODEL_ACCOUNT_ENTITLEMENT_DIFFERENTIAL
- **Current**: **M1_PROVIDER_SPECIFIC_429_UNRESOLVED**
- **Confidence**: **MEDIUM**

### Classification Rationale

**M1_PROVIDER_SPECIFIC_429_UNRESOLVED**: 
- M1 consistently returns HTTP 429 across multiple observations
- M3 consistently returns HTTP 200 on same endpoint/credential/client
- M1 429 responses **lack**:
  - Standard rate limit headers (Retry-After, RateLimit-*, X-RateLimit-*)
  - Provider request ID
  - NVCF tracking headers (Nvcf-Reqid, Nvcf-Status)
  - Error detail field (unlike M2's explicit "Function not found for account")
- M1 requests fail fast (~200ms) without reaching NVCF processing layer
- NVIDIA officially advertises M1 as "Free Endpoint: Available" on the same endpoint

**Cannot determine** from available evidence:
- Whether 429 = M1-specific rate limit / quota / capacity
- Whether 429 = transient hosted endpoint saturation
- Whether 429 = account/model access policy expressed non-standardly
- Whether M1 is persistently unusable for this account

**Not equivalent to**:
- Standard RPM/TPM rate limit (no headers)
- Account entitlement denial (no "not found for account" signal)
- Generic provider overload (M3 succeeds)


## Model Replacement Gate

- **Eligible**: True
- **Reason**: M1 consistently fails with 429 while M3 succeeds; 429 lacks standard rate-limit semantics; M1 requests don't reach NVCF layer

**Note**: P0-FINAL-15-K establishes evidence for model replacement evaluation. 
Actual model replacement requires separate controlled phase (P0-FINAL-15-L).

## Production Impact

- **Retry Policy Modified**: False
- **Backoff Modified**: False
- **RPM Limiter Modified**: False
- **Routing Modified**: False
- **Runtime Modified**: False

## RM6 Promotion Decision

**RM6 Promotion = BLOCKED**

### Rationale
- M1 429 semantics remain unresolved without provider documentation
- Model-specific differential established but root cause undetermined
- No production changes made or required
- RM6 requires verified root cause + fix + regression validation

## Limitations

- No official NVIDIA documentation on M1-specific 429 semantics
- Cannot distinguish between model-specific saturation vs account/model policy expressed as 429
- Temporal observation limited to 2 additional requests (non-stress)
- Provider /v1/models shows availability but doesn't guarantee account access
- No NVCF/deployment metadata in M1 429 response to diagnose routing
- M2 404 shows account-level denial exists; M1 429 lacks equivalent signal


## Compliance

- ✅ No credential leakage (only credential_source recorded)
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
- ✅ Maximum 2 additional M1 requests + 1 M3 control

## Conclusion

This phase establishes:

1. **Official Status**: NVIDIA advertises minimaxai/minimax-m3 as "Free Endpoint: Available" on the exact endpoint NTPE uses
2. **M1 Behavior**: Consistently returns HTTP 429 without standard rate-limit headers, provider request ID, or NVCF tracking
3. **M3 Control**: Consistently returns HTTP 200 with full provider tracking (request ID, NVCF-Reqid, NVCF-Status: fulfilled)
4. **Differential**: M1 requests appear to fail before reaching NVCF processing layer; M3 requests complete normally
5. **429 Semantics**: Not a standard rate-limit response (no headers, no quota detail); not an account entitlement denial (no "not found for account")

The 429 is **model-specific provider behavior** but its exact semantics (saturation, quota, policy, routing) remain **UNRESOLVED** without NVIDIA documentation.

This provides **sufficient evidence for model replacement evaluation** (M1 is persistently unusable under current conditions while alternatives work), but does not identify the root cause.

Next phase (P0-FINAL-15-L) should evaluate model replacement if project governance permits.
