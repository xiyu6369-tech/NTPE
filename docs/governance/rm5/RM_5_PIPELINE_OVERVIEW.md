# RM-5 Pipeline Overview

**Version**: RM-5.0  
**Purpose**: High-level pipeline architecture with insertion points for context, glossary, and character memory.

---

## Main Translation Flow

```
                        Input (Source Text)
                              │
                              ▼
                     ┌────────────────┐
                     │    Analyzer     │
                     │  (Chunk Engine) │
                     └───────┬────────┘
                             │ chunks
                             ▼
              ┌─────────────────────────────┐
              │        Prompt Builder       │
              │  (PromptEngine + Rules)     │
              │                             │
              │  Inputs:                    │
              │    • chunk text             │
              │    • context (sliding win)   │ ← Context Pipeline
              │    • glossary terms          │ ← Glossary Pipeline
              │    • novel profile           │
              │    • absolute rules          │
              └─────────────┬───────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │     Translation Engine      │
              │     (NvidiaEngine)          │
              └─────────────┬───────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │     Quality Evaluation      │
              │  (Validator + Rules)        │
              │                             │
              │  Checks:                    │
              │    • forbidden phrases      │
              │    • name correctness        │
              │    • Korean residue          │
              │    • length sanity            │
              │    • hallucination markers    │
              │    • glossary coverage        │ ← Glossary Enforcement
              └─────────────┬───────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │       Regression            │
              │  (post-process + format)    │
              │                             │
              │  • OpenCC s2twp              │
              │  • Glossary output fix       │
              │  • Format normalization      │
              │  • Source structure restore  │
              └─────────────┬───────────────┘
                            │
                            ▼
                         Output
```
---

## Pipeline Insertion Points

### 1. Context Pipeline

```
Insertion Point: Prompt Builder (before prompt assembly)

Current Implementation:
  context = last_translated_part[-context_size:]  # 650 chars sliding window

Gap:
  - No scene-level context awareness
  - No cross-volume context
  - No character-state-aware context selection

RM-5 Target:
  - Context selection based on scene/chapter boundaries
  - Scene memory integration
  - Cross-chunk narrative continuity
```

### 2. Glossary Pipeline

```
Insertion Point A: Prompt Builder (injection)
  → PromptEngine.build_translate_prompt(text, context, glossary)
  → glossary_text(glossary) → rendered into prompt block

Insertion Point B: Post-Translation (enforcement)
  → enforce_glossary_output(source, text, glossary) in rules.py
  → Glossary.check_required_terms(source, translated) in validator.py

Current state:
  - Runtime glossary: data/glossary.txt (flat key=value)
  - Build-time glossary: memory/glossary.json (structured, categorized)
  - Gap: runtime does not consume the structured glossary.json

RM-5 Target:
  - Runtime consumes memory/glossary.json
  - Category-aware glossary injection (abbreviation vs. proper_english_term)
  - Conflict resolution for overlapping terms
```

### 3. Character Memory Pipeline

```
Insertion Point: Prompt Builder (currently UNUSED in runtime)

Current state:
  - character_memory_engine.py builds character_memory.json offline
  - character_resolver.py resolves character aliases
  - Runtime prompt does NOT consume character memory

Gap:
  - Character names have no guaranteed consistency across chunks
  - No character-tone guidance per character
  - No dialogue attribution consistency

RM-5 Target:
  - Inject character memory into prompt context
  - Character-aware name resolution
  - Voice/tone consistency across chapters
```

---

## Pipeline Architecture Summary

```
┌─────────────────────────────────────────────────────────┐
│                    RM-5 Architecture                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐    ┌───────────┐    ┌──────────────┐     │
│  │ Input    │───►│ Analyzer  │───►│ Prompt       │     │
│  │ (source) │    │ (chunker) │    │ Builder      │     │
│  └──────────┘    └───────────┘    └──────┬───────┘     │
│                                          │             │
│                    ┌─────────────────────┤             │
│                    ▼                     ▼             │
│  ┌────────────────────┐    ┌─────────────────────┐     │
│  │ Glossary Pipeline  │    │ Character Memory   │     │
│  │ (terms + aliases)  │    │ (names + tones)    │     │
│  └────────────────────┘    └─────────────────────┘     │
│                                          │             │
│                                          ▼             │
│                    ┌─────────────────────────────┐     │
│                    │ Translation Engine          │     │
│                    │ (NvidiaEngine)              │     │
│                    └─────────────┬───────────────┘     │
│                                  │                     │
│                                  ▼                     │
│                    ┌─────────────────────────────┐     │
│                    │ Quality Evaluation          │     │
│                    └─────────────┬───────────────┘     │
│                                  │                     │
│                                  ▼                     │
│                    ┌─────────────────────────────┐     │
│                    │ Regression / Output         │     │
│                    └─────────────────────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

**Note**: All pipelines described here are frozen per RM-4.  
RM-5.x stages will propose modifications to each pipeline individually, anchored to this baseline.