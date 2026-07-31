# RM-5.1 Pipeline Audit Report

## Pipeline Evidence Matrix

| Pipeline | Exists | Runtime Used | Production Used | Prompt Impact | Status |
|---|---|---|---|---|---|
| TXT Input | YES | YES | YES | NO | ACTIVE |
| EPUB Input | YES (book_intake) | PARTIAL | NO | NO | PARTIAL |
| Document Normalizer | YES (standalone) | NO | NO | NO | LEGACY |
| Document Analyzer | YES (standalone) | NO | NO | NO | LEGACY |
| Book Intake | YES | YES (tests/verif) | NO | NO | DEAD PATH |
| Book Preparation | YES | YES (tests/verif) | NO | NO | DEAD PATH |
| Book Segmentation | YES | YES (tests only) | NO | NO | DEAD PATH |
| Book Chunking | YES | YES (tests only) | NO | NO | DEAD PATH |
| Chunking (LTS) | YES | YES | YES | NO | ACTIVE |
| Context Builder (core/context) | YES | NO | NO | NO | DEAD PATH |
| Context Scene Memory | YES | PARTIAL (v7.2) | NO | PARTIAL | PARTIAL |
| Previous Chunk Context | YES | YES | YES | YES | ACTIVE |
| Narrative Context | YES (literary) | YES | YES | YES | ACTIVE |
| Character Context (literary) | YES (literary) | YES | YES | YES | ACTIVE |
| Character Memory V1 | YES | NO | NO | NO | LEGACY |
| Character Memory Engine | YES (standalone) | NO | NO | NO | LEGACY |
| Character Memory V2 | YES | PARTIAL (v7.2) | NO | PARTIAL | PARTIAL |
| Character Database | YES | NO | NO | NO | LEGACY |
| Character Resolver | YES | YES (glossary_builder) | NO | NO | PARTIAL |
| Glossary (core/glossary.py) | YES (v1) | NO | NO | NO | LEGACY |
| Glossary Builder | YES (standalone) | NO | NO | NO | LEGACY |
| Glossary (LTS) | YES (LTS lock) | YES | YES | YES | ACTIVE |
| Knowledge Base Builder | YES (standalone) | NO | NO | NO | LEGACY |
| Knowledge Runtime | YES | PARTIAL (optional) | NO | NO | PARTIAL |
| Prompt Engine (v1) | YES (core/prompt_engine.py) | NO | NO | NO | LEGACY |
| Prompt Builder (lit) | YES (literary/) | YES | YES | YES | ACTIVE |
| Prompt Compiler | YES | YES | YES | YES | ACTIVE |
| Prompt Intelligence | YES | YES | YES | PARTIAL | ACTIVE |
| Context Intelligence | YES | YES | YES | PARTIAL | ACTIVE |
| Translation Discipline | YES | YES | YES | YES | ACTIVE |
| Translation Engine | YES | YES | YES | NO | ACTIVE |
| Translation Runtime | YES | YES | YES | NO | ACTIVE |
| TXT Runtime | YES (LTS) | YES | YES | NO | ACTIVE |
| Batch Runtime | YES (LTS) | YES | YES | NO | ACTIVE |
| Production Runtime | YES | PARTIAL (optional) | NO | NO | PARTIAL |
| Translation Scheduler | YES | YES (gate modules) | NO | NO | DEAD PATH |
| Translation Orchestrator | YES | PARTIAL (SDK) | NO | NO | PARTIAL |
| LTR Recovery | YES | YES | YES | NO | ACTIVE |
| Chunk Cache V2 | YES | PARTIAL (v7.2) | NO | NO | PARTIAL |
| Literary Evaluation | YES (root) | YES (CLI compile) | NO | NO | PARTIAL |
| Literary Regression | YES (root) | YES (CLI only) | NO | NO | PARTIAL |
| Quality Engine V5 | YES | YES | YES | NO | ACTIVE |
| Quality Report | YES (core/quality) | NO | NO | NO | DEAD PATH |
| Quality Benchmark | YES (core/quality) | NO | NO | NO | DEAD PATH |
| Novel Prompt Engine | YES (core/quality) | NO | NO | NO | DEAD PATH |
| Provider (NvidiaClient) | YES | YES | YES | NO | ACTIVE |
| Provider Manager (TE) | YES | YES | YES | NO | ACTIVE |
| AI Provider (core/ai_provider) | YES | YES | YES | NO | ACTIVE |
| Provider Router | YES | YES | YES | NO | ACTIVE |
| Provider Retry | YES | YES | YES | NO | ACTIVE |
| Provider Rate Limiter | YES | YES | YES | NO | ACTIVE |
| Provider Fallback | YES | YES | YES | NO | ACTIVE |
| Provider Telemetry | YES | PARTIAL | NO | NO | PARTIAL |

## Module Detail

### 1. Input Pipeline

| Module | Path | Runtime Caller | Production Used |
|---|---|---|---|
| TXT Input (LTS) | lts/txt_translation_runtime.py:read_text_auto() | build_prompt_package -> read_text_auto | YES |
| EPUB/Book Intake | core/book_intake/ | Only tests & verification | NO |
| Document Normalizer v1 | core/document_normalizer.py | launcher.py (standalone only) | NO |
| Document Analyzer v1 | core/document_analyzer.py | tools/one_shots/launcher_analyzer.py (standalone) | NO |
| Chunking (core/chunker.py) | core/chunker.py | core/translator.py (v1 engine, deprecated) | NO |
| Chunking (LTS) | lts/txt_translation_runtime.py:split_text() | translate_txt() | YES |
| Book Book Intake | core/book_intake/ | controlled_translation_runtime_integration, controlled_multi_chunk_translation_canary | NO |
| Book Preparation | core/book_preparation/ | tests, verification, controlled_runtime ops | NO |
| Book Segmentation | core/book_segmentation/ | book_chunking, tests only | NO |
| Book Chunking | core/book_chunking/ | book_preparation, tests only | NO |

### 2. Context Pipeline

| Module | Path | Runtime Used | Prompt Impact |
|---|---|---|---|---|
| Context Builder | core/context/context_builder.py | NO (no runtime imports) | NO |
| Context Scene Memory | core/context_scene_memory/ | PARTIAL (v7.2 gate only) | PARTIAL |
| character_state.py | core/context/character_state.py | NO | NO |
| scene_state.py | core/context/scene_state.py | NO | NO |
| story_state.py | core/context/story_state.py | NO | NO |
| memory_engine.py | core/context/memory_engine.py | NO | NO |
| narrative_state.py | core/context/narrative_state.py | NO | NO |
| Previous Chunk Context | lts/txt_translation_runtime.py:previous_context | build_prompt_package() -> combine | YES |
| NarrativeContext (literary) | core/literary/narrative_context.py | LiteraryPromptBuilder.build() | YES |
| CharacterContext (literary) | core/literary/character_context.py | LiteraryPromptBuilder.build() | YES |
| Context Intelligence | core/translation_engine/context_intelligence.py | apply_context_intelligence() via build_prompt_package + TranslationEngine | YES |

### 3. Memory Pipeline

| Module | Path | Storage | Loader | Runtime Usage |
|---|---|---|---|---|
| Character Memory Engine (Legacy) | core/character_memory_engine.py | memory/character_memory.json | load_override + auto candidates | NO |
| Character Database (Legacy) | core/character_database.py | memory/character_database.json | load_override_characters | NO |
| Character V2 | core/character_memory_v2/ | In-memory store | v7.2 gate only | NO |
| Glossary (v1 Legacy) | core/glossary.py | glossary.txt file | Path-based load | NO |
| Glossary Builder (Legacy) | core/glossary_builder.py | memory/glossary.json | merge auto candidates | NO |
| Knowledge Base Builder (Legacy) | core/knowledge_base_builder.py | memory/knowledge_base.json | merge character | NO |
| Character Resolver | core/character_resolver.py | In-memory alias | glossary_builder (Legacy) | NO |
| Character Memory (LTS Runtime) | lts/txt_translation_runtime.py:load_locked_dictionary | glossary.txt, character_override.json, glossary_override.json | translate_txt -> locked_dictionary | YES |
| Character Memory (Prompt) | core/literary/character_context.py | runtime build | LiteraryPromptBuilder inside prompt | YES |
| Glossary (Prompt) | core/literary/glossary_context.py | runtime build | LiteraryPromptBuilder prompt | YES |

### 4. Prompt Pipeline

| Module | Path | Production Path |
|---|---|---|
| PromptEngine v1 (Legacy) | core/prompt_engine.py | NOT used by production runtime |
| LiteraryPromptBuilder | core/literary/literary_prompt_builder.py | YES - call from build_prompt_package() at LTSP |
| PromptCompiler | core/prompt_compiler/ | YES - called from PromptBuilder.compile() |
| Translation Discipline | core/translation_discipline/ | YES - injected by _ensure_runtime_prompt_compiler_wiring() |
| Prompt Intelligence | core/translation_engine/prompt_intelligence.py | YES - apply_prompt_intelligence() in build_thread |
| Context Intelligence | core/translation_engine/context_intelligence.py | YES - apply_context_intelligence() |
| pb_v72 Character/Scene | core/translation_quality_integration_v72 | YES - when quality flags are enabled (--quality-v72) |

### 5. Translation Engine

| Module | Path | Production Path |
|---|---|---|
| TranslationEngine | core/translation_engine/translation_engine.py | YES - used in TXT runtime |
| TranslationRuntime | core/translation_runtime/runtime.py -> translation_engine | YES - entry for PRODUCTION translate |
| Text Translator Engine (v1 legacy) | core/translator.py | NOT USED in production |
| NvidiaClient (TE provider) | core/translation_engine/nvidia_client.py | YES - via build_translation_provider_manager |
| Orchestrator | core/translation_engine/orchestrator.py | PARTIAL - SDK/UI only, not in production |
| Production Runtime host | core/production_runtime/host.py | PARTIAL - optional bridge to Orchestrator only |
| Translation Sessions | core/translation_session/ | YES - loaded by TranslationRuntime |
| Translation Pipelines | core/translation_pipeline/ | YES - loaded |
| Translation Resources | core/translation_resources/ | YES - loaded |
| Translation Plugin | core/translation_plugins/ | YES - loaded |
| LTS Retry/Resume | lts/txt_translation_runtime.py:translate_package_with_retry + resume state loading | YES |

### 6. Quality Pipeline

| Module | Path | Production Use |
|---|---|---|
| Basic QA | core/translation_engine/basic_qa.py | YES but minimal - inside TranslationEngine.translate_package |
| Runtime QA (v5) | core/translation_runtime/runtime_qa.py | YES - via analyze_runtime_quality in txt_runtime |
| Quality V5 (RT) | core/translation_quality_v5/ | YES - RuntimeIntegration + stage reports |
| Quality integration V7.2 | core/translation_quality_integration_v72/ | PARTIAL - gate-controlled by V2 KM/CM flags |
| Quality Engine (core) | core/quality/quality_engine.py | NO - no runtime import from production |
| Quality Report/Repair (core) | core/quality/*.py | NO |
| Novel Prompt Engine | core/quality/novel_prompt_engine.py | NO |
| Literary Evaluation | ntpe_literary_evaluation.py | YES (CLI only, post-translation after regression compiles) |
| Literary Regression | ntpe_literary_regression.py | YES (CLI only, test suite only, not translation pipeline) |

### 7. Provider Pipeline

| Module | Path | Production Path |
|---|---|---|
| NvidiaEngine (v1) | engine/nvidia.py | NO (v1 engine) |
| NvidiaClient (TE) | core/translation_engine/nvidia_client.py | YES |
| Provider Runtime | core/translation_engine/provider_runtime.py | YES (build_translation_provider_manager) |
| AI Provider Layer | core/ai_provider/ | YES (ProviderManager, Router, Registry) |
| RateLimiter | core/ai_provider/rate_limiter.py | YES |
| Retry | core/ai_provider/retry.py | YES |
| FallbackChain | core/ai_provider/fallback_chain.py | YES |
| Provider connection via | core/translation_runtime/runtime.py:RuntimeProviderAdapter | YES |
| Provider bridge | core/ai_provider/runtime_bridge.py | YES |

## Key Evidence

- **ACTIVE Pipeline Total: 23 (pipelines)** - TXT Input, Chunking (LT), Previous Context, Narrative Context, Character Context (Lit), Glossary (LT), Prompt Builder, Prompt Compiler, Translation Discipline, Prompt Intelligence, Context Intelligence, TranslationEngine, TranslationRuntime, TXT Runtime, Batch Runtime, LTR Recovery, Basic QA, Runtime QA V5, Quality V5, Quality V72, NvidiaClient, Provider Runtime, AI Provider
- **PARTIAL**: 7 (Book Intake, Context Scene Memory, Character Memory V2, Character Resolver, Knowledge Runtime, Orchestrator, Literary Evalutation, Literary Regression)
- **DEAD PATH**: 8 (core/context/ builder, Document Intake, Book Preparation, Book Segmentation, Book Chunk, core/quality engine, Quality Report, Quality Benchmark, Novel Prompt Engine, core/knowledge)
- **LEGACY**: 10 (Doc Normalizer, Doc Analyzer, core/chunker.py, PromptEngine, core/grossary.py, )