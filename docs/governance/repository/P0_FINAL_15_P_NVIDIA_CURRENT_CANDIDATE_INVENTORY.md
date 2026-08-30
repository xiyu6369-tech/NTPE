# P0-FINAL-15-P — NVIDIA Current Candidate Inventory

## Phase A: Catalog Verification

### Environment
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY (present: True)
- **Timestamp**: 2026-08-28T20:31:42.561681Z

### NVIDIA /v1/models Catalog
- **Fetch Status**: SUCCESS
- **HTTP Status**: 200
- **Models Count**: 83

## Phase B: Account/Endpoint Verification

### Priority Candidates (Section 8)
- deepseek-ai/DeepSeek-V4-Pro-0813
- deepseek-ai/DeepSeek-V4-Flash-0731
- google/gemma-4-31b

### All Screened Candidates (86 total)
- deepseek-ai/DeepSeek-V4-Pro-0813
- deepseek-ai/DeepSeek-V4-Flash-0731
- google/gemma-4-31b
- 01-ai/yi-large
- adept/fuyu-8b
- ai21labs/jamba-1.5-large-instruct
- aisingapore/sea-lion-7b-instruct
- bigcode/starcoder2-15b
- databricks/dbrx-instruct
- deepseek-ai/deepseek-coder-6.7b-instruct
- deepseek-ai/deepseek-v4-flash-0731
- deepseek-ai/deepseek-v4-pro-0813
- google/codegemma-1.1-7b
- google/codegemma-7b
- google/deplot
- google/diffusiongemma-26b-a4b-it
- google/gemma-2b
- google/gemma-3-12b-it
- google/gemma-3-4b-it
- google/gemma-4-31b-it
- google/recurrentgemma-2b
- ibm/granite-3.0-3b-a800m-instruct
- ibm/granite-3.0-8b-instruct
- ibm/granite-34b-code-instruct
- ibm/granite-8b-code-instruct
- meta/codellama-70b
- meta/llama-3.2-11b-vision-instruct
- meta/llama-3.2-90b-vision-instruct
- meta/llama-guard-4-12b
- meta/llama2-70b
- meta/muse-glimmer-30b
- microsoft/kosmos-2
- microsoft/phi-3-vision-128k-instruct
- microsoft/phi-3.5-moe-instruct
- minimaxai/minimax-m3
- mistralai/codestral-22b-instruct-v0.1
- mistralai/mistral-7b-instruct-v0.3
- mistralai/mistral-large
- mistralai/mistral-large-2-instruct
- mistralai/mistral-nemotron
- mistralai/mixtral-8x22b-v0.1
- moonshotai/kimi-k2.6
- moonshotai/kimi-k3
- nv-mistralai/mistral-nemo-12b-instruct
- nvidia/ai-synthetic-video-detector
- nvidia/cosmos-reason2-8b
- nvidia/embed-qa-4
- nvidia/ising-calibration-1.5-31b
- nvidia/llama-3.1-nemoguard-8b-content-safety
- nvidia/llama-3.1-nemoguard-8b-topic-control
- nvidia/llama-3.1-nemotron-51b-instruct
- nvidia/llama-3.1-nemotron-70b-instruct
- nvidia/llama-3.1-nemotron-safety-guard-8b-v3
- nvidia/llama-3.1-nemotron-ultra-253b-v1
- nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1
- nvidia/llama-3.2-nv-embedqa-1b-v1
- nvidia/llama-nemotron-embed-vl-1b-v2
- nvidia/llama3-chatqa-1.5-70b
- nvidia/mistral-nemo-minitron-8b-8k-instruct
- nvidia/nemotron-3-embed-1b
- nvidia/nemotron-3-nano-30b-a3b
- nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
- nvidia/nemotron-3-super-120b-a12b
- nvidia/nemotron-3-ultra-550b-a55b
- nvidia/nemotron-3.5-content-safety
- nvidia/nemotron-3.5-lightning-30b-a3b
- nvidia/nemotron-4-340b-instruct
- nvidia/nemotron-4-340b-reward
- nvidia/nemotron-nano-3-30b-a3b
- nvidia/nemotron-parse
- nvidia/neva-22b
- nvidia/nv-embedqa-mistral-7b-v2
- nvidia/nvclip
- nvidia/riva-translate-4b-instruct
- nvidia/riva-translate-4b-instruct-v1.1
- nvidia/riva-translate-4b-instruct-v2
- nvidia/vila
- openai/gpt-oss-120b
- openai/gpt-oss-20b
- poolside/laguna-xs-2.1
- snowflake/arctic-embed-l
- writer/palmyra-creative-122b
- writer/palmyra-fin-70b-32k
- writer/palmyra-med-70b
- writer/palmyra-med-70b-32k
- zyphra/zamba2-7b-instruct

## Screening Results

| Model | In Catalog | Catalog Avail | Endpoint Avail | Account Entitled | Invocation Success | HTTP Status | Required | Preferred | Classification |
|-------|------------|---------------|----------------|------------------|-------------------|-------------|----------|-----------|----------------|
| deepseek-ai/DeepSeek-V4-Pro-0813 | False | False | False | False | False | None | False | 4/7 | SCREENED_OUT_REQUIRED |
| deepseek-ai/DeepSeek-V4-Flash-0731 | False | False | False | False | False | None | False | 4/7 | SCREENED_OUT_REQUIRED |
| google/gemma-4-31b | False | False | False | False | False | None | False | 4/7 | SCREENED_OUT_REQUIRED |
| 01-ai/yi-large | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| adept/fuyu-8b | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| ai21labs/jamba-1.5-large-instruct | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| aisingapore/sea-lion-7b-instruct | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| bigcode/starcoder2-15b | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| databricks/dbrx-instruct | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| deepseek-ai/deepseek-coder-6.7b-instruct | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| deepseek-ai/deepseek-v4-flash-0731 | True | True | True | False | False | 408 | False | 4/7 | SCREENED_OUT_REQUIRED |
| deepseek-ai/deepseek-v4-pro-0813 | True | True | True | True | True | 200 | False | 5/7 | SCREENED_OUT_REQUIRED |
| google/codegemma-1.1-7b | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| google/codegemma-7b | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| google/deplot | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| google/diffusiongemma-26b-a4b-it | True | True | True | True | True | 200 | False | 5/7 | SCREENED_OUT_REQUIRED |
| google/gemma-2b | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| google/gemma-3-12b-it | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| google/gemma-3-4b-it | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| google/gemma-4-31b-it | True | True | True | True | True | 200 | False | 5/7 | SCREENED_OUT_REQUIRED |
| google/recurrentgemma-2b | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| ibm/granite-3.0-3b-a800m-instruct | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| ibm/granite-3.0-8b-instruct | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| ibm/granite-34b-code-instruct | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| ibm/granite-8b-code-instruct | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| meta/codellama-70b | True | True | True | False | False | 404 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| meta/llama-3.2-11b-vision-instruct | True | True | True | True | True | 200 | False | 5/7 | SCREENED_OUT_REQUIRED |
| meta/llama-3.2-90b-vision-instruct | True | True | True | True | True | 200 | False | 5/7 | SCREENED_OUT_REQUIRED |
| meta/llama-guard-4-12b | True | True | True | False | False | 400 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| meta/llama2-70b | True | True | True | False | False | 404 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| meta/muse-glimmer-30b | True | True | True | True | True | 200 | False | 3/7 | SCREENED_OUT_REQUIRED |
| microsoft/kosmos-2 | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| microsoft/phi-3-vision-128k-instruct | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| microsoft/phi-3.5-moe-instruct | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| minimaxai/minimax-m3 | True | True | True | True | True | 200 | True | 5/7 | PRIMARY_CANDIDATE |
| mistralai/codestral-22b-instruct-v0.1 | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| mistralai/mistral-7b-instruct-v0.3 | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| mistralai/mistral-large | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| mistralai/mistral-large-2-instruct | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| mistralai/mistral-nemotron | True | True | True | False | False | 408 | False | 4/7 | SCREENED_OUT_REQUIRED |
| mistralai/mixtral-8x22b-v0.1 | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| moonshotai/kimi-k2.6 | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| moonshotai/kimi-k3 | True | True | True | False | False | 400 | False | 2/7 | SCREENED_OUT_REQUIRED |
| nv-mistralai/mistral-nemo-12b-instruct | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| nvidia/ai-synthetic-video-detector | True | True | True | False | False | 500 | False | 2/7 | SCREENED_OUT_REQUIRED |
| nvidia/cosmos-reason2-8b | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| nvidia/embed-qa-4 | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| nvidia/ising-calibration-1.5-31b | True | True | True | True | True | 200 | False | 3/7 | SCREENED_OUT_REQUIRED |
| nvidia/llama-3.1-nemoguard-8b-content-safety | True | True | True | True | True | 200 | True | 5/7 | PRIMARY_CANDIDATE |
| nvidia/llama-3.1-nemoguard-8b-topic-control | True | True | True | False | False | 500 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| nvidia/llama-3.1-nemotron-51b-instruct | True | True | True | False | False | 404 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| nvidia/llama-3.1-nemotron-70b-instruct | True | True | True | False | False | 404 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| nvidia/llama-3.1-nemotron-safety-guard-8b-v3 | True | True | True | True | True | 200 | True | 5/7 | PRIMARY_CANDIDATE |
| nvidia/llama-3.1-nemotron-ultra-253b-v1 | True | True | True | False | False | 404 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1 | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| nvidia/llama-3.2-nv-embedqa-1b-v1 | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| nvidia/llama-nemotron-embed-vl-1b-v2 | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| nvidia/llama3-chatqa-1.5-70b | True | True | True | False | False | 404 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| nvidia/mistral-nemo-minitron-8b-8k-instruct | True | True | True | False | False | 404 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| nvidia/nemotron-3-embed-1b | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| nvidia/nemotron-3-nano-30b-a3b | True | True | True | True | True | 200 | True | 5/7 | PRIMARY_CANDIDATE |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | True | True | True | True | True | 200 | True | 5/7 | PRIMARY_CANDIDATE |
| nvidia/nemotron-3-super-120b-a12b | True | True | True | True | True | 200 | True | 5/7 | PRIMARY_CANDIDATE |
| nvidia/nemotron-3-ultra-550b-a55b | True | True | True | True | True | 200 | True | 5/7 | PRIMARY_CANDIDATE |
| nvidia/nemotron-3.5-content-safety | True | True | True | True | True | 200 | True | 5/7 | PRIMARY_CANDIDATE |
| nvidia/nemotron-3.5-lightning-30b-a3b | True | True | True | False | False | 404 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| nvidia/nemotron-4-340b-instruct | True | True | True | False | False | 404 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| nvidia/nemotron-4-340b-reward | True | True | True | False | False | 404 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| nvidia/nemotron-nano-3-30b-a3b | True | True | True | False | False | 404 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| nvidia/nemotron-parse | True | True | True | False | False | 400 | True | 4/7 | ACCOUNT_NOT_ENTITLED |
| nvidia/neva-22b | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| nvidia/nv-embedqa-mistral-7b-v2 | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| nvidia/nvclip | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| nvidia/riva-translate-4b-instruct | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| nvidia/riva-translate-4b-instruct-v1.1 | True | True | True | True | True | 200 | False | 3/7 | SCREENED_OUT_REQUIRED |
| nvidia/riva-translate-4b-instruct-v2 | True | True | True | True | True | 200 | False | 3/7 | SCREENED_OUT_REQUIRED |
| nvidia/vila | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| openai/gpt-oss-120b | True | True | True | True | True | 200 | False | 5/7 | SCREENED_OUT_REQUIRED |
| openai/gpt-oss-20b | True | True | True | True | True | 200 | False | 5/7 | SCREENED_OUT_REQUIRED |
| poolside/laguna-xs-2.1 | True | True | True | True | True | 200 | False | 3/7 | SCREENED_OUT_REQUIRED |
| snowflake/arctic-embed-l | True | True | True | False | False | 404 | False | 2/7 | SCREENED_OUT_REQUIRED |
| writer/palmyra-creative-122b | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| writer/palmyra-fin-70b-32k | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| writer/palmyra-med-70b | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| writer/palmyra-med-70b-32k | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |
| zyphra/zamba2-7b-instruct | True | True | True | False | False | 404 | False | 4/7 | SCREENED_OUT_REQUIRED |

## Screening Criteria Applied (Section 7)

### Required (all must pass)
1. **General-purpose LLM** or high language generation capability (not translation-only, speech, vision-first, embedding, reranker, image generation)
2. **Chinese support** (assumed for general LLMs)
3. **Instruction following** capability (general LLMs)
4. **Long-form text** handling (general LLMs)
5. **NVIDIA hosted endpoint** invocable (owned_by indicates NVIDIA/Meta/MiniMax)
6. **No NTPE architecture change** required (OpenAI-compatible chat/completions)

### Preferred (scored 0-7)
1. **≥32K context window**
2. **Multilingual** capability
3. **Strong language generation**
4. **Long-context capability** (≥16K)
5. **NVIDIA Free Endpoint** availability
6. **Stable provider response metadata** (NVCF tracking)
7. **Literary/narrative generation** suitability

## Candidate Classifications

### PRIMARY_CANDIDATE (preferred_score ≥ 5, passes all required)

#### minimaxai/minimax-m3
- **Catalog Owner**: minimaxai
- **Context Window**: None
- **Preferred Score**: 5/7
- **Smoke Test**: HTTP 200 (298ms)
- **NVCF Tracking**: e43f63d0-f751-4cbc-a60f-b207832c908d

#### nvidia/llama-3.1-nemoguard-8b-content-safety
- **Catalog Owner**: nvidia
- **Context Window**: None
- **Preferred Score**: 5/7
- **Smoke Test**: HTTP 200 (570ms)
- **NVCF Tracking**: c3d45781-87f2-4656-899b-a988b8605437

#### nvidia/llama-3.1-nemotron-safety-guard-8b-v3
- **Catalog Owner**: nvidia
- **Context Window**: None
- **Preferred Score**: 5/7
- **Smoke Test**: HTTP 200 (746ms)
- **NVCF Tracking**: d269b35e-9636-4e32-b278-c5c688123968

#### nvidia/nemotron-3-nano-30b-a3b
- **Catalog Owner**: nvidia
- **Context Window**: None
- **Preferred Score**: 5/7
- **Smoke Test**: HTTP 200 (453ms)
- **NVCF Tracking**: f8a2e997-6111-42d7-852b-10f38d38a705

#### nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
- **Catalog Owner**: nvidia
- **Context Window**: None
- **Preferred Score**: 5/7
- **Smoke Test**: HTTP 200 (1715ms)
- **NVCF Tracking**: 5ef7adfc-6222-497f-b7e1-f042d6c6a346

#### nvidia/nemotron-3-super-120b-a12b
- **Catalog Owner**: nvidia
- **Context Window**: None
- **Preferred Score**: 5/7
- **Smoke Test**: HTTP 200 (13264ms)
- **NVCF Tracking**: 8bf58fa9-39f7-4108-8af4-0a8e8f1b8b8b

#### nvidia/nemotron-3-ultra-550b-a55b
- **Catalog Owner**: nvidia
- **Context Window**: None
- **Preferred Score**: 5/7
- **Smoke Test**: HTTP 200 (19272ms)
- **NVCF Tracking**: 34e9c992-45c4-4df3-98d4-73d71a7d3863

#### nvidia/nemotron-3.5-content-safety
- **Catalog Owner**: nvidia
- **Context Window**: None
- **Preferred Score**: 5/7
- **Smoke Test**: HTTP 200 (502ms)
- **NVCF Tracking**: 1a278ba6-d39c-4819-9298-0d9a2d5203d1

### SECONDARY_CANDIDATE (preferred_score 3-4, passes all required)

### CANDIDATE (preferred_score < 3, passes all required)

### SCREENED_OUT_REQUIRED (fails one or more required criteria)

#### deepseek-ai/DeepSeek-V4-Pro-0813
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### deepseek-ai/DeepSeek-V4-Flash-0731
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### google/gemma-4-31b
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### 01-ai/yi-large
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### adept/fuyu-8b
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### ai21labs/jamba-1.5-large-instruct
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### aisingapore/sea-lion-7b-instruct
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### bigcode/starcoder2-15b
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### databricks/dbrx-instruct
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### deepseek-ai/deepseek-coder-6.7b-instruct
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### deepseek-ai/deepseek-v4-flash-0731
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### deepseek-ai/deepseek-v4-pro-0813
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### google/codegemma-1.1-7b
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### google/codegemma-7b
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### google/deplot
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### google/diffusiongemma-26b-a4b-it
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### google/gemma-2b
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### google/gemma-3-12b-it
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### google/gemma-3-4b-it
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### google/gemma-4-31b-it
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### google/recurrentgemma-2b
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### ibm/granite-3.0-3b-a800m-instruct
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### ibm/granite-3.0-8b-instruct
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### ibm/granite-34b-code-instruct
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### ibm/granite-8b-code-instruct
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### meta/llama-3.2-11b-vision-instruct
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### meta/llama-3.2-90b-vision-instruct
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### meta/muse-glimmer-30b
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### microsoft/kosmos-2
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### microsoft/phi-3-vision-128k-instruct
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### microsoft/phi-3.5-moe-instruct
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### mistralai/codestral-22b-instruct-v0.1
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### mistralai/mistral-7b-instruct-v0.3
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### mistralai/mistral-large
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### mistralai/mistral-large-2-instruct
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### mistralai/mistral-nemotron
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### mistralai/mixtral-8x22b-v0.1
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### moonshotai/kimi-k2.6
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### moonshotai/kimi-k3
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nv-mistralai/mistral-nemo-12b-instruct
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/ai-synthetic-video-detector
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/cosmos-reason2-8b
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/embed-qa-4
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/ising-calibration-1.5-31b
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/llama-3.2-nv-embedqa-1b-v1
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/llama-nemotron-embed-vl-1b-v2
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/nemotron-3-embed-1b
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/neva-22b
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/nv-embedqa-mistral-7b-v2
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/nvclip
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/riva-translate-4b-instruct
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/riva-translate-4b-instruct-v1.1
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/riva-translate-4b-instruct-v2
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### nvidia/vila
- **General LLM**: False
- **NVIDIA Hosted**: True
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### openai/gpt-oss-120b
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### openai/gpt-oss-20b
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### poolside/laguna-xs-2.1
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### snowflake/arctic-embed-l
- **General LLM**: False
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### writer/palmyra-creative-122b
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### writer/palmyra-fin-70b-32k
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### writer/palmyra-med-70b
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### writer/palmyra-med-70b-32k
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

#### zyphra/zamba2-7b-instruct
- **General LLM**: True
- **NVIDIA Hosted**: False
- **Reason**: Specialized model (translation/speech/vision/embedding/image-gen) or not NVIDIA-hosted

### CATALOG_UNAVAILABLE / ENDPOINT_UNAVAILABLE / ACCOUNT_NOT_ENTITLED / INVOCATION_FAILED

#### ACCOUNT_NOT_ENTITLED
- meta/codellama-70b: HTTP 404 - HTTP 404: {"status":404,"title":"Not Found","detail":"Function 'f6b06895-d073-4714-8bb2-26c09e9f6597': Not found for account 'e2eVxHJe7CNlNT6nkM9SbJ-FDUTkjIyWkvDmYypTYs4'"}
- meta/llama-guard-4-12b: HTTP 400 - HTTP 400: {"object":"error","message":"Conversation roles must alternate user/assistant/user/assistant/...","type":"BadRequestError","param":null,"code":400}
- meta/llama2-70b: HTTP 404 - HTTP 404: {"status":404,"title":"Not Found","detail":"Function '2fddadfb-7e76-4c8a-9b82-f7d3fab94471': Not found for account 'e2eVxHJe7CNlNT6nkM9SbJ-FDUTkjIyWkvDmYypTYs4'"}
- nvidia/llama-3.1-nemoguard-8b-topic-control: HTTP 500 - HTTP 500: {"error":"Error during inference of request chat-50f33d67288a48e6a3509af0a9ef8d9a -- Encountered an error in forwardAsync function: [TensorRT-LLM][ERROR] CUDA runtime error in cudaMemcpyAsync(dst, src
- nvidia/llama-3.1-nemotron-51b-instruct: HTTP 404 - HTTP 404: {"status":404,"title":"Not Found","detail":"Function '5beba52c-65a9-4f46-8cd9-656689a1b205': Not found for account 'e2eVxHJe7CNlNT6nkM9SbJ-FDUTkjIyWkvDmYypTYs4'"}
- nvidia/llama-3.1-nemotron-70b-instruct: HTTP 404 - HTTP 404: {"status":404,"title":"Not Found","detail":"Function '9b96341b-9791-4db9-a00d-4e43aa192a39': Not found for account 'e2eVxHJe7CNlNT6nkM9SbJ-FDUTkjIyWkvDmYypTYs4'"}
- nvidia/llama-3.1-nemotron-ultra-253b-v1: HTTP 404 - HTTP 404: {"status":404,"title":"Not Found","detail":"Function '84bf12ff-edbd-4435-baea-0fa6a7453d2e': Not found for account 'e2eVxHJe7CNlNT6nkM9SbJ-FDUTkjIyWkvDmYypTYs4'"}
- nvidia/llama3-chatqa-1.5-70b: HTTP 404 - HTTP 404: {"status":404,"title":"Not Found","detail":"Function '46594287-38b9-481c-a37f-baa02f2d3ba1': Not found for account 'e2eVxHJe7CNlNT6nkM9SbJ-FDUTkjIyWkvDmYypTYs4'"}
- nvidia/mistral-nemo-minitron-8b-8k-instruct: HTTP 404 - HTTP 404: {"status":404,"title":"Not Found","detail":"Function '5aa06dd2-0a02-4a5d-be4c-bf88e956965d': Not found for account 'e2eVxHJe7CNlNT6nkM9SbJ-FDUTkjIyWkvDmYypTYs4'"}
- nvidia/nemotron-3.5-lightning-30b-a3b: HTTP 404 - HTTP 404: 
- nvidia/nemotron-4-340b-instruct: HTTP 404 - HTTP 404: {"status":404,"title":"Not Found","detail":"Function 'b0fcd392-e905-4ab4-8eb9-aeae95c30b37': Not found for account 'e2eVxHJe7CNlNT6nkM9SbJ-FDUTkjIyWkvDmYypTYs4'"}
- nvidia/nemotron-4-340b-reward: HTTP 404 - HTTP 404: {"status":404,"title":"Not Found","detail":"Function 'c53ee0e9-bad9-4e09-b365-52c9d6b71254': Not found for account 'e2eVxHJe7CNlNT6nkM9SbJ-FDUTkjIyWkvDmYypTYs4'"}
- nvidia/nemotron-nano-3-30b-a3b: HTTP 404 - HTTP 404: {"error":{"message":"Model not found","type":"Not Found","code":404}}
- nvidia/nemotron-parse: HTTP 400 - HTTP 400: {"object":"error","message":"Expected exactly one message. Expected exactly one message.","type":"BadRequestError","param":null,"code":400}

## Official Catalog Evidence (Sample)

Total models in catalog: 83

Sample entries (first 20):
- 01-ai/yi-large: owned_by=01-ai, created=735790403
- adept/fuyu-8b: owned_by=adept, created=735790403
- ai21labs/jamba-1.5-large-instruct: owned_by=ai21labs, created=735790403
- aisingapore/sea-lion-7b-instruct: owned_by=aisingapore, created=735790403
- bigcode/starcoder2-15b: owned_by=bigcode, created=735790403
- databricks/dbrx-instruct: owned_by=databricks, created=735790403
- deepseek-ai/deepseek-coder-6.7b-instruct: owned_by=deepseek-ai, created=735790403
- deepseek-ai/deepseek-v4-flash-0731: owned_by=deepseek-ai, created=735790403
- deepseek-ai/deepseek-v4-pro-0813: owned_by=deepseek-ai, created=735790403
- google/codegemma-1.1-7b: owned_by=google, created=735790403
- google/codegemma-7b: owned_by=google, created=735790403
- google/deplot: owned_by=google, created=735790403
- google/diffusiongemma-26b-a4b-it: owned_by=google, created=735790403
- google/gemma-2b: owned_by=google, created=735790403
- google/gemma-3-12b-it: owned_by=google, created=735790403
- google/gemma-3-4b-it: owned_by=google, created=735790403
- google/gemma-4-31b-it: owned_by=google, created=735790403
- google/recurrentgemma-2b: owned_by=google, created=735790403
- ibm/granite-3.0-3b-a800m-instruct: owned_by=ibm, created=735790403
- ibm/granite-3.0-8b-instruct: owned_by=ibm, created=735790403

... and 63 more models

## Limitations
- Token measurement uses character-based estimation
- Screening criteria applied heuristically based on model ID patterns
- Chinese support assumed for general LLMs (not verified per-model)
- Single smoke test per model (not repeated for stability)
- No direct account entitlement API available
- Free Endpoint availability inferred, not verified per-model

## Compliance
- ✅ No credential leakage (only credential_source recorded)
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
- ✅ Production model (M1) unchanged

## Next Phase
Proceed to **Phase C: Provider Smoke** with PRIMARY_CANDIDATE and SECONDARY_CANDIDATE models for controlled repeated observations.
