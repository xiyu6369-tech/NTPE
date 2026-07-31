# RM-5.2 Prompt Assembly Flow

> **Stage**: RM-5.2 Runtime Context Integration Audit  
> **Status**: Audit Only — Zero Production Code Modified  
> **Date**: 2026-08-01

---

## Complete Prompt Assembly Flow (Production Path)

```
Input → ChunkEngine → PromptBuilder → PromptRenderer → PackageBuilder → TranslationEngine → ProviderManager → NVIDIA API

See RM_5_2_EXECUTION_REPORT.md for the full annotated trace with file paths.
```

---

## Per-Stage Data Inventory

| Step | Module | File | Input | Output |
|------|--------|------|-------|--------|
| 1. Scan | `ProjectManager` | `engine/pipeline/project_manager.py` | Normalized TXT files | File list |
| 2. Split | `ChunkEngine` | `engine/pipeline/chunk_engine.py` | Raw text (per file) | `list[Chunk]` |
| 3. Load | `PromptBuilderLoader` | `core/prompt_builder/loader.py` | `passion_profile.json`, char dict, glossary.json, KB | `profile` dict, char dict, glossary |
| 4. Context | `ContextMemoryEngine` | `core/context/memory_engine.py` | state JSON files | `context` dict (previous, tail, chars) |
| 5. Characters | `CharacterSelector` | `core/prompt_builder/character_selector.py` | chunk_text + char_match_dict | `character_matches[]` |
| 6. Glossary | `GlossarySelector` | `core/prompt_builder/glossary_selector.py` | chunk_text + glossary dict | `glossary_matches[]` |
| 7. Voice | `VoiceProfile` | `core/voice/voice_profile.py` | chunk_text | `voice_matches[]` (opt) |
| 8. Semantic | `SemanticEngine` | `core/quality/semantic_engine.py` | chunk_text | `semantic_matches[]` (opt) |
| 9. Structure | `DocumentStructureEngine` | `core/quality/structure_engine.py` | chunk_text | `doc_structure` (opt) |
| 10. Style | `NovelStylePlanner` | `core/quality/novel_style_planner.py` | chunk_text | `style_plan` (opt) |
| 11. NovelPrompt | `NovelPromptEngine` | `core/quality/novel_prompt_engine.py` | chunk_text | `novel_sections` (opt) |
| 12. Rules | `RuleGenerator` | `core/prompt_builder/rule_generator.py` | profile | `rules` dict |
| 13. Render | `PromptRenderer` | `core/prompt_builder/prompt_renderer.py` | All above + chunk_text | `{system_prompt, user_prompt}` |
| 14. Package | `PackageBuilder` | `core/prompt_builder/package_builder.py` | Everything | Package JSON |
| 15. Translate | `TranslationEngine` | `core/translation_engine/translation_engine.py` | Package JSON | ProviderRequest |
| 16. Provider | `ProviderManager` | `core/translation_engine/provider_runtime.py` | ProviderRequest | ProviderResponse |
| 17. QA | `BasicTranslationQA` | `core/translation_engine/basic_qa.py` | package + translation | QA result |

---

## Key Architectural Facts

1. **The final `user_prompt` is assembled in `PromptRenderer.render()`** (step 13) and then **modified post-serialization** by `apply_prompt_intelligence()` and `apply_context_intelligence()` inside `TranslationEngine.translate_package()` (step 15).

2. **system_prompt is sent via metadata**, not as a top-level system role — `ProviderRequest(prompt=user_prompt, metadata={system_prompt=...})` → the `NvidiaTranslationProvider` passes it to `NvidiaClient.chat()` which does make a proper system + user message call.

3. **The final prompt string is NOT saved back to the package JSON file** — it's computed at runtime from `PromptRenderer.render()` output + runtime injection.

4. **ContextMemoryEngine builds from 5 JSON state files** (story, character, scene, dialogue, narrative) stored in `core/context/`.

5. **CharacterMemoryV2** (with `select_prompt_eligible_memories`) exists but is NOT called in the Production path; it's only used by the LCR shadow hook and the `translation_quality_integration_v72` adapter — **neither is active in current production**.

---

## Prompt Injection Order

1. `PromptRenderer.render()` produces `user_prompt` 
2. `PackageBuilder.build()` wraps into package JSON
3. Package saved to `prompt_packages/*.json`
4. `TranslationEngine.translate_package()` loads package
5. `apply_prompt_intelligence()` prepends quality directives block
6. `apply_context_intelligence()` prepends context directives block
7. Final `user_prompt` sent as `ProviderRequest.prompt`
                          │    Selector.select()  │
                          │    → glossary_match[] │  substring match
                          │                       │
                          │  Step 5: VoiceProfile │  voice_profile.py (optional)
│ all data
                                    ▼
                          ┌──────────────────────┐
                          │   PromptRenderer     │  prompt_renderer.py
                          │   .render()          │
                          │  ──────────────────── │
                          │  Combines:           │
                          │  【翻譯規則】         │
                          │  【本段人物譯名】     │
                          │  【本段術語】         │
                          │  【人物語氣規則】     │
                          │  【本段語義鎖定】     │
                          │  【前文參考】         │
                          │  【待翻譯內容】       │
                          │                       │
                          │  Output:             │
                          │  {                   │
                          │    system_prompt     │
                          │    user_prompt       │  ← THE FINAL PROMPT
                          │  }                   │
                          └─────────┬────────────┘
                                    │
                                    ▼
                          ┌──────────────────────┐
                          │   PackageBuilder     │  package_builder.py
                          │   .build()           │
                          │  ──────────────────── │
                          │  Wraps everything     │
                          │  into JSON package:   │
                          │   - package_id        │
                          │   - source            │
                          │   - context           │
                          │   - knowledge         │
                          │   - rules             │
                          │   - prompt            │  ← system + user
                          │   - model_profile     │
                          │   - token_estimate    │
                          │   - qa_requirements   │
                          │   - metadata          │
                          └─────────┬────────────┘
                                    │ saved as JSON
                                    ▼
                          ┌──────────────────────┐
                          │  TranslationEngine   │  translation_engine.py
                          │  .translate_package() │
                          │  ──────────────────── │
                          │  Step A: validate     │
                          │  Step B: prompt_intel │  ← injects quality directives
                          │          -> user_prompt │
                          │  Step C: context_intel│  ← injects context directives
                          │          -> user_prompt │
                          │  Step D: provider     │  ← sends user_prompt + system
                          │     ProviderRequest(   │     to LLM
                          │       prompt=user_prompt│
                          │       metadata={       │
                          │         system_prompt  │
                          │       })               │
                          │  Step E: QA check     │  basic_qa.py
                          │  Step F: save output  │
                          └─────────┬────────────┘
                                    │
                                    ▼
                          ┌──────────────────────┐
                          │   ProviderManager    │  provider_runtime.py
                          │   .complete()        │
                          │  ──────────────────── │
                          │  Dispatches to:      │
                          │  NvidiaTranslation-  │
                          │  Provider.complete()  │
                          │    → NvidiaClient    │
                          │    → NVIDIA API      │
                          │      https://integrate│
                          │      .api.nvidia.com │
                          └─────────┬────────────┘
                                    │
                                    ▼
                          ┌──────────────────────┐
                          │   Translation + QA   │
                          │  → translated/*_zh.txt│
                          └──────────────────────┘
```

---

## Per-Stage Data Inventory

| Stage | Module | Consumed Data | Produced Data |
|-------|--------|---------------|---------------|
| Chunk Builder | `chunk_engine.py` | Normalized TXT | `Chunk.text`, `.index`, `.char_count` |
| PromptBuilder Init | `prompt_builder.py` | `passion_profile.json`, char dict, glossary, KB | `self.data` (in-memory) |
| Context Memory | `memory_engine.py` | state JSONs (`story_state.json`, etc.) | `context` dict |
| Character Selector | `character_selector.py` | chunk_text, char dict | `character_matches` list |
| Glossary Selector | `glossary_selector.py` | chunk_text, glossary dict | `glossary_matches` list |
| Voice Profile | `voice_profile.py` | chunk_text | `voice_matches` list |
| Semantic Engine | `semantic_engine.py` | chunk_text | `semantic_matches` list |
| Structure Engine | `structure_engine.py` | chunk_text | `document_structure` dict |
| Style Planner | `novel_style_planner.py` | chunk_text | `style_plan` dict |
| Novel Prompt Engine | `novel_prompt_engine.py` | chunk_text | `novel_prompt_sections` dict |
| Rule Generator | `rule_generator.py` | profile | `rules` dict |
| Prompt Renderer | `prompt_renderer.py` | All above + chunk_text | `{system, user}` prompt |
| Package Builder | `package_builder.py` | Everything | Package JSON |
| Translation Engine | `translation_engine.py` | Package JSON | enhanced `user_prompt` → ProviderRequest |
| Provider Manager | `provider_runtime.py` | ProviderRequest | ProviderResponse → raw text |
| QA Check | `basic_qa.py` | package, translation | QA issues |
                          │    .match()           │
                          │    → voice_matches[]  │
                          │                       │
                          │  Step 6: Semantic     │  semantic_engine.py (optional)
                          │    Engine.select()    │
                          │    → semantic_match[] │
                          │                       │
                          │  Step 7: Structure    │  structure_engine.py (optional)
                          │    Engine.analyze()   │
                          │    → doc_structure    │
                          │                       │
                          │  Step 8: StylePlan    │  novel_style_planner.py (optional)
                          │    Planner.plan()     │
                          │    → style_plan       │
                          │                       │
                          │  Step 9: NovelPrompt  │  novel_prompt_engine.py (optional)
                          │    Engine.build_sec() │
                          │    → novel_sections   │
                          │                       │
                          │  Step 10: Rules       │  rule_generator.py
                          │    Generator.gen()    │
                          │    → rules dict        │
                          └─────────┬────────────┘