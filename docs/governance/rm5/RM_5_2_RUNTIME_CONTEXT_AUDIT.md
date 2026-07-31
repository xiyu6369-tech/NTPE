# RM-5.2 Runtime Context Integration Audit

> **Stage**: RM-5.2 — Audit Only  
> **Status**: ✅ AUDIT COMPLETE  
> **Date**: 2026-08-01  
> **Production Code Modified**: 0  
> **Provider Requests Made**: 0  
> **Network Requests Made**: 0

---

## Executive Summary

The NTPE Production Translation Runtime has a well-structured prompt assembly pipeline that correctly injects static dictionary-based resources (character names, glossary terms, translation rules) and optional dynamic layers (voice profile, semantic engine, style planner, novel prompt engine).

However, the system has a **significant gap**: three fully-built, Provider-Free quality modules exist but are **never wired into the production translation flow**:

1. **Character Memory V2** — Token-budget-aware, confidence-filtered character memory with 16 fact types.
2. **Context Scene Memory** — Scene participant tracking, reference resolution, speaker/location states.
3. **Translation Quality Integration V72** — A provider-free adapter that bridges all quality contexts into the prompt.

Additionally, two modules are **loaded but never consumed** (Knowledge Base, KnowledgePromptRuntime), and one module exists but is CLI-only (Semantic Repair).

---

## What ACTUALLY Reaches the LLM

### Confirmed route (from code trace):

```
chunk_text
    → CharacterSelector (regex match from static dict)
    → GlossarySelector (substring match from static dict)
    → VoiceProfile (optional, runtime-dependent)
    → SemanticEngine (optional)
    → DocumentStructureEngine (optional)
    → NovelStylePlanner (optional)
    → NovelPromptEngine (optional)
    → RuleGenerator (from profile)
    → ContextMemoryEngine (optional, from 5 JSON state files)
    → PromptRenderer.render()
        → system_prompt
        → user_prompt (the combined prompt)
    → PackageBuilder.build()
    → TranslationEngine.translate_package()
        → apply_prompt_intelligence() → prepends quality directives
        → apply_context_intelligence() → prepends context directives
        → ProviderRequest(prompt=user_prompt, metadata={system_prompt})
    → NvidiaTranslationProvider
    → NVIDIA API
```

### What is MISSING from the prompt that was designed to be there:

1. **Dynamic character memory** (relationships, honorifics, speech styles, pronouns) — only static name mapping exists.
2. **Scene context tracking** (who is in the room, what just happened, location changes).
3. **Naturalness guard policy** (anti-pattern rules: redundant counting, tourist-person, entangled, etc.)
4. **KB-enriched terminology** — KB is loaded, never used.

---

## The Single Most Valuable Change

**Wire `translation_quality_integration_v72/adapter.apply_to_prompt_package()`** inside `TranslationEngine.translate_package()`.

This **single call** (Provider-Free, Output-Free) would inject:
- Character Memory V2 (filtered, budget-managed)
- Context Scene Memory (scene participants, states)
- Naturalness Policy (14 anti-pattern rules)

All three modules already exist, are tested, and are designed for exactly this injection point. They are currently **orphaned** — only called from LCR shadow hooks and test frameworks.

---

## RM-5.3 Readiness

### All exit criteria questions can now be answered with evidence:

| Question | Answer |
|----------|--------|
| 1. Character Memory should be injected at which layer? | **TranslationEngine.translate_package()**, via `apply_to_prompt_package()`, as a `user_prompt` section prepend. Evidence: `translation_engine.py:41` already calls `apply_prompt_intelligence()`. |
| 2. Glossary should be provided by which module? | Currently by `GlossarySelector` (static dict). **Can be enhanced** by `character_memory_v2`'s `FactType.TERMINOLOGY_PREFERENCE` if needed. |
| 3. Does PromptBuilder have an extension point? | **Yes** — The `prompt` dict's `user_prompt` key is modified in-place by prompt/context intelligence. An additional section prepend is the established pattern. |
| 4. Which legacy context can be safely removed? | **Knowledge Base load** (`loader.py:25-26`) — data loaded but never referenced downstream. |
| 5. Minimum change, maximum benefit? | **Wire `apply_to_prompt_package()` in `TranslationEngine`**. ~5 lines of code. Unlocks 3 dormant quality modules. |

---

## Deliverables

- ✅ `RM_5_2_PROMPT_FLOW.md` — Step-by-step prompt assembly with file paths
- ✅ `RM_5_2_CONTEXT_INVENTORY.md` — 15-item inventory with evidence
- ✅ `RM_5_2_GAP_ANALYSIS.md` — 6 gaps ranked by impact
- ✅ `RM_5_2_EXECUTION_REPORT.md` — This file with execution summary
- ✅ No production code modified

---

## Validation Checklist

| Check | Status |
|-------|--------|
| Production Code Modified | 0 files ✅ |
| Runtime Modified | 0 lines ✅ |
| Provider Requests | 0 ✅ |
| Network Requests | 0 ✅ |
| Wrapper Created | 0 ✅ |
| `git diff --check` | PENDING |
| `python ntpe_validate.py` | PENDING |
| `python -m compileall .` | PENDING |