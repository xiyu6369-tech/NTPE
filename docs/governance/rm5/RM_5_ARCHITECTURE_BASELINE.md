# RM-5 Architecture Baseline

**Baseline**: RM-4 Freeze  
**Version**: RM-5.0  
**Status**: Architecture Governance  
**Created**: 2026-07-31  
**Purpose**: Reference architecture for all RM-5.x stages — defines pipeline boundaries, data flows, and frozen constraints.

---

## 1. Current Architecture

The RM-4 baseline provides the following top-level architectural layers:

### 1.1 `core/` — Translation Core

The production runtime resides here. All translation logic, chunk processing, prompt construction, glossary enforcement, character memory, and quality validation live under `core/`.

| Module | Responsibility |
|---|---|
| `core/translator.py` | Translation Entry: file ingestion → chunk splitting → per-chunk translate → output assembly |
| `core/chunker.py` | `ChunkEngine`: scene/paragraph-first segmentation with `ChunkOptions` (target_size=1100, hard_limit=1500) |
| `core/prompt_engine.py` | `PromptEngine`: builds translation prompts with novel profile, glossary, context, and absolute rules |
| `core/character_memory_engine.py` | Character Memory Engine v1.0: merges multi-volume character candidates, applies overrides, exports `character_memory.json` & CSV |
| `core/glossary_builder.py` | Glossary Builder v1.1.1: merges multi-volume glossary auto-candidates, resolves character aliases, exports `glossary.json` & `character_alias_index.json` |
| `core/glossary.py` | `Glossary`: runtime glossary loader with term enforcement and output fix |
| `core/rules.py` | Post-processing rules: glossary enforcement, forbidden-AI-text guard, hallucination patterns, bad-name correction |
| `core/formatter.py` | `FormatEngine`: paragraph normalization, quote normalization, source-structure restoration |
| `core/chunker.py` | `split_chunks()` legacy interface → delegates to `ChunkEngine` |
| `core/validator.py` | `Validator`: post-translation validation — empty check, forbidden phrases, bad names, Korean residue, length guard, repetition, inference markers |
| `core/scheduler.py` | `RPMScheduler`: rolling 60-second window rate limiter for API calls |
| `core/config.py` | Configuration management |
| `core/exceptions.py` | Centralized exception types for the pipeline |

### 1.2 `engine/` — Provider Layer

| Module | Responsibility |
|---|---|
| `engine/nvidia.py` | `NvidiaEngine`: NVIDIA NIM API client (llama-3.3-70b-instruct), Bearer token auth, POST to `/v1/chat/completions`, temperature=0.1, max_tokens=4096 |

### 1.3 `tools/` — Operational Tooling

| Directory | Role |
|---|---|
| `tools/legacy_pipeline_launchers/` | Historical pipeline launch scripts |
| `tools/maintenance/` | Maintenance utilities (cleanup, audit) |
| `tools/one_shots/` | One-shot stage application scripts |
| `tools/provider_controls/` | Provider authorization, invocation, benchmarking tools |
| `tools/provider_utils/` | Provider setup/verification utilities |

### 1.4 `lts/` — Long-Term Support

| Module | Responsibility |
|---|---|
| `lts/batch_translation_runtime.py` | Batch translation execution |
| `lts/batch_runtime_monitor.py` | Batch monitoring |
| `lts/rc_freeze.py` | Release candidate freeze |
| `lts/release_candidate.py` | RC management |
| `lts/stable_finalization.py` | Stable release finalization |
| `lts/runtime_freeze.py` | Runtime freeze |
| `lts/regression_validation.py` | Regression test validation |
| `lts/quality_validation.py` | Quality validation |
| `lts/performance_validation.py` | Performance validation |
| `lts/compatibility_validation.py` | Compatibility validation |
| `lts/final_validation.py` | Final validation |

### 1.5 `archive/` — Historical Artifacts

| Directory | Contents |
|---|---|
| `archive/data_artifacts/` | Historical data artifacts |
| `archive/historical/` | Analysis, audits, memory, quality corpus, reports, sessions |
| `archive/legacy/` | Legacy data and examples |
| `archive/legacy_config/` | Archived prompt packages and rules |
| `archive/legacy_tools/` | Deprecated tools |
| `archive/legacy_ui_safe/` | Archived GUI code |
| `archive/lts_duplicates/` | Duplicate LTS snapshots |
| `archive/one_shot_creation/` | One-shot script snapshots |
| `archive/release_artifacts/` | Release packages (full, increment, manifests, source, wheel) |
| `archive/stage_tests/` | Historical stage tests |
| `archive/translation_history/` | Translation cache history |

### 1.6 `tests/` — Test Suite

Over 100 test directories covering unit tests, integration tests, literary tests, contract tests, characterization tests, stage-level tests (foundation, beta), validation tests, LTS RC tests, production tests, and smoke tests.

### 1.7 `docs/` — Documentation

| Directory | Role |
|---|---|
| `docs/governance/` | Repository governance, migration records, audits |
| `docs/stages/` | Stage-by-stage implementation docs |
| `docs/releases/` | Release milestone reports |
| `docs/governance/rm5/` | **RM-5 Architecture Baseline (this directory)** |
---

## 2. Translation Runtime

The current production translation runtime follows this flow:

### 2.1 Translation Entry
```
launcher_translate.py / ntpe_translate_txt.py / ntpe_translate_batch.py
  → core/translator.py: translate_file()
```

Entry points invoke `translate_file()` which orchestrates the full per-file pipeline.

### 2.2 Chunk Flow
```
source text (*.txt)
  → read_text_auto()          # auto-detect encoding
  → ChunkEngine.split()       # scene/paragraph segmentation (target=1100 chars)
  → chunks: List[str]
```

### 2.3 Context Flow
```
for each chunk:
  context = last_translated_part[-context_size:]    # default 650 chars
  → PromptEngine.build_translate_prompt(text, context, glossary)
```

Context is a sliding window of the most recently translated output — no external context management, no character state injection.

### 2.4 Retry
```
for attempt in range(max_retry):       # default 4
  NvidiaEngine.translate(prompt)       # API call
    → normalize_output()               # OpenCC s2twp + glossary enforcement + post-processing
    → validate_translation()           # forbidden phrases, residue, length, hallucination check
    → on pass: return candidate
    → on fail: wait (base=8s * attempt), retry
```

### 2.5 Resume
```
progress.json  → per-file { filename: chunks_completed }
  → skip already-translated chunks
  → append new translations to existing output
```

### 2.6 Validation
```
validator.validate(source, candidate)
  → empty check
  → forbidden AI refusal phrases
  → bad name patterns (正太義, 卡爾, etc.)
  → Korean residue (≥ 10 chars)
  → length check (≥ max(80, 35% of source length))
  → duplicate paragraph detection
  → hallucination markers
  → glossary term coverage
```
---

## 3. Quality Pipeline — Data Flow

```
[Source Text]                    [Glossary Data]           [Character Memory Data]
     │                                │                            │
     ▼                                ▼                            ▼
┌──────────┐                   ┌───────────┐            ┌──────────────────┐
│ Chunking │                   │ Glossary  │            │ Character Memory │
│ Engine   │                   │ Builder   │            │ Engine v1.0      │
└────┬─────┘                   └─────┬─────┘            └────────┬─────────┘
     │                              │                             │
     │                    ┌─────────┼──────────┐                 │
     │                    ▼         ▼          ▼                 │
     │              glossary.json  glossary.csv  glossary_report │
     │                    │         │          │                 │
     │                    └────┬────┘          │                 │
     │                         │               │                 │
     ▼                         ▼               │                 ▼
┌──────────────────────────────────────────────┼──────────────────────┐
│               Prompt Engine                  │  character_memory.json│
│  (novel profile + absolute rules + context)  │  character_memory.csv  │
└──────────────────────┬───────────────────────┴──────────────────────┘
                       │
                       ▼
           ┌─────────────────┐
           │   NvidiaEngine  │
           │   (API call)    │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │   Validator     │  ← Glossary.check_required_terms()
           │   (rules.py)    │  ← Post-process (fixes + formatting)
           └────────┬────────┘
                    │
                    ▼
           [Final Output]

Key observations:
- Character Memory Engine extracts and merges character data, but is **NOT integrated** into the runtime prompt at chunk translation time (no character-state injection into context)
- Glossary is loaded from `data/glossary.txt` at **runtime** (text format), NOT from the structured `memory/glossary.json`
- Quality evaluation is purely rules-based (no ML, no semantic scoring, no readability metrics)

---

## 4. Provider Pipeline

### 4.1 NVIDIA Provider Flow

```
config/config.json         engine/nvidia.py
     │                         │
     ▼                         ▼
  api_key ──────────► NvidiaEngine(config)
  model               │
  api_url             ├─ .translate(prompt)
  timeout             │   → .chat(prompt)
                      │     → POST https://integrate.api.nvidia.com/v1/chat/completions
                      │         headers: Authorization: Bearer {key}
                      │         body: {model, messages, temperature:0.1, top_p:0.7, max_tokens:4096}
                      │     → response: data["choices"][0]["message"]["content"]
                      │
                      ▼
                  raw translated text
```

### 4.2 Authorization

- API key stored in `config/config.json` (key: `api_key`)
- Validated at engine initialization: raises `RuntimeError` if missing
- No OAuth, no JWT refresh, no key rotation, no credential encryption

### 4.3 Retry

- Implemented in `core/translator.py::translate_chunk()`
- Max retry: `config.get("max_retry", 4)`
- Backoff: `min(retry_wait_base * (attempt + 1), 40)` seconds
- Retry on: any exception (API error, validation fail)

### 4.4 Benchmark

- Manual tools under `tools/provider_controls/`:
  - `ntpe_provider_benchmark_session.py`
  - `ntpe_provider_audit.py`
  - `ntpe_provider_verify.py`
  - `ntpe_provider_setup.py`
- Not integrated into runtime.

### 4.5 Validation

- Post-translation validation in `core/validator.py`
- Pre-translation: API key check at engine init only
- No provider-level quality canary (output passes validation but is not scored)

---

## 5. Responsibility Boundary

| Pipeline | Owner | Boundaries |
|---|---|---|
| **Translation Pipeline** | `core/translator.py` | File → chunks → translate → validate → output |
| **Context Pipeline** | `core/translator.py` (sliding window) | Last 650 chars of previous translation |
| **Prompt Pipeline** | `core/prompt_engine.py` | Template + glossary + context + novel profile |
| **Glossary Pipeline** | `core/` (glossary.py, glossary_builder.py) | Static term enforcement at runtime + structured build at analysis time |
| **Character Memory Pipeline** | `core/character_memory_engine.py` | Offline character database — **NOT runtime-integrated** |
| **Quality Evaluation** | `core/validator.py` + `core/rules.py` | Rule-based post-translation validation |
| **Provider Pipeline** | `engine/nvidia.py` | API bridge: auth → request → response extraction |
| **Runtime Pipeline** | `core/scheduler.py` + `core/translator.py:translate_file()` | RPM enforcement, retry logic, resume from progress |
| **LTS Runtime** | `lts/*.py` | Batch execution, monitoring, freeze, validation |

**Frozen State Note:**  
All production Python under `core/`, `lts/`, `tools/`, and `tests/` is frozen per RM-4.  
No logic modification is allowed during RM-5.0.