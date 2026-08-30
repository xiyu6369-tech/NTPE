# P0-FINAL-15-Q — NVIDIA Current Catalog Refresh

## Phase Q1: Current Catalog Verification

### Environment
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY (present: True)
- **Timestamp**: 2026-08-29T05:49:39.291461Z

### NVIDIA /v1/models Catalog Fetch
- **Fetch Status**: SUCCESS
- **HTTP Status**: 200
- **Models Count**: 83

### Model Detail Fetch Summary
- **Total Models**: 83
- **Successfully Fetched**: 83
- **Failed**: 0

## Comparison with P0-FINAL-15-P

| Metric | P0-FINAL-15-P | Current (Q) | Delta |
|--------|---------------|-------------|-------|
| Models in Catalog | 83 | 83 | 0 |

## Model Family Distribution
| Family | Count |
|--------|-------|
| Other | 18 |
| Nemotron | 17 |
| Llama | 10 |
| Gemma | 8 |
| Mistral | 8 |
| Granite | 4 |
| Palmyra | 4 |
| DeepSeek | 3 |
| RivaTranslate | 3 |
| Phi | 2 |
| GPT | 2 |
| Yi | 1 |
| Jamba | 1 |
| MiniMax | 1 |
| Zamba | 1 |

## Capability Summary (Inferred)

| Capability | Models | Percentage |
|------------|--------|------------|
| Chinese Support | 67 | 80.7% |
| Multilingual | 67 | 80.7% |
| Instruction Following | 54 | 65.1% |

## Model Details

| Model ID | Owner | Family | Context Window | Max Output | Chinese | Multilingual | Instruction Following | Description |
|----------|-------|--------|----------------|------------|---------|--------------|----------------------|-------------|
| 01-ai/yi-large | 01-ai | Yi | N/A | N/A | True | True | True | Yi family, owned by 01-ai |
| adept/fuyu-8b | adept | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by adept |
| ai21labs/jamba-1.5-large-instruct | ai21labs | Jamba | N/A | N/A | True | True | True | General-purpose LLM, owned by ai21labs |
| aisingapore/sea-lion-7b-instruct | aisingapore | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by aisingapore |
| bigcode/starcoder2-15b | bigcode | Other | N/A | N/A | False | False | True | Code generation model, owned by bigcode |
| databricks/dbrx-instruct | databricks | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by databricks |
| deepseek-ai/deepseek-coder-6.7b-instruct | deepseek-ai | DeepSeek | N/A | N/A | True | True | True | DeepSeek family, owned by deepseek-ai |
| deepseek-ai/deepseek-v4-flash-0731 | deepseek-ai | DeepSeek | N/A | N/A | True | True | True | DeepSeek family, owned by deepseek-ai |
| deepseek-ai/deepseek-v4-pro-0813 | deepseek-ai | DeepSeek | N/A | N/A | True | True | True | DeepSeek family, owned by deepseek-ai |
| google/codegemma-1.1-7b | google | Gemma | N/A | N/A | True | True | True | Gemma family, owned by google |
| google/codegemma-7b | google | Gemma | N/A | N/A | True | True | True | Gemma family, owned by google |
| google/deplot | google | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by google |
| google/diffusiongemma-26b-a4b-it | google | Gemma | N/A | N/A | True | True | True | Gemma family, owned by google |
| google/gemma-2b | google | Gemma | N/A | N/A | True | True | True | Gemma family, owned by google |
| google/gemma-3-12b-it | google | Gemma | N/A | N/A | True | True | True | Gemma family, owned by google |
| google/gemma-3-4b-it | google | Gemma | N/A | N/A | True | True | True | Gemma family, owned by google |
| google/gemma-4-31b-it | google | Gemma | N/A | N/A | True | True | True | Gemma family, owned by google |
| google/recurrentgemma-2b | google | Gemma | N/A | N/A | True | True | True | Gemma family, owned by google |
| ibm/granite-3.0-3b-a800m-instruct | ibm | Granite | N/A | N/A | True | True | True | General-purpose LLM, owned by ibm |
| ibm/granite-3.0-8b-instruct | ibm | Granite | N/A | N/A | True | True | True | General-purpose LLM, owned by ibm |
| ibm/granite-34b-code-instruct | ibm | Granite | N/A | N/A | True | True | True | Code generation model, owned by ibm |
| ibm/granite-8b-code-instruct | ibm | Granite | N/A | N/A | True | True | True | Code generation model, owned by ibm |
| meta/codellama-70b | meta | Llama | N/A | N/A | True | True | True | Llama family, owned by meta |
| meta/llama-3.2-11b-vision-instruct | meta | Llama | N/A | N/A | True | True | True | Llama family, owned by meta |
| meta/llama-3.2-90b-vision-instruct | meta | Llama | N/A | N/A | True | True | True | Llama family, owned by meta |
| meta/llama-guard-4-12b | meta | Llama | N/A | N/A | True | True | True | Llama family, owned by meta |
| meta/llama2-70b | meta | Llama | N/A | N/A | True | True | True | Llama family, owned by meta |
| meta/muse-glimmer-30b | meta | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by meta |
| microsoft/kosmos-2 | microsoft | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by microsoft |
| microsoft/phi-3-vision-128k-instruct | microsoft | Phi | N/A | N/A | True | True | True | Phi family, owned by microsoft |
| microsoft/phi-3.5-moe-instruct | microsoft | Phi | N/A | N/A | True | True | True | Phi family, owned by microsoft |
| minimaxai/minimax-m3 | minimaxai | MiniMax | N/A | N/A | True | True | True | MiniMax family, owned by minimaxai |
| mistralai/codestral-22b-instruct-v0.1 | mistralai | Mistral | N/A | N/A | True | True | True | Mistral/Mixtral family, owned by mistralai |
| mistralai/mistral-7b-instruct-v0.3 | mistralai | Mistral | N/A | N/A | True | True | True | Mistral/Mixtral family, owned by mistralai |
| mistralai/mistral-large | mistralai | Mistral | N/A | N/A | True | True | True | Mistral/Mixtral family, owned by mistralai |
| mistralai/mistral-large-2-instruct | mistralai | Mistral | N/A | N/A | True | True | True | Mistral/Mixtral family, owned by mistralai |
| mistralai/mistral-nemotron | mistralai | Nemotron | N/A | N/A | True | True | True | NVIDIA Nemotron family, owned by mistralai |
| mistralai/mixtral-8x22b-v0.1 | mistralai | Mistral | N/A | N/A | True | True | True | Mistral/Mixtral family, owned by mistralai |
| moonshotai/kimi-k2.6 | moonshotai | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by moonshotai |
| moonshotai/kimi-k3 | moonshotai | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by moonshotai |
| nv-mistralai/mistral-nemo-12b-instruct | nv-mistralai | Mistral | N/A | N/A | True | True | True | Mistral/Mixtral family, owned by nv-mistralai |
| nvidia/ai-synthetic-video-detector | nvidia | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by nvidia |
| nvidia/cosmos-reason2-8b | nvidia | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by nvidia |
| nvidia/embed-qa-4 | nvidia | Other | N/A | N/A | True | True | False | Embedding / retrieval model, owned by nvidia |
| nvidia/ising-calibration-1.5-31b | nvidia | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by nvidia |
| nvidia/llama-3.1-nemoguard-8b-content-safety | nvidia | Llama | N/A | N/A | True | True | False | Llama family, owned by nvidia |
| nvidia/llama-3.1-nemoguard-8b-topic-control | nvidia | Llama | N/A | N/A | True | True | False | Llama family, owned by nvidia |
| nvidia/llama-3.1-nemotron-51b-instruct | nvidia | Nemotron | N/A | N/A | True | True | True | NVIDIA Nemotron family, owned by nvidia |
| nvidia/llama-3.1-nemotron-70b-instruct | nvidia | Nemotron | N/A | N/A | True | True | True | NVIDIA Nemotron family, owned by nvidia |
| nvidia/llama-3.1-nemotron-safety-guard-8b-v3 | nvidia | Nemotron | N/A | N/A | True | True | False | NVIDIA Nemotron family, owned by nvidia |
| nvidia/llama-3.1-nemotron-ultra-253b-v1 | nvidia | Nemotron | N/A | N/A | True | True | True | NVIDIA Nemotron family, owned by nvidia |
| nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1 | nvidia | Llama | N/A | N/A | True | True | False | Llama family, owned by nvidia |
| nvidia/llama-3.2-nv-embedqa-1b-v1 | nvidia | Llama | N/A | N/A | True | True | False | Llama family, owned by nvidia |
| nvidia/llama-nemotron-embed-vl-1b-v2 | nvidia | Nemotron | N/A | N/A | True | True | False | NVIDIA Nemotron family, owned by nvidia |
| nvidia/llama3-chatqa-1.5-70b | nvidia | Llama | N/A | N/A | True | True | True | Llama family, owned by nvidia |
| nvidia/mistral-nemo-minitron-8b-8k-instruct | nvidia | Mistral | N/A | N/A | True | True | True | Mistral/Mixtral family, owned by nvidia |
| nvidia/nemotron-3-embed-1b | nvidia | Nemotron | N/A | N/A | True | True | False | NVIDIA Nemotron family, owned by nvidia |
| nvidia/nemotron-3-nano-30b-a3b | nvidia | Nemotron | N/A | N/A | True | True | True | NVIDIA Nemotron family, owned by nvidia |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | nvidia | Nemotron | N/A | N/A | True | True | True | NVIDIA Nemotron family, owned by nvidia |
| nvidia/nemotron-3-super-120b-a12b | nvidia | Nemotron | N/A | N/A | True | True | True | NVIDIA Nemotron family, owned by nvidia |
| nvidia/nemotron-3-ultra-550b-a55b | nvidia | Nemotron | N/A | N/A | True | True | True | NVIDIA Nemotron family, owned by nvidia |
| nvidia/nemotron-3.5-content-safety | nvidia | Nemotron | N/A | N/A | True | True | False | NVIDIA Nemotron family, owned by nvidia |
| nvidia/nemotron-3.5-lightning-30b-a3b | nvidia | Nemotron | N/A | N/A | True | True | True | NVIDIA Nemotron family, owned by nvidia |
| nvidia/nemotron-4-340b-instruct | nvidia | Nemotron | N/A | N/A | True | True | True | NVIDIA Nemotron family, owned by nvidia |
| nvidia/nemotron-4-340b-reward | nvidia | Nemotron | N/A | N/A | True | True | True | NVIDIA Nemotron family, owned by nvidia |
| nvidia/nemotron-nano-3-30b-a3b | nvidia | Nemotron | N/A | N/A | True | True | True | NVIDIA Nemotron family, owned by nvidia |
| nvidia/nemotron-parse | nvidia | Nemotron | N/A | N/A | True | True | True | NVIDIA Nemotron family, owned by nvidia |
| nvidia/neva-22b | nvidia | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by nvidia |
| nvidia/nv-embedqa-mistral-7b-v2 | nvidia | Mistral | N/A | N/A | True | True | False | Mistral/Mixtral family, owned by nvidia |
| nvidia/nvclip | nvidia | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by nvidia |
| nvidia/riva-translate-4b-instruct | nvidia | RivaTranslate | N/A | N/A | True | True | False | NVIDIA Riva Translation specialized model, owned by nvidia |
| nvidia/riva-translate-4b-instruct-v1.1 | nvidia | RivaTranslate | N/A | N/A | True | True | False | NVIDIA Riva Translation specialized model, owned by nvidia |
| nvidia/riva-translate-4b-instruct-v2 | nvidia | RivaTranslate | N/A | N/A | True | True | False | NVIDIA Riva Translation specialized model, owned by nvidia |
| nvidia/vila | nvidia | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by nvidia |
| openai/gpt-oss-120b | openai | GPT | N/A | N/A | True | True | True | General-purpose LLM, owned by openai |
| openai/gpt-oss-20b | openai | GPT | N/A | N/A | True | True | True | General-purpose LLM, owned by openai |
| poolside/laguna-xs-2.1 | poolside | Other | N/A | N/A | False | False | False | General-purpose LLM, owned by poolside |
| snowflake/arctic-embed-l | snowflake | Other | N/A | N/A | True | True | False | Embedding / retrieval model, owned by snowflake |
| writer/palmyra-creative-122b | writer | Palmyra | N/A | N/A | True | True | True | General-purpose LLM, owned by writer |
| writer/palmyra-fin-70b-32k | writer | Palmyra | N/A | N/A | True | True | True | General-purpose LLM, owned by writer |
| writer/palmyra-med-70b | writer | Palmyra | N/A | N/A | True | True | True | General-purpose LLM, owned by writer |
| writer/palmyra-med-70b-32k | writer | Palmyra | N/A | N/A | True | True | True | General-purpose LLM, owned by writer |
| zyphra/zamba2-7b-instruct | zyphra | Zamba | N/A | N/A | True | True | True | General-purpose LLM, owned by zyphra |

## Limitations
- Model details inferred from model ID patterns, not official documentation
- Chinese/multilingual/instruction-following capabilities inferred, not verified per-model
- Context window from API may not reflect actual usable context
- Single catalog fetch (not repeated for consistency)
- No official NVIDIA documentation on model capabilities used

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
Proceed to **Phase Q2: Candidate Admission Filter** using this refreshed catalog as the authoritative source.
