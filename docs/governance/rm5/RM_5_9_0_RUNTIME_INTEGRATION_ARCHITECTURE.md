# RM-5.9.0 Runtime Integration Architecture

**Version**: RM-5.9.0  
**Date**: 2026-08-06  
**Status**: 🔒 **FROZEN — Architecture Governance Only**  
**Dependencies**: RM-5.7.6 (Knowledge Layer Frozen), RM-5.8.6 (Benchmark Frozen)

---

## Purpose

This document defines the integration architecture between the frozen RM-5.7 Knowledge Layer and the existing Translation Runtime pipeline. It defines the complete runtime pipeline stages, their responsibilities, and the contract boundaries.

**No Runtime implementation is produced or modified by this stage.**

---

## 1. Architectural Context

### 1.1 What Exists Today (Frozen)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  RM-5.7.6 KNOWLEDGE LAYER (Frozen)   │  RM-4 TRANSLATION RUNTIME (Frozen│
│                                       │                                  │
│  KnowledgePackageProvider             │  TranslationEngine               │
│    get_character()                    │  PromptBuilder                    │
│    get_glossary()                     │  PromptRenderer                   │
│    get_scene()                        │  PackageBuilder                   │
│    get_narrative()                    │  ChunkEngine                      │
│    get_style()                        │  ProviderManager                  │
│    build_context()                    │  CharacterSelector                │
│    attach_to_prompt_package()         │  GlossarySelector                 │
│                                       │  ContextMemoryEngine              │
│  Frozen Package (v1/)                 │                                  │
│  characters.json / glossaries.json    │  Prompt injection today:          │
│  scenes.json / narrative.json         │    rules → characters → glossary   │
│  style.json / manifest.json           │    → voice → semantic → style     │
│                                       │    → novel → context → chunk       │
│  Read-only. Deterministic.            │                                  │
│  Self-verifying checksum.             │                                  │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.2 What RM-5.9.0 Introduces (Architecture Only)

RM-5.9.0 inserts a **Knowledge Integration Layer** between the Knowledge Layer and the Translation Runtime:

```
┌──────────────────────────────────────────────────────────────────────────┐
│    FROZEN PACKAGE (artifacts/knowledge_packages/v1/)                     │
│         │                                                                 │
│         ▼                                                                 │
│    KnowledgePackageProvider (FROZEN — read-only interface)                │
│         │                                                                 │
│         ▼                                                                 │
│  ╔══════════════════════════════════════════════════════════════════════╗ │
│  ║              KNOWLEDGE INTEGRATION LAYER (RM-5.9.0 NEW)              ║ │
│  ║                                                                      ║ │
│  ║  ┌─────────────────────┐    ┌──────────────────────────────────┐    ║ │
│  ║  │ Knowledge Retriever   │    │ PromptInjector                   │    ║ │
│  ║  │ (domain-aware query  │    │ (injection order enforcement    │    ║ │
│  ║  │  with budget cap)    │◄───│  with context budget per domain)│    ║ │
│  ║  └──────────┬──────────┘    └───────────────┬──────────────────┘    ║ │
│  ║             │                               │                        ║ │
│  ║             ▼                               ▼                        ║ │
│  ║    CacheProvider (per-session read-only; invalidates on reload)      ║ │
│  ║      chapter_scope + volume_scope cache policies                     ║ │
│  ╚══════════════════════════════════════════════════════════════════════╝ │
│         │                                                                 │
│         ▼                                                                 │
│    Translation Runtime (Frozen) — Receives enriched prompt package        │
│         │                                                                 │
│         ▼                                                                 │
│    Provider (NVIDIA API) — Translation as today                            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Runtime Pipeline Architecture

### 2.1 Complete Pipeline (View North to South)

```
Document Input
    │
    ▼
┌───────────────────┐
│  CHUNK GENERATOR  │
│  Responsibility:  │
│  Split novel text │
│  into translatable│
│  chunks           │
│  Output: Chunk[]  │
└────────┬──────────┘
         │
         ▼
┌───────────────────────┐
│   DOCUMENT ANALYZER   │
│ Responsibility:       │
│ Detect chunk context: │
│   chapter_id, scene   │
│   boundaries, volume, │
│   character mentions  │
│ Output: ChunkProfile  │
└────────┬──────────────┘
         │
         ▼
┌──────────────────────────┐
│ KNOWLEDGE PACKAGE        │
│ PROVIDER                 │
│ Responsibility:          │
│ Load frozen package      │
│ Verify checksum          │
│ Provide typed entity     │
│ access (5 domains)       │
│ Output: Verified package │
│         handle           │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ KNOWLEDGE RETRIEVER      │
│ Responsibility:          │
│ Query relevant entities  │
│ per chunk's profile      │
│ Apply retrieval policy   │
│ Respect context budget   │
│ Output: KnowledgeContext │
│ {character,glossary,     │
│  scene,narrative,style}  │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ PROMPT BUILDER           │
│ Responsibility:          │
│ Compose full prompt with │
│ injection order enforced │
│ Respect context budget   │
│ Output: PromptPackage│
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ TRANSLATION PROVIDER     │
│ Responsibility:          │
│ Execute translation      │
│ using NVIDIA API         │
│ Output: TranslationResult│
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ TRANSLATION RESULT       │
│ Collects per-chunk result│
│ Aggregates merged output │
└──────────────────────────┘
```

### 2.2 Stage Responsibilities

#### Stage 1 — Chunk Generator

| Aspect | Specification |
|--------|--------------|
| **Location** | Frozen: `engine/pipeline/chunk_engine.py` (RM-4) |
| **Input** | Source TXT file (UTF-8) |
| **Algorithm** | `\n\n` paragraph splitting with configurable `chunk_size` from speed profile |
| **Output** | `list[Chunk]` where each Chunk = {index, text, char_count} |
| **RM-5.9.0 Role** | **Unchanged** — provides entry point to the pipeline; knowledge retrieval consumes Chunk boundaries |
| **Modifications** | ❌ NONE |

#### Stage 2 — Document Analyzer

| Aspect | Specification |
|--------|--------------|
| **Location** | Future: `core/knowledge_runtime/document_analyzer.py` |
| **Input** | `Chunk.text` |
| **Responsibilities** | 1. Extract `chapter_id` and `volume_id` from chunk metadata<br>2. Identify character mentions by name matching against known character registry<br>3. Detect scene boundaries (e.g., horizontal rule markers like `* * *`)<br>4. Classify chunk text type (narration / dialogue / mixed) |
| **Output** | `ChunkProfile` = {chapter_id, volume_id, mentioned_characters: list[entity_id], scene_id, text_type, token_estimate} |
| **RM-5.9.0 Constraints** | Must be a **read-only observation** layer — no writes, no mutations, no provider calls |
| **Implementation** | **Not in RM-5.9.0** (stub provide only; real implementation in RM-5.9.1+) |
| **Modifications** | NONE in RM-5.9.0 |

#### Stage 3 — Knowledge Package Provider

| Aspect | Specification |
|--------|--------------|
| **Location** | Frozen: `core/knowledge/compatibility/provider.py` |
| **Interface** | `KnowledgePackageProvider` — 18 read-only methods |
| **Responsibilities** | Load frozen package (characters.json, glossary.json, scenes.json, narrative.json, style.json)<br>Verify SHA-256 checksum against manifest<br>Provide typed entity access (`get_character`, `get_glossary`, `get_scene`, `get_narrative`, `get_style`)<br>Build context (`build_context(entity_types)`) |
| **RM-5.9.0 Role** | **Used as-is** — the integration layer consumes this interface directly |
| **Modifications** | NONE |

#### Stage 4 — Knowledge Retriever

| Aspect | Specification |
|--------|--------------|
| **Location** | Future: `core/knowledge_runtime/retriever.py` |
| **Input** | `ChunkProfile` from Document Analyzer + `KnowledgePackageProvider` handle |
| **Responsibilities** | 1. For each of 5 knowledge domains, execute the retrieval policy<br>2. Match characters in chunk to character entities in package<br>3. Match glossary terms in chunk to glossary entities<br>4. Resolve scene entities by chapter_id + scene_id<br>5. Select current narrative context (plot points, timeline, etc.)<br>6. Retrieve applicable style profile<br>7. Ensure total retrieval stays within context budget |
| **Output** | `KnowledgeContext` = {characters: [entity], glossary: [entity], scenes: [entity], narrative: [entity], style: [entity]} |
| **Implementation** | **Not in RM-5.9.0** (stub architecture only) |
| Modifications | Runtime NONE in RM-5.9.0 |

#### Stage 5 — Prompt Builder

| Aspect | Specification |
|--------|--------------|
| **Location** | Future: `core/knowledge_runtime/prompt_builder.py` (extending existing `Prompter`) |
| **Input** | `KnowledgeContext` + `Chunk.text` + existing production prompt pipeline output |
| **Responsibilities** | 1. Compose knowledge into prompt sections following injection policy<br>2. Apply context budget per domain (truncation strategy)<br>3. Serialize knowledge injections into prompt strings<br>4. Produce final `PromptPackage` compatible with existing TranslationEngine |
| **Output** | `PromptPackage` (extended) with knowledge sections injected |
| **Implementation** | **Not in RM-5.9.0** (architecture only) |
| Modifications | None |

#### Stage 6 — Translation Provider

| Aspect | Specification |
|--------|--------------|
| **Location** | Frozen: `core/translation_engine/translation_engine.py` |
| **Role** | Receives `PromptPackage` → translates via NVIDIA API |
| **Modifications** | NONE — PromptPackage format unchanged; translation receives enriched context through existing prompt channels |
| **Keyguard** | Knowledge injection does NOT introduce new provider calls |

#### Stage 7 — Translation Result

| Aspect | Specification |
|--------|--------------|
| **Location** | Frozen: `lts/txt_translation_runtime.py` ending |
| **Role** | Collects per-chunk results, aggregates final output |
| Modifications | NONE |

---

## 3. Integration Surface (Contract Definitions)

### 3.1 Knowledge Package Provider Contract (from RM-5.7.6)

```python
# FROZEN contract — do not modify
class KnowledgePackageProvider:
    def get_character(entity_id, name) -> List[Dict]
    def get_glossary(entity_id, name) -> List[Dict]
    def get_scene(entity_id, name) -> List[Dict]
    def get_narrative(entity_id, name) -> List[Dict]
    def get_style(entity_id, name) -> List[Dict]
    def get_entities(entity_type, entity_id, name) -> List[Dict]
    def get_package_info() -> Dict
    def get_entity_types() -> List[str]
    def get_entity_count(entity_type) -> int
    def total_entity_count() -> int
    def verify() -> bool
    def is_verified() -> bool
    def build_context(entity_types) -> Dict
    def attach_to_prompt_package(prompt_package) -> Dict
```

### 3.2 KnowledgeRetriever — Contract (New Architecture)

```python
class KnowledgeRetriever:
    def retrieve(chunk_profile: ChunkProfile,
                 provider: KnowledgePackageProvider,
                 budget: ContextBudget) -> KnowledgeContext:
        """Retrieve relevant knowledge for one chunk according to retrieval and budget policies.
        Returns a KnowledgeContext that fits within the total context budget."""
```

### 3.3 PromptInjector — Contract (New Architecture)

```python
class PromptInjector:
    def inject_knowledge_context(knowledge_context: KnowledgeContext,
                                budget: ContextBudget,
                                injection_policy: InjectionPolicy) -> str:
        """Serialize all knowledge context into injectable prompt sections according to injection ordering and token budget.

        Returns a single string that can be prepended to the existing user_prompt."""
```

### 3.4 ContextBudget — Contract (New Architecture)

```python
@dataclass(frozen=True)
class ContextBudget:
    total_budget: int              # = total_prompt_tokens
    domain_allocations: dict[str, int]  # per-domain allocation
    reserved_tokens: int           # source text + system prompt + rules
    overflow_strategy: OverflowStrategy
```

### 3.5 Overflow Strategy

```python
class OverflowStrategy:
    """Specifiers how tokens overflowing the budget for a domain are handled."""
    TRUNCATE_FROM_TAIL    # Keep first N entries, drop last
    PRIORITIZE_CONFIDENCE  # Keep highest-confidence entries
    SUMMARIZE_TOP          # Summarize overflow entries in 1-2 sentences
    DROP_DOMAIN            # Drop entire domain if overflown
```

---

## 4. Domain Instantiation

Each knowledge domain has a distinct instantiation in the KnowledgeContext:

| Domain | Context Key | Entity Count Limit | Entity Type |
|--------|------------|--------------------|-------------|
| Character | `context.characters` | ≤ 8 | Character with attributes |
| Glossary | `context.glossary` | ≤ 12 | GlossaryEntry with canonical_translation |
| Scene | `context.scene` | ≤ 2 | Scene with location, participants, summary |
| Narrative | `context.narrative` | ≤ 5 (plot points) | PlotPoint, Timeline entries |
| Style | `context.style` | ≤ 3 (rules) | StyleRule with category + rule content |

---

## 5. Boundary Enforcement

| Boundary | Description | Enforcer |
|----------|------------|----------|
| Knowledge Layer ⇏ Integration Layer | KnowledgePackageProvider is read-only; Integration Layer never writes to packages | Static analysis + RuntimeBoundary test |
| Integration Layer ⇏ Runtime | PromptInjector produces plain strings, never modifies runtime code paths | Architecture policy |
| Provider = 0 | No NVIDIA API calls from knowledge retrieval or injection | Production guard |
| Runtime Modified = 0 | No production Python files changed in RM-5.9.0 | Git diff check |

---

## 6. Architecture Validation

### 6.1 Design Principles Conformance

| Principle | Conformance | Evidence |
|-----------|------------|----------|
| **Translation Quality First** | Knowledge retrieval improves character / glossary / scene / narrative consistency | Exact metrics from RM-5.9.x future runs; architecture tuned for quality insertion |
| **Architecture Simplicity** | Single knowledge integration layer; no new parallel pipelines | Pipeline design in this document |
| **Frozen Compatibility** | Zero modifications to any frozen .py file | `git diff --check` |
| **Evidence Driven** | Architecture design informed by RM-5.7 capability audits, RM-5 token budget analysis | All inflation governance documents reference original audits |
| **Incremental Delivery** | RM-5.9.0 is architecture only, no implementation | This document (plus 5 policy/sequence/report docs) |

### 6.2 Verification Commands

| Check | Command | Expected Result |
|-------|---------|-----------------|
| No production code modified | `git diff --check` | Clean |
| No runtime modified | `git diff --name-only` | Only new docs under `docs/governance/rm5/` |
| compileall check | `python -m compileall docs/governance/rm5/` | Pass (no .py files) |
| ntpe_validate | `python ntpe_validate.py` | ALL PASS |
| Provider Requests | — | 0 |
| Network Requests | — | 0 |

---

## 7. Reference Documents

| Document | Role |
|----------|------|
| `RM_5_7_6_ARCHITECTURE_BASELINE.md` | Frozen knowledge layer architecture |
| `RM_5_7_6_RUNTIME_BOUNDARY_REPORT.md` | Provider boundary audit |
| `RM_5_8_6_ARCHITECTURE_BASELINE.md` | Frozen benchmark architecture |
| `RM_5_8_6_RUNTIME_BOUNDARY_REPORT.md` | Benchmark boundary audit |
| `RM_5_1_RUNTIME_FLOW_MAP.md` | Production translation flow |
| `RM_5_2_PROMPT_FLOW.md` | Prompt assembly flow |
| `RM_5_2_CONTEXT_INVENTORY.md` | Current context inventory (13 levels) |
| `RM_5_4_TOKEN_BUDGET_ANALYSIS.md` | Token budget |
| `RM_5_DESIGN_PRINCIPLES.md` | Governance principles |
| `RM_5_9_0_PROMPT_INJECTION_POLICY.md` | Injection ordering |
| `RM_5_9_0_CONTEXT_BUDGET_POLICY.md` | Token allocation |
| `RM_5_9_0_RUNTIME_SEQUENCE.md` | Sequence diagrams |
| `RM_5_9_0_RUNTIME_CACHE_POLICY.md` | Caching policy |
| `RM_5_9_0_EXECUTION_REPORT.md` | Validation report |

---

*This architecture is FROZEN as of RM-5.9.0 (2026-08-06). All subsequent stages must Extend only into this architecture.*