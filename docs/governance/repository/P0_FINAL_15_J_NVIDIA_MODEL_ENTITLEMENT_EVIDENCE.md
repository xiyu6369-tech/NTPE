# P0-FINAL-15-J — NVIDIA Account Model Entitlement & Provider Model Availability Evidence

## Purpose

Establish evidence chain for model availability/entitlement differential observed in P0-FINAL-15-I:
- M1 (minimaxai/minimax-m3): HTTP 429
- M2 (nvidia/llama-3.1-nemotron-70b-instruct): HTTP 404 "Function not found for account"
- M3 (meta/llama-3.2-90b-vision-instruct): HTTP 200

## Scope

### In Scope
- Local NTPE configuration inventory (model catalog, provider adapter, provider_config.json)
- Official NVIDIA /v1/models catalog endpoint
- Account entitlement evidence from provider responses
- Actual HTTP results from P0-FINAL-15-I
- Classification of 429/404/200 differential

### Out of Scope
- Rate limit stress testing
- Production retry/backoff modification
- RPM limiter changes
- Concurrency/burst testing
- Quota exhaustion verification
- Credential rotation or new account provisioning

## Baseline

- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Client**: core/translation_engine/nvidia_client.py
- **Timestamp**: 2026-08-26T19:36:06.280250Z
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY (present: True)

## Provider Endpoint

- **Chat Completions**: https://integrate.api.nvidia.com/v1/chat/completions
- **Models List**: https://integrate.api.nvidia.com/v1/models
- **Model Detail**: https://integrate.api.nvidia.com/v1/models/{model_id}
- **Protocol**: OpenAI-compatible REST
- **Auth**: Bearer token (NVIDIA_API_KEY)

## Credential Handling

- **Credential Present**: True
- **Credential Source**: NVIDIA_API_KEY
- **Secret Exposed**: False (only credential_source recorded, no token values)

## Model Matrix

| Model | NTPE Catalog | Provider Adapter | Provider Config | Provider Catalog | Endpoint Support | Account Evidence | HTTP Status | Classification | Confidence |
|-------|--------------|------------------|-----------------|------------------|------------------|------------------|-------------|----------------|------------|
| minimaxai/minimax-m3 | True | True | True | True | True | UNCLEAR | 429 | UNCLEAR | LOW |
| nvidia/llama-3.1-nemotron-70b-instruct | False | False | False | True | True | NOT_ENTITLED | 404 | ACCOUNT_NOT_ENTITLED | HIGH |
| meta/llama-3.2-90b-vision-instruct | False | False | False | True | True | ENTITLED | 200 | ACCOUNT_ENTITLED | HIGH |


## Catalog Evidence

### NTPE Static Model Catalog (core/launcher_product/model_catalog.py)

#### minimaxai/minimax-m3
- **In Catalog**: True
- **Enabled**: True
- **Experimental**: False
- **Context Notes**: Static catalog entry used by the existing NVIDIA CLI.

#### nvidia/llama-3.1-nemotron-70b-instruct
- **In Catalog**: False
- **Enabled**: None
- **Experimental**: None
- **Context Notes**: None

#### meta/llama-3.2-90b-vision-instruct
- **In Catalog**: False
- **Enabled**: None
- **Experimental**: None
- **Context Notes**: None


### NTPE Provider Adapter Config (core/ai_provider/adapters.py)

#### minimaxai/minimax-m3
- **In Adapter Config**: True

#### nvidia/llama-3.1-nemotron-70b-instruct
- **In Adapter Config**: False

#### meta/llama-3.2-90b-vision-instruct
- **In Adapter Config**: False


### Provider Config JSON (config/provider_config.json)

#### minimaxai/minimax-m3
- **Is Default Model**: N/A
- **Is Fallback Model**: N/A
- **Default Model**: N/A
- **Fallback Models**: N/A

#### nvidia/llama-3.1-nemotron-70b-instruct
- **Is Default Model**: N/A
- **Is Fallback Model**: N/A
- **Default Model**: N/A
- **Fallback Models**: N/A

#### meta/llama-3.2-90b-vision-instruct
- **Is Default Model**: N/A
- **Is Fallback Model**: N/A
- **Default Model**: N/A
- **Fallback Models**: N/A


### Official NVIDIA /v1/models Catalog

#### minimaxai/minimax-m3
- **In Catalog**: True
- **Owned By**: minimaxai
- **Endpoint Supports**: True

#### nvidia/llama-3.1-nemotron-70b-instruct
- **In Catalog**: True
- **Owned By**: nvidia
- **Endpoint Supports**: True

#### meta/llama-3.2-90b-vision-instruct
- **In Catalog**: True
- **Owned By**: meta
- **Endpoint Supports**: True


## Account Evidence

### M2 (nvidia/llama-3.1-nemotron-70b-instruct) - HTTP 404 Analysis

**Response Body**: `{"status":404,"title":"Not Found","detail":"Function '9b96341b-9791-4db9-a00d-4e43aa192a39': Not found for account '1V0ANVqp2OBpPKuHKGA1zY_YgNj09uy7yYnM52Boax4'"}`

**Parsed Analysis**:
- **Function ID**: 9b96341b-9791-4db9-a00d-4e43aa192a39
- **Account ID**: 1V0ANVqp2OBpPKuHKGA1zY_YgNj09uy7yYnM52Boax4
- **Semantics**: Function not found for account - indicates model not deployed/entitled for this account
- **Evidence Type**: PROVIDER_RESPONSE

**Interpretation**: The explicit "Function not found for account" message indicates this model is not deployed as an invokable function for the requesting account. This is an account-level entitlement signal, not a generic rate limit.


### M3 (meta/llama-3.2-90b-vision-instruct) - HTTP 200 Analysis

**Response Body**: `{"id":"chatcmpl-439fa62e3f124f03b090e07cd8fb4f2e","object":"chat.completion","created":1787771672,"model":"meta/llama-3.2-90b-vision-instruct","choices":[{"index":0,"message":{"role":"assistant","reas...`

**Key Headers**:
- **Nvcf-Reqid**: 08dee51b-7b3a-45bb-9e94-06329e3793db
- **Nvcf-Status**: fulfilled
- **Provider Request ID**: chatcmpl-439fa62e3f124f03b090e07cd8fb4f2e

**Semantics**: Successful completion with provider request ID and NVCF tracking

**Interpretation**: Successful completion with full provider tracking (NVCF request ID, status fulfilled) confirms account entitlement and endpoint capability for this model.


### M1 (minimaxai/minimax-m3) - HTTP 429 Analysis

**Response Body**: `{"status":429,"title":"Too Many Requests"}`

**Key Observations**:
- **Status**: 429
- **Title**: Too Many Requests
- **Rate Limit Headers**: False
- **Semantics**: Generic 'Too Many Requests' without rate-limit headers or quota detail

**Interpretation**: The 429 response lacks:
- RateLimit-* headers
- Retry-After header
- X-RateLimit-* headers
- Quota-type detail in body (no "requests per minute", "tokens per minute", "concurrent", "account quota", "model quota")

This differs from M2's explicit account entitlement signal (404 with function/account IDs) and M3's success with full provider metadata.


## Classification

- **Previous (P0-FINAL-15-I)**: NON_UNIFORM_PROVIDER_BEHAVIOR
- **Current**: **MODEL_ACCOUNT_ENTITLEMENT_DIFFERENTIAL**
- **Confidence**: **HIGH**

### Classification Rationale

**MODEL_ACCOUNT_ENTITLEMENT_DIFFERENTIAL**: 
- M2 receives explicit account-level denial: "Function not found for account"
- M3 receives successful completion with provider tracking
- This confirms account entitlement varies by model

**Cannot directly explain M1's 429** from this evidence alone. M1's 429 lacks:
- Account entitlement denial signal (no "not found for account")
- Rate limit detail (no headers, no quota type in body)
- Model-specific quota indication

M1 remains ambiguous: could be model-specific rate limit, model-specific capacity, or different routing.


## Production Impact

- **Retry Policy Modified**: False
- **Backoff Modified**: False
- **RPM Limiter Modified**: False
- **Admission Modified**: False
- **Runtime Modified**: False

## RM6 Promotion Decision

**RM6 Promotion = BLOCKED**

### Rationale
- M1 429 cause remains undetermined without provider documentation
- Cannot verify if 429 = rate limit, capacity, or entitlement rejection
- No production changes made or required
- Entitlement differential established for M2 vs M3 only

## Limitations

- No direct account entitlement API available
- Cannot distinguish M1 429 cause without provider documentation
- M2 404 indicates account-level function deployment absence, not necessarily model-level denial
- Provider /v1/models lists model but doesn't guarantee account access
- No official NVIDIA documentation on 429 vs 404 semantics for entitlement


## Compliance

- ✅ No credential leakage (only credential_source recorded)
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
- ✅ Reuses P0-FINAL-15-I evidence (no new provider requests for M1/M2/M3)

## Conclusion

This phase establishes:

1. **M2 (nvidia/llama-3.1-nemotron-70b-instruct)**: Explicitly NOT entitled for this account (404 "Function not found for account")
2. **M3 (meta/llama-3.2-90b-vision-instruct)**: Explicitly entitled (200 with provider tracking)
3. **M1 (minimaxai/minimax-m3)**: 429 without rate-limit headers or quota detail — **cause undetermined**

The entitlement differential is proven between M2 and M3. M1 requires provider documentation or account-level API to classify.

Next phase (if any) should target:
- NVIDIA provider documentation on 429 semantics
- Account model access API (if available)
- Minimax M3 specific deployment status for this account
