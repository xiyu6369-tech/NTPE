# RM-5.2 Gap Analysis

> **Stage**: RM-5.2 Runtime Context Integration Audit  
> **Status**: Audit Only — Zero Production Code Modified  
> **Date**: 2026-08-01

---

## Gap 1: Character Memory V2 — Full Capability, Zero Usage

**Status**: ❌ UNUSED in production

**What exists**: `core/character_memory_v2/` — a complete 9-file package with:
- MemoryRecord lifecycle (approve, reject, expire, supersede)
- Token-budget-aware selection (`select_prompt_eligible_memories`)
- 16 fact types (CANONICAL_NAME, RELATIONSHIP, SPEECH_STYLE, PRONOUN_REFERENCE, etc.)
- Confidence threshold filtering (default 0.85)
- Scope-based expiry (segment, chapter, session)
- Language profile filtering
- Deduplication engine

**What happens at runtime**: The character names in the prompt come ONLY from `CharacterSelector` which is a **regex/substring static dictionary**. There is NO dynamic memory:

```
Production path:
  chunk_text → CharacterSelector.select() → character_match_dictionary.json → matches[]

NOT called:
  character_memory_v2/selection.select_prompt_eligible_memories(store, ...)
```

### Impact

| Dimension | Rating |
|-----------|--------|
| **Translation Quality Impact** | **HIGH** — Without character memory, the LLM gets only one chunk's context for names, honorifics, pronouns, and character relationships. Can result in name inconsistency across chunks. |
| **Runtime Risk** | LOW — CharacterMemoryV2 is pure offline, no provider calls. |
| **Compatibility Risk** | LOW — V2 stores are JSON files, no schema migration needed. |
| **Estimated Benefit** | Significant reduction in name/pronoun/honorific errors across chunk boundaries. |

**Injection point**: `PromptBuilder.build()` or `PromptRenderer.render()` — between character selector and renderer.

---

## Gap 2: Context Scene Memory — Full Capability, Zero Usage

### Status**: ❌ UNUSED in production

**What exists**: `core/context_scene_memory` — scene participant tracking, reference resolution, speaker state, location_state, temporal_state.
**What runs**: `core/context/memory_engine.py` — a simpler 5-state-file system (story, character, scene, dialogue, narrative).

### Impact

| Dimension | Status |
|-----------|--------|
| **Translation Quality Impact** | **HIGH** — Without scene memory, the LLM gets only `【前文參考】` (previous chunk tail) for context continuity. No scene-level tracking of who is in the room, what just happened, etc. |
| **Runtime Risk** | LOW — Context scene is pure data, no provider. |
| **Compatibility Risk** | LOW — Can coexist with existing memory_engine. |
| **Estimated Benefit** | High — Better scene continuity, POV consistency. |

---

## Gap 3: Knowledge Base — Loaded, Never Consumed

### Status**: ⚠️ DEPRECATED (dead path)

**Evidence**: `PromptBuilderLoader.load_knowledge_base()` reads `knowledge_base.json` at init.
Variable: `self.data["knowledge_base"]`
Consumer: **None found**. Checked `packager_builder.py`, `prompt_renderer.py`, `PromptBuilder.build()` — none reference `self.data["knowledge_base"]`.

### Impact

| Dimension | Status |
|-----------|--------|
| **Translation Quality Impact** | **ZERO** — Data exists but never enters prompt. |
| **Runtime Risk** | NONE |
| **Action** | **Safe to remove** the `load_knowledge_base()` call from loader to reduce startup I/O. |
---

## Gap 4: Translation Quality Integration V72 — Designed, Not Wired

**Status**: ❌ UNUSED in production

**What exists**: `core/translation_quality_integration_v72/adapter.py` — Provider-Free adapter: `integrate_prompt()`, `apply_to_prompt_package()`, `allocate_prompt_budget()`, `select_quality_context()`.

**What happens at runtime**: NOTHING. `TranslationEngine.translate_package()` calls `apply_prompt_intelligence()` + `apply_context_intelligence()` but NEVER calls `apply_to_prompt_package()`.

**Confirmation**: Searched all production `.py` for `from.*translation_quality_integration_v72` → 0 results.

### Impact

| Dimension | Rating |
|-----------|--------|
| **Translation Quality Impact** | **HIGH** — TQI V72 bridges CharacterMemoryV2 + ContextSceneMemory + Naturalness Policy. Missing = none in prompt. |
| **Runtime Risk** | LOW — Provider-Free, Output-Free. |
| **Compatibility Risk** | LOW — Pure function on package dict. |
| **Estimated Benefit** | Very High — SINGLE HIGHEST VALUE: one call unlocks 3 major quality features. |

---

## Gap 5: Style Expansion — Standalone Post-Processor

**Status**: ❌ UNUSED in production

**What exists**: `core/expansion/style_expansion_engine.py` — calls NVIDIA API for paragraph expansion.

### Impact

| Dimension | Rating |
|-----------|--------|
| **Translation Quality Impact** | **MEDIUM** |
| **Runtime Risk** | **HIGH** — additional provider calls |
| **Action** | Defer to RM-5.4+ |

---

## Gap 6: Semantic Repair — CLI Only

**Status**: ❌ UNUSED in production translation

**What exists**: `core/quality/semantic_repair.py`. Only accessed via `cli/commands/quality.py`.

### Impact

| Dimension | Rating |
|-----------|--------|
| **Translation Quality Impact** | **MEDIUM** |
| **Runtime Risk** | LOW |
| **Action** | Optional post-translation step for RM-5.4+ |

---

## Ranked Priority — Minimal Change, Maximum Impact

| Rank | Change | Lines | Impact | Risk |
|------|--------|-------|--------|------|
| **🥇 1** | Wire TQI V72 adapter in TranslationEngine | ~5 lines | HIGH | LOW |
| **🥈 2** | Sync ContextMemoryEngine after each chunk | ~10 lines | HIGH | LOW |
| **🥉 3** | Remove dead KB loader call | ~1 line | ZERO | NONE |
| 4 | Wire Voice Profile (already optional) | ~3 lines | MEDIUM | LOW |
| 5 | Wire StyleExpansion | ~10 lines | MEDIUM | HIGH (provider) |
| 6 | Wire Semantic Repair post-QA | ~15 lines | MEDIUM | LOW |