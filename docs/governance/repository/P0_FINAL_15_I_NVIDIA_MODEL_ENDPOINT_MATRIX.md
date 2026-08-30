# P0-FINAL-15-I — NVIDIA Provider Request Eligibility / Model-Endpoint Matrix

## A. Scope

### What Was Tested
- Provider request eligibility across multiple models on the same NVIDIA endpoint
- Identical request conditions (endpoint, credential, request format, client) with only MODEL variable changed
- Single-chunk, no-retry, no-concurrency controlled requests

### What Was Explicitly Not Tested
- Rate limit stress testing (no burst, no >2 requests per model)
- Production retry/backoff behavior
- RPM limiter modifications
- Quota exhaustion scenarios
- Concurrent request behavior

## B. Environment

- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Models Tested**: minimaxai/minimax-m3, nvidia/llama-3.1-nemotron-70b-instruct, meta/llama-3.2-90b-vision-instruct
- **Models Unavailable**: None
- **Python Version**: 3.14.6
- **Client Path**: core/translation_engine/nvidia_client.py
- **Test Timestamp**: 2026-08-26T19:14:36.110617Z
- **Git Commit**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **Branch**: main
- **Credential Present**: True
- **Credential Source**: NVIDIA_API_KEY

## C. Matrix

| Test ID | Model | Request # | HTTP Status | Success | Elapsed (ms) | Limiter Wait (ms) |
|---------|-------|-----------|-------------|---------|--------------|-------------------|
| I-01 | minimaxai/minimax-m3 | 1 | 429 | False | 176 | 0 |
| I-02 | nvidia/llama-3.1-nemotron-70b-instruct | 1 | 404 | False | 160 | 1323 |
| I-03 | meta/llama-3.2-90b-vision-instruct | 1 | 200 | True | 3453 | 1339 |
| I-04 | minimaxai/minimax-m3 | 2 | 429 | False | 145 | 0 |
| I-05 | nvidia/llama-3.1-nemotron-70b-instruct | 2 | 404 | False | 154 | 1354 |


## D. Evidence

### Detailed Results

#### I-01 — minimaxai/minimax-m3
- **Timestamp**: 2026-08-26T19:14:27.997378Z
- **HTTP Status**: 429
- **Success**: False
- **Elapsed (ms)**: 176
- **Client Limiter RPM Limit**: 40
- **Client Limiter Observed Wait (ms)**: 0
- **Client Limiter Request Index**: 1
- **Request ID**: None
- **Retry-After**: None
- **RateLimit-Limit**: None
- **RateLimit-Remaining**: None
- **RateLimit-Reset**: None
- **X-RateLimit-Limit**: None
- **X-RateLimit-Remaining**: None
- **X-RateLimit-Reset**: None
- **Provider Request ID**: None
- **Exception Type**: None
- **Exception Message**: None
- **Response Body**: {"status":429,"title":"Too Many Requests"}

#### I-02 — nvidia/llama-3.1-nemotron-70b-instruct
- **Timestamp**: 2026-08-26T19:14:28.174482Z
- **HTTP Status**: 404
- **Success**: False
- **Elapsed (ms)**: 160
- **Client Limiter RPM Limit**: 40
- **Client Limiter Observed Wait (ms)**: 1323
- **Client Limiter Request Index**: 1
- **Request ID**: None
- **Retry-After**: None
- **RateLimit-Limit**: None
- **RateLimit-Remaining**: None
- **RateLimit-Reset**: None
- **X-RateLimit-Limit**: None
- **X-RateLimit-Remaining**: None
- **X-RateLimit-Reset**: None
- **Provider Request ID**: None
- **Exception Type**: None
- **Exception Message**: None
- **Response Body**: {"status":404,"title":"Not Found","detail":"Function '9b96341b-9791-4db9-a00d-4e43aa192a39': Not found for account '1V0ANVqp2OBpPKuHKGA1zY_YgNj09uy7yYnM52Boax4'"}

#### I-03 — meta/llama-3.2-90b-vision-instruct
- **Timestamp**: 2026-08-26T19:14:29.659414Z
- **HTTP Status**: 200
- **Success**: True
- **Elapsed (ms)**: 3453
- **Client Limiter RPM Limit**: 40
- **Client Limiter Observed Wait (ms)**: 1339
- **Client Limiter Request Index**: 1
- **Request ID**: None
- **Retry-After**: None
- **RateLimit-Limit**: None
- **RateLimit-Remaining**: None
- **RateLimit-Reset**: None
- **X-RateLimit-Limit**: None
- **X-RateLimit-Remaining**: None
- **X-RateLimit-Reset**: None
- **Provider Request ID**: chatcmpl-439fa62e3f124f03b090e07cd8fb4f2e
- **Exception Type**: None
- **Exception Message**: None
- **Response Body**: {"id":"chatcmpl-439fa62e3f124f03b090e07cd8fb4f2e","object":"chat.completion","created":1787771672,"model":"meta/llama-3.2-90b-vision-instruct","choices":[{"index":0,"message":{"role":"assistant","reasoning_content":null,"content":"你好。这是测试。","tool_calls":[]},"logprobs":null,"finish_reason":"stop","stop_reason":null}],"usage":{"prompt_tokens":61,"total_tokens":68,"completion_tokens":7,"prompt_tokens_details":null},"prompt_logprobs":null}

#### I-04 — minimaxai/minimax-m3
- **Timestamp**: 2026-08-26T19:14:34.454430Z
- **HTTP Status**: 429
- **Success**: False
- **Elapsed (ms)**: 145
- **Client Limiter RPM Limit**: 40
- **Client Limiter Observed Wait (ms)**: 0
- **Client Limiter Request Index**: 2
- **Request ID**: None
- **Retry-After**: None
- **RateLimit-Limit**: None
- **RateLimit-Remaining**: None
- **RateLimit-Reset**: None
- **X-RateLimit-Limit**: None
- **X-RateLimit-Remaining**: None
- **X-RateLimit-Reset**: None
- **Provider Request ID**: None
- **Exception Type**: None
- **Exception Message**: None
- **Response Body**: {"status":429,"title":"Too Many Requests"}

#### I-05 — nvidia/llama-3.1-nemotron-70b-instruct
- **Timestamp**: 2026-08-26T19:14:34.601188Z
- **HTTP Status**: 404
- **Success**: False
- **Elapsed (ms)**: 154
- **Client Limiter RPM Limit**: 40
- **Client Limiter Observed Wait (ms)**: 1354
- **Client Limiter Request Index**: 2
- **Request ID**: None
- **Retry-After**: None
- **RateLimit-Limit**: None
- **RateLimit-Remaining**: None
- **RateLimit-Reset**: None
- **X-RateLimit-Limit**: None
- **X-RateLimit-Remaining**: None
- **X-RateLimit-Reset**: None
- **Provider Request ID**: None
- **Exception Type**: None
- **Exception Message**: None
- **Response Body**: {"status":404,"title":"Not Found","detail":"Function '9b96341b-9791-4db9-a00d-4e43aa192a39': Not found for account '1V0ANVqp2OBpPKuHKGA1zY_YgNj09uy7yYnM52Boax4'"}


## E. Differential Analysis

### Model Differential
{
  "minimaxai/minimax-m3": {
    "status_codes": [
      429,
      429
    ],
    "successes": 0,
    "failures": 2
  },
  "nvidia/llama-3.1-nemotron-70b-instruct": {
    "status_codes": [
      404,
      404
    ],
    "successes": 0,
    "failures": 2
  },
  "meta/llama-3.2-90b-vision-instruct": {
    "status_codes": [
      200
    ],
    "successes": 1,
    "failures": 0
  }
}

### Key Questions Answered
- **Does model choice correlate with 429?**: {'minimaxai/minimax-m3': {'status_codes': [429, 429], 'successes': 0, 'failures': 2}, 'nvidia/llama-3.1-nemotron-70b-instruct': {'status_codes': [404, 404], 'successes': 0, 'failures': 2}, 'meta/llama-3.2-90b-vision-instruct': {'status_codes': [200], 'successes': 1, 'failures': 0}}
- **Does endpoint remain constant?**: True
- **Does authentication remain constant?**: True

## F. Classification

- **Previous**: UNKNOWN
- **Current**: **NON_UNIFORM_PROVIDER_BEHAVIOR**

### Classification Rationale

**NON-UNIFORM PROVIDER BEHAVIOR**: Different models return different error classes (429, 5xx, 200).
This suggests complex provider state that cannot be simplified to rate limiting.


## G. Promotion Decision

**RM6 Promotion = BLOCKED**

This phase only performs differential diagnosis. Promotion requires:
1. Root cause identification
2. Verified fix implementation
3. Regression test validation
4. Governance approval

## Compliance

- ✅ No credential leakage (only credential_source recorded)
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
