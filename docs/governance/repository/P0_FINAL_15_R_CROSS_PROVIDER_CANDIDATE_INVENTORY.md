# P0-FINAL-15-R — Cross-Provider Candidate Inventory

## Phase R-B: Non-NVIDIA Candidate Discovery

### Baseline
- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Timestamp**: 2026-08-29T06:50:57.588802Z

### Provider Coverage

| Provider | Models |
|----------|--------|
| Anthropic | 3 |
| Cohere | 2 |
| DeepSeek | 2 |
| Google | 3 |
| Mistral AI | 2 |
| OpenAI | 3 |
| Z.ai | 1 |

### Mandatory Criteria (Section 11)

| Criterion | Requirement |
|-----------|-------------|
| General-purpose LLM | Not specialized (translation-only, embedding, safety, code-only) |
| Chinese Support | Explicit Mandarin/Chinese capability |
| Multilingual | Supports multiple languages |
| Instruction Following | Chat completion / instruction-tuned |
| Context Window | ≥ 8K tokens |
| API Available | Production API endpoint exists |
| Credential Required | Standard API key auth |

### All Candidates

| Model ID | Provider | General LLM | Chinese | Multilingual | Instruction | Context | Recent | Prod Ready | API Type |
|----------|----------|-------------|---------|--------------|-------------|---------|--------|------------|----------|
| gpt-4o | OpenAI | True | True | True | True | 128000 | True | True | openai-compatible |
| gpt-4o-mini | OpenAI | True | True | True | True | 128000 | True | True | openai-compatible |
| gpt-4-turbo | OpenAI | True | True | True | True | 128000 | True | True | openai-compatible |
| claude-3-5-sonnet-20241022 | Anthropic | True | True | True | True | 200000 | True | True | anthropic |
| claude-3-5-haiku-20241022 | Anthropic | True | True | True | True | 200000 | True | True | anthropic |
| claude-3-opus-20240229 | Anthropic | True | True | True | True | 200000 | True | True | anthropic |
| gemini-1.5-pro | Google | True | True | True | True | 2000000 | True | True | google |
| gemini-1.5-flash | Google | True | True | True | True | 1000000 | True | True | google |
| gemini-1.0-pro | Google | True | True | True | True | 32768 | False | True | google |
| command-r-plus | Cohere | True | True | True | True | 128000 | True | True | cohere |
| command-r | Cohere | True | True | True | True | 128000 | True | True | cohere |
| mistral-large-latest | Mistral AI | True | True | True | True | 32768 | True | True | openai-compatible |
| mistral-medium-latest | Mistral AI | True | True | True | True | 32768 | True | True | openai-compatible |
| deepseek-chat | DeepSeek | True | True | True | True | 64000 | True | True | openai-compatible |
| deepseek-coder | DeepSeek | False | True | True | True | 16384 | True | True | openai-compatible |
| glm-4 | Z.ai | True | True | True | True | 128000 | True | True | openai-compatible |

### Qualified Candidates (15)

Pass all mandatory criteria.

#### gpt-4o (OpenAI)
- **Context Window**: 128000
- **Max Output**: 16384
- **API Type**: openai-compatible
- **Credential**: OPENAI_API_KEY
- **Notes**: Flagship model, strong multilingual, excellent instruction following

#### gpt-4o-mini (OpenAI)
- **Context Window**: 128000
- **Max Output**: 16384
- **API Type**: openai-compatible
- **Credential**: OPENAI_API_KEY
- **Notes**: Cost-efficient variant, strong capabilities

#### gpt-4-turbo (OpenAI)
- **Context Window**: 128000
- **Max Output**: 4096
- **API Type**: openai-compatible
- **Credential**: OPENAI_API_KEY
- **Notes**: Previous generation flagship

#### claude-3-5-sonnet-20241022 (Anthropic)
- **Context Window**: 200000
- **Max Output**: 8192
- **API Type**: anthropic
- **Credential**: ANTHROPIC_API_KEY
- **Notes**: Strong reasoning, excellent multilingual, large context

#### claude-3-5-haiku-20241022 (Anthropic)
- **Context Window**: 200000
- **Max Output**: 8192
- **API Type**: anthropic
- **Credential**: ANTHROPIC_API_KEY
- **Notes**: Fast, cost-efficient variant

#### claude-3-opus-20240229 (Anthropic)
- **Context Window**: 200000
- **Max Output**: 4096
- **API Type**: anthropic
- **Credential**: ANTHROPIC_API_KEY
- **Notes**: Previous flagship, very strong reasoning

#### gemini-1.5-pro (Google)
- **Context Window**: 2000000
- **Max Output**: 8192
- **API Type**: google
- **Credential**: GOOGLE_API_KEY
- **Notes**: Massive context window, strong multilingual

#### gemini-1.5-flash (Google)
- **Context Window**: 1000000
- **Max Output**: 8192
- **API Type**: google
- **Credential**: GOOGLE_API_KEY
- **Notes**: Fast, cost-efficient, large context

#### gemini-1.0-pro (Google)
- **Context Window**: 32768
- **Max Output**: 2048
- **API Type**: google
- **Credential**: GOOGLE_API_KEY
- **Notes**: Previous generation

#### command-r-plus (Cohere)
- **Context Window**: 128000
- **Max Output**: 4096
- **API Type**: cohere
- **Credential**: COHERE_API_KEY
- **Notes**: Strong RAG capabilities, multilingual

#### command-r (Cohere)
- **Context Window**: 128000
- **Max Output**: 4096
- **API Type**: cohere
- **Credential**: COHERE_API_KEY
- **Notes**: Efficient variant

#### mistral-large-latest (Mistral AI)
- **Context Window**: 32768
- **Max Output**: 8192
- **API Type**: openai-compatible
- **Credential**: MISTRAL_API_KEY
- **Notes**: Flagship model, strong multilingual

#### mistral-medium-latest (Mistral AI)
- **Context Window**: 32768
- **Max Output**: 8192
- **API Type**: openai-compatible
- **Credential**: MISTRAL_API_KEY
- **Notes**: Balanced performance

#### deepseek-chat (DeepSeek)
- **Context Window**: 64000
- **Max Output**: 8192
- **API Type**: openai-compatible
- **Credential**: DEEPSEEK_API_KEY
- **Notes**: Strong Chinese capability, cost-effective

#### glm-4 (Z.ai)
- **Context Window**: 128000
- **Max Output**: 8192
- **API Type**: openai-compatible
- **Credential**: ZAI_API_KEY
- **Notes**: Strong Chinese, from Zhipu AI

### Priority Candidates (15)

Top 3 per provider (by context window, recency, production readiness).
- **gpt-4o** (OpenAI) — ctx: 128000, recent: True
- **gpt-4o-mini** (OpenAI) — ctx: 128000, recent: True
- **gpt-4-turbo** (OpenAI) — ctx: 128000, recent: True
- **claude-3-5-sonnet-20241022** (Anthropic) — ctx: 200000, recent: True
- **claude-3-5-haiku-20241022** (Anthropic) — ctx: 200000, recent: True
- **claude-3-opus-20240229** (Anthropic) — ctx: 200000, recent: True
- **gemini-1.5-pro** (Google) — ctx: 2000000, recent: True
- **gemini-1.5-flash** (Google) — ctx: 1000000, recent: True
- **gemini-1.0-pro** (Google) — ctx: 32768, recent: False
- **command-r-plus** (Cohere) — ctx: 128000, recent: True
- **command-r** (Cohere) — ctx: 128000, recent: True
- **mistral-large-latest** (Mistral AI) — ctx: 32768, recent: True
- **mistral-medium-latest** (Mistral AI) — ctx: 32768, recent: True
- **deepseek-chat** (DeepSeek) — ctx: 64000, recent: True
- **glm-4** (Z.ai) — ctx: 128000, recent: True

## Limitations
- Candidate list based on publicly known models as of 2024
- API availability not verified at runtime (requires credentials)
- Capability claims based on provider documentation, not independent testing
- Cost feasibility not evaluated
- Regional availability (China/Taiwan) not verified
- No actual API calls performed in this phase

## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ No actual API calls performed
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved

## Next Phase
Proceed to **Candidate Evaluation** (smoke, translation, quality, glossary, context, reliability) for priority candidates.
