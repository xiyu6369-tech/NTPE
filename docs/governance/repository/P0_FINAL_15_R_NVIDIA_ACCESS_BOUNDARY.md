# P0-FINAL-15-R — NVIDIA Access Boundary Investigation

## Phase R-A1: Current Account Access Verification

### Baseline
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY (present: True)
- **Timestamp**: 2026-08-29T06:45:05.087603Z

### Summary

| Metric | Count |
|--------|-------|
| Models Tested | 39 |
| Catalog Available | 39 |
| Endpoint Available | 39 |
| Account Entitled | 11 |
| Invocation Success | 11 |

### Access Classifications

| Classification | Count |
|----------------|-------|
| ACCOUNT_NOT_ENTITLED | 28 |
| FULLY_AVAILABLE | 11 |

### Detailed Results

| Model | Catalog | Endpoint | Entitled | Chat HTTP | Classification |
|-------|---------|----------|----------|-----------|----------------|
| 01-ai/yi-large | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| ai21labs/jamba-1.5-large-instruct | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| deepseek-ai/deepseek-v4-flash-0731 | True | True | True | 200 | FULLY_AVAILABLE |
| deepseek-ai/deepseek-v4-pro-0813 | True | True | True | 200 | FULLY_AVAILABLE |
| google/gemma-2b | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| google/gemma-3-12b-it | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| google/gemma-3-4b-it | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| google/gemma-4-31b-it | True | True | True | 200 | FULLY_AVAILABLE |
| google/recurrentgemma-2b | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| ibm/granite-3.0-3b-a800m-instruct | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| ibm/granite-3.0-8b-instruct | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| meta/llama2-70b | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| microsoft/phi-3.5-moe-instruct | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| minimaxai/minimax-m3 | True | True | True | 200 | FULLY_AVAILABLE |
| mistralai/mistral-7b-instruct-v0.3 | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| mistralai/mistral-large | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| mistralai/mistral-large-2-instruct | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| mistralai/mistral-nemotron | True | True | False | 408 | ACCOUNT_NOT_ENTITLED |
| mistralai/mixtral-8x22b-v0.1 | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| nv-mistralai/mistral-nemo-12b-instruct | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| nvidia/llama-3.1-nemotron-51b-instruct | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| nvidia/llama-3.1-nemotron-70b-instruct | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| nvidia/llama-3.1-nemotron-ultra-253b-v1 | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| nvidia/llama3-chatqa-1.5-70b | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| nvidia/mistral-nemo-minitron-8b-8k-instruct | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| nvidia/nemotron-3-nano-30b-a3b | True | True | True | 200 | FULLY_AVAILABLE |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | True | True | True | 200 | FULLY_AVAILABLE |
| nvidia/nemotron-3-super-120b-a12b | True | True | True | 200 | FULLY_AVAILABLE |
| nvidia/nemotron-3-ultra-550b-a55b | True | True | True | 200 | FULLY_AVAILABLE |
| nvidia/nemotron-3.5-lightning-30b-a3b | True | True | True | 200 | FULLY_AVAILABLE |
| nvidia/nemotron-4-340b-instruct | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| nvidia/nemotron-nano-3-30b-a3b | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| openai/gpt-oss-120b | True | True | True | 200 | FULLY_AVAILABLE |
| openai/gpt-oss-20b | True | True | True | 200 | FULLY_AVAILABLE |
| writer/palmyra-creative-122b | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| writer/palmyra-fin-70b-32k | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| writer/palmyra-med-70b | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| writer/palmyra-med-70b-32k | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |
| zyphra/zamba2-7b-instruct | True | True | False | 404 | ACCOUNT_NOT_ENTITLED |

### M1 Specific Analysis


- **Model**: minimaxai/minimax-m3
- **Catalog Available**: True
- **Endpoint Available**: True
- **Account Entitled**: True
- **Chat HTTP Status**: 200
- **Chat Latency**: 943ms
- **Provider Request ID**: chatcmpl-3c814f13-2934-4367-a4c6-fd0355b52e65
- **NVCF ReqID**: 1fe4c841-479a-4a2d-88e5-358440abc862
- **NVCF Status**: fulfilled
- **Error**: None
- **Access Classification**: FULLY_AVAILABLE
- **Chat Response Body**: 你好。

### Key Findings for M1


## Limitations
- Single chat completion attempt per model (not repeated for stability)
- Cannot distinguish model-specific vs account-wide entitlement without provider API
- 429 on M1 could be rate limit, capacity, or provider routing - not definitively classified
- Credential source is single NVIDIA account; no comparison account available

## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ No retry/RPM/timeout/backoff changes
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved
- ✅ Historical evidence retained

## Next Phase
Proceed to **R-A2: M1 429 Reconciliation** and **R-A3: Account Comparison (if alternative credentials available)**.
