# RM-5.2 Runtime Context Inventory

> **Stage**: RM-5.2 Runtime Context Integration Audit  
> **Status**: Audit Only — Zero Production Code Modified  
> **Date**: 2026-08-01

---

## Context Inventory: What Reaches the LLM

| # | Context Type | Status | Evidence |
|---|-------------|--------|----------|
| 1 | **Previous Chunk (tail text)** | ⚠️ PARTIALLY_USED | `PromptBuilder.build()` calls `ContextMemoryEngine.build_context()` which returns `previous_chunk_tail`. PromptRenderer injects it under `【前文參考】`. BUT: `context` param is always `None` in ProductionPipeline (line 93-99). Falls back to `memory_engine.build_context()`. States loaded from JSON files. If states empty, block omitted. |
| 2 | **Character Names (match dictionary)** | ✅ USED | `CharacterSelector.select()` called in PromptBuilder.build(). Results → PromptRenderer under `【本段人物譯名】`, also in `knowledge.character_matches`. Source: `character_match_dictionary.json`. |
| 3 | **Glossary Terms** | ✅ USED | `GlossarySelector.select()` in PromptBuilder.build(). Results → `【本段術語】` and `knowledge.glossary_matches`. Source: `glossary.json` (or `data/glossary.txt` via `core/rules.py`). |
| 4 | **Character Memory (V2)** | ❌ UNUSED | `core/character_memory_v2` has `select_prompt_eligible_memories()` with token-budget, scope, confidence, fact-type filtering. Only called from: (a) `translation_quality_integration_v72/selection.py` (b) `lcr_production_shadow_hook/`. NEITHER is active in production. |
| 5 | **Context Scene Memory** | ❌ UNUSED | `core/context_scene_memory` → `select_context_for_translation()`. Only called from TQI v72 adapter and LCR shadow hooks. NOT wired into ProductionPipeline. |
| 6 | **Knowledge Base (KB)** | ⚠️ DEPRECATED | `PromptBuilderLoader.load_knowledge_base()` loads KB, but data is never passed to downstream builder (not Renderer, not Package). Sits in `self.data["knowledge_base"]` unused. |
| 7 | **Novel Profile** | ✅ USED | Loaded from `profiles/passion_profile.json`. Used by: RuleGenerator, PromptRenderer (`target_variant`). |
| 8 | **Style Guide / Style Plan** | ⚠️ PARTIALLY_USED | `NovelStylePlanner` is optional import. Output → `【小說風格規劃】`. Defaults to empty if import fails. |
| 9 | **Semantic Repair** | ❌ UNUSED | `core/quality/semantic_repair.py` exists but NOT called from TranslationEngine or ProductionPipeline. Used only by CLI quality commands. |
| 10 | **Quality Evaluation Engine** | ⚠️ PARTIALLY_USED | `core/quality/quality_engine.py` exists but NOT called in translation flow. Only `basic_qa.py` runs — checks Korean residue, length, locked names. No quality score. |
| 11 | **Context Window (model)** | ✅ USED | Stored in package JSON (`model_profile.context_window`) but not enforced at runtime. Provider uses max_tokens for output, not input capping. |
| 12 | **Resume State** | ⚠️ PARTIALLY_USED | `resume_key` stored in package.session. Session saved. But no explicit checkpoint loading on restart. |
| 13 | **Voice Profile / Voice Memory** | ⚠️ PARTIALLY_USED | Optional import in PromptBuilder. If available: matches voice profiles → `【人物語氣規則】`. If import fails → skipped. |
| 14 | **Style Expansion Engine** | ❌ UNUSED | `core/expansion/style_expansion_engine.py` calls NVIDIA API for post-process coverage expansion. NOT called from ProductionPipeline. |
| 15 | **Translation Quality Integration V72** | ❌ UNUSED | `apply_to_prompt_package()` is Provider-Free. But NO code in production path calls it. Only tests + AB canary frameworks. |

---

## Summary

| Status | Count | Items |
|--------|-------|-------|
| ✅ USED | 5 | Character Names (dict), Glossary, Novel Profile, Context Window, Model Profile |
| ⚠️ PARTIALLY_USED | 4 | Previous Chunk, Style Plan, Voice Profile, Resume State |
| ❌ UNUSED | 5 | Character Memory V2, Context Scene Memory, Semantic Repair, Style Expansion, TQI V72 |
| ⚠️ DEPRECATED | 1 | Knowledge Base (loaded but never consumed) |
---

## Evidence Trace Map

| Claim | Evidence File | Line(s) |
|-------|--------------|---------|
| CharMemoryV2 not in prod path | `core/prompt_builder/prompt_builder.py` | No import of character_memory_v2 |
| KB loaded but unused | `core/prompt_builder/loader.py` | L25-26 load_knowledge_base() |
| KB never passed downstream | `core/prompt_builder/prompt_builder.py:build()` | No use in render/package |
| TQI V72 not called | `core/translation_engine/translation_engine.py` | No import of tqi_v72 |
| CharV2 only in LCR/TQI | Search for `select_prompt_eligible_memories` | Found only in shadow hooks, TQI |
| ContextSceneMemory only in shadow | Search for `select_context_for_translation` | Found only in TQI, shadow |
| SemanticRepair not used | `translation_engine.py:38-110` | No import or call |
| StyleExpansion not used | `production_pipeline.py` | No import |
| KnowledgePromptRuntime not imported | Search all `.py` files | 0 production imports |