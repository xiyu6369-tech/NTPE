# RM-5.9.0 Prompt Injection Policy

**Version**: RM-5.9.0  
**Date**: 2026-08-06  
**Status**: 🔒 **FROZEN — Governance Policy**

---

## Purpose

Define the mandatory injection order and section structure for knowledge context insertion into translation prompts. This policy serves as the single source of truth for all RM-5.9.x prompt assembly — every knowledge injection must follow this ordering.

---

## 1. Injection Order

### 1.1 Mandurated Injection Sequence

```
┌──────────────────────────────────────────────┐
│          SYSTEM PROMPT (FROZEN RM-4)          │  Always first. Never modified by knowledge layer.
├──────────────────────────────────────────────┤
│                                                │
│  1. CHARACTER KNOWLEDGE                        │  Character metadata, aliases, translations.
│                                                │
├──────────────────────────────────────────────┤
│                                                │
│  2. GLOSSARY KNOWLEDGE                        │  Term translations, context rules, forbidden forms.
│                                                │
├──────────────────────────────────────────────┤
│                                                │
│  3. SCENE KNOWLEDGE                           │  Scene setting: location, time, participants.
│                                                │
├──────────────────────────────────────────────┤
│                                                │
│  4. NARRATIVE KNOWLEDGE                      │  Plot points, timeline position, world rules.
│                                                │
├──────────────────────────────────────────────┤
│                                                │
│  5. STYLE KNOWLEDGE                           │  Register rules, voice style, collocation patterns.
│                                                │
├──────────────────────────────────────────────┤
│                                                │
│  6. TRANSLATION RULES (FROZEN RM-4)   │  【翻譯規則】— existing rules block
│                                                │
├──────────────────────────────────────────────┤
│                                                │
│  7. CHUNK TEXT                               │  【待翻譯內容】— the source text to translate
│                                                │
└──────────────────────────────────────────────┘
```

### 1.2 Injection Rationale

| Position | Domain | Rationale |
|----------|--------|-----------|
| 1 | **Character** | Characters form the backbone of narrative identity. Injecting characters first establishes the "who" before any terminology. If the model confuses a character's canonical name, all subsequent terms referencing that character are corrupted. |
| 2 | **Glossary** | Glossary terms must reference characters correctly. A glossary entry that says "use X for character A" is meaningless if character A was already confused. Glossary follows character to ensure cross-domain consistency. |
| 3 | **Scene** | Scenes provide spatial-temporal context. The LLM needs to know WHERE and WHEN the action occurs before applying narrative or style rules, because style and pacing depend on scene type (action vs dialogue-heavy vs atmospheric). |
| 4 | **Narrative** | Narrative knowledge provides the "what" — plot position, timeline state, world rules. This is deliberately after Scene so the LLM can evaluate plot state against the concrete setting. |
| 5 | **Style** | Style is the most subjective domain. Tone, register, and voice patterns are nudges, not constraints. They should influence the final phrasing without overriding substance. Injecting style late means the LLM has already processed character, glossary, scene, and narrative — style then refines. |
| 6 | **Rules** | Existing translation rules (【翻譯規則】) are operational constraints. They must be visible but not dominate the prompt. Rules after knowledge means knowledge first informs the LLM, then rules govern the output. |
| 7 | **Chunk** | Source text is the payload. Everything before it is context. The LLMs media processes the context stack in natural reading order: identity → terms → setting → story → style → rules → text. |

### 1.3 Ordering Proof

The injection order is validated against RM-5.2 Context Inventory facts:

- **CharacterMemoryV2** — has select_prompt_eligible_memories() (token budget, confidence filtering) — needs character before scene so character IDs can scope scene/marrative queries.
- **SceneMemory** — participants are referenced by character entity IDs — must have Character before Scene.
- **Glossary** — has context_rules and forbidden_forms that reference character names (e.g., "do not translate 定期-先生 as X in character Y's dialogue") — must inject after Character to ensure cross-domain integrity.
- **Narrative** — plot_points reference scenes_timeline; scenes and events cross-reference character milestones — needs Character + Scene before Narrative.
- **Style** — voice_register_guard detects CHARACTER_VOICE_DRIFT, NARRATIVE_REGISTER_DRIFT — needs Character + Narrative before Style to detect drift against individual characters.

**Conclusion**: The 1→5 ordering from Character → Glossary → Scene → Narrative → Style is a **transitive dependency chain** driven by entity reference graph. No reverse ordering is possible without breaking cross-domain integrity.

---

## 2. Section Structure Per Domain

### 2.1 Character Knowledge Section

```
【人物知識】
- 姓名: {canonical_name} (原文: {source_name}) | 别名: {aliases}
  角色: {role} | 特徵: {traits} | 與 {character_name} 關係: {relationship_description}
```

**Template properties**:
| Field | Source | Required |
|-------|--------|----------|
| canonical_name | character canonic name | ✅ |
| source_name | character source name (Korean) | ✅ |
| aliases | character liases (other names/pronouns) | If non-empty |
| role | character role | ✅ |
| traits | character traits (max 5) | Optional |
| relationships | other characters referenced | If non-empty |

**No more than 8 characters per chunk** (enforced by context budget policy).

### 2.2 Glossary Knowledge Section

```
【術語知識】
【術語】 {source_term} {source_term_alt} → {canonical_translation}
       領域: {domain_tags} | 上下文限制: {context_rules}
       禁用: {forbidden_forms}
```

**No more than 12 entries per chunk** (context budget).

### 2.3 Scene Knowledge Section

```
【場景知識】
位置: {location} | 時間: {time_of_day} | 章節: {chapter_range}
出場角色: {participants} | 基調: {tone}
摘要: {summary}
```

**No more than 2 scenes per chunk** (scene continuity assumption on same chapter).

### 2.4 Narrative Knowledge Section

```
【敘事知識】
章節進度: 第{current_chapter_n}/{total_chapters}章
時間線: {timeline_summary}
劇情點: {plot_points}
{plot_point_guidance}
世界規則: {world_rules}
角色里程碑: {character_milestones}
```

**No more than 5 plot points, 3 world rules per chapter**.

### 2.5 Style Knowledge Section

```
【風格知識】
語域: {register_rules}
文體: {genre_profile}
配搭模式: {collocation_patterns}
正面風格圖案: {positive_patterns:[1-3]}
```

**No more than 3 rules + 3 patterns**.

---

## 3. Injection Complexity Policy

### 3.1 When to Skip a Section

A domain section is **omitted** entirely from a chunk's prompt when:

| Condition | Behavior |
|-----------|----------|
| No matching entities after retrieval | Omit the section (empty section adds noise) |
| All entities too short to provide information | Omit |
| Domain has been culled by budget policy | Omit (with metadata: `injection_skips: ["Character"]`) |
| KnowledgeContext indicates retrieve timeout | Omit (fallback to no-knowledge mode) |

### 3.2 When to Use Minimal Sections

| Condition | Behavior |
|-----------|----------|
| Single entity, but the entity (< 50 char) | Collapse into inline note, not full section |
| Entities are stale (no update from previous session) | Attach `(from previous session)` |
| Budget at 40% remaining after character + glossary | Use summary sections for scene/narrative/style |

### 3.3 Metadata Injection

Every injected prompt package contains metadata for traceability:

```json
{
  "injection_policy": "rm-5.9.0",
  "injection_order": [
    "system",
    "character",
    "glossary",
    "scene",
    "narrative",
    "style",
    "rules",
    "chunk"
  ],
  "injection_skipped": [],
  "domains_injected": 5,
  "bytes_injected": 2840
}
```

---

## 4. Interleaving Exclusions

### 4.1 Never Interleave

The same order and section boundaries apply to EACH chunk in a translation session. The order is never rearranged or interleaved.

| Forbidden | Why |
|-----------|-----|
| Injecting Glossary before Character | Glossary context_rules reference character names; broken cross-domain integrity |
| Injecting Narrative between Scene → Style | Scene is the foundation for narrative context — style must follow narrative |
| Injecting raw JSON entity objects | Prompt is markdown — never send JSON to the LLM |
| Injecting schema metadata (version, created_time, UUID) | Theseedbitrary noise for the LLM |

### 4.2 Exceptions

| Exception | When applicable | Rationale |
|-----------|----------------|-----------|
| Character-only mode | Chunk has >90% dialogue and Scene/Narrative/Style are all redundant | Use character + existing rules only; skip narrative and scene |
| Pure narration fallback | Chunk has >95% narration (minimal character references) | Run narrative + style first, then character (still within injection policy, but re-prioritized) |

Both exceptions must be explicitly declared and logged in injection metadata under `injection_mode: "character_only" | "pure_narraration"`.

---

## 5. Injection Budget Enforcement

The entire prompt injection section before rules and chunk text must respect the total context budget. If the 5-level injection would exceed 5% preliminary allocated budget, the following strategy is applied:

| Exceed Method | Action |
|---------------|--------|
| Minor overflow (<5% over) | Truncate last section (style) to fit |
| Moderate overflow (5-15% over) | Cut style → narrative → scene in that order; warn in metadata |
| Critical overflow (>15% over) | Use character + glossary only; skip scene/narrative/style; log as emergency mode |

---

## 6. Reference Documents

| Document | Role |
|----------|------|
| `RM_5_9_0_RUNTIME_INTEGRATION_ARCHITECTURE.md` | Parent architecture |
| `RM_5_9_0_CONTEXT_BUDGET_POLICY.md` | Token allocation policy |
| `RM_5_9_0_RUNTIME_SEQUENCE.md` | Sequence diagrams |
| `RM_5_9_0_RUNTIME_CACHE_POLICY.md` | Caching policy |
| `RM_5_2_PROMPT_FLOW.md` | Current production prompt assembly |
| `RM_5_2_CONTEXT_INVENTORY.md` | Current context inventory |

---

*This policy is FROZEN as of RM-5.9.0 (2026-08-06). All subsequent RM-5.9.x stages must obey this injection order.*