# RM-5.9.0 Runtime Sequence

**Version**: RM-5.9.0  
**Date**: 2026-08-06  
**Status**: 🔒 **FROZEN — Governance Sequence Specification**

---

## Purpose

Specify all knowledge runtime interaction sequences for translation operations. Each sequence diagram describes the exact order and participants of each interaction in the integrated Knowledge + Translation pipeline.

---

## 1. Sequence 1: Initial Translation (Session Start)

### 1.1 When Applied

First chunk of a new translation session. No cache, no pre-loaded package. Entire knowledge pipeline initializes from scratch.

### 1.2 Sequence

```
Client        ChunkEngine    DocAnalyzer    PackageProvider    CacheProvider    Retriever    PromptInjector   Provider
  │               │               │                  │                 │               │               │             │
  │──translate───►│               │                  │                 │               │               │             │
  │               │───chunk──►   │                  │                 │               │               │             │
  │               │               │───profile────────►                │               │               │             │
  │               │               │                  │                 │               │               │             │
  │               │               │                  │◄──load_pkg()───│               │               │             │
  │               │               │                  │────pkg_ok────► │               │               │             │
  │               │               │                  │                │               │               │             │
  │               │               │                  │                │───cache me───│               │             │
  │               │               │                  │                │◄──store_ok───│               │             │
  │               │               │                  │                                 │               │             │
  │               │               │───retrieve(chunk_profile, provider, budget)────►│               │             │
  │               │               │                  │                                 │               │             │
  │               │               │                  │     query character, glossary    │               │             │
  │               │               │                  │◄────────────────────────────────│               │             │
  │               │               │                  │────────────────────────────────►│               │             │
  │               │               │                  │     query scene, narrative       │               │             │
  │               │               │                  │◄────────────────────────────────│               │             │
  │               │               │                  │────────────────────────────────►│               │             │
  │               │               │                  │                                 │               │             │
  │               │               │                  │◄──KnowledgeContext──────────────│               │             │
  │               │               │                  │                                 │               │             │
  │               │               │────inject(KnowledgeContext, budget, policy)──────────────────────►│             │
  │               │               │                  │                                                   │             │
  │               │               │                  │         Compose injection sections                │             │
  │               │               │                  │         per Injection Policy:                     │             │
  │               │               │                  │         system → char → glossary → scene          │             │
  │               │               │                  │         → narrative → style → rules → chunk      │             │
  │               │               │                  │                                                   │             │
  │               │               │◄──────────────injected_prompt_package────────────────────────────────│             │
  │               │               │                  │                                                   │             │
  │               │───────────────│──────────────────│───────────────────────────────────────────────────│───translate()──►│
  │               │               │                  │                                                   │                  │
  │               │               │                  │                                                   │    NVIDIA API    │
  │               │               │                  │                                                   │◄─────────────────│
  │               │               │                  │                                                   │                  │
  │               │               │◄─────────────────────────────────────────────────────────────────────│────translation──│
  │               │               │                                                                                       │
  │               │───result──────│                                                                                       │
  │               │               │                                                                                       │
  │◄──────────────│               │                                                                                       │
```

### 1.3 Steps Explanation

| Step | Action | Participant | Duration |
|------|--------|-------------|----------|
| 1 | Session initiates translation | SessionManager | — |
| 2 | ChunkEngine splits source into chunks | ChunkEngine | < 1ms |
| 3 | DocumentAnalyzer profiles chunk (chapter, characters, scene bounds) | DocAnalyzer | ~ 2ms |
| 4 | PackageProvider loads frozen package + verifies checksum | PackageProvider | < 50ms (first load) |
| 5 | CacheProvider stores verified package in session cache | CacheProvider | < 1ms |
| 6 | KnowledgeRetriever queries all 5 domains: character by IDs → glossary by text match → scene by chapter_id → narrative by timeline → style by genre | Retriever | < 10ms |
| 7 | PromptInjector receives KnowledgeContext → builds injection sections → serializes into PromptPackage compatible format | PromptInjector | < 5ms |
| 8 | TranslationEngine receives enriched PromptPackage → sends to NVIDIA API | Frozen RM-4 pipeline | Provider dependent |
| 9 | Translation result returned | Frozen RM-4 pipeline | Provider dependent |

**Critical**: Steps 1-7 are **offline / local compute only**. No network calls, no provider API calls. Only step 8 hits NVIDIA.

---

## 2. Continuous Translation Sequence (Chunk N > 1)

### 2.1 When Applied

For every chunk after the first chunk in a session. Cache is hot. Package is loaded. Most knowledge is incremental.

### 2.2 Sequence

```
ChunkProducer   DocAnalyzer    PackageProvider     CacheProvider       Retriever          PromptInjector
    │               │                  │                    │                   │                    │
    │───chunk─►     │                  │                    │                   │                    │
    │               │───profile──►     │                    │                   │                    │
    │               │                  │                    │                   │                    │
    │               │                  │ (skip load — cache is hot)              │                    │
    │               │                  │                    │                   │                    │
    │               │                  │Signify: reuse cached package             │                    │
    │               │                  │                    │                   │                    │
    │               │              retrieve(chunk_profile, cached_provider, budget)──►               │
    │               │                  │                    │                   │                    │
    │               │                  │   CASE: same chapter → reuse scene, narrative               │
    │               │                  │   CASE: new chapter → refresh Scene, Narrative              │
    │               │                  │                    │                   │                    │
    │               │                  │   query character:       │ (same chapter same chars)        │
    │               │                  │   query character: exact same as previous ──►                │
    │               │                  │   query character: returns above──►                        │
    │               │                  │                    │                   │                    │
    │               │                  │   query glossary terms from chunk text (any), ──►          │
    │               │                  │   query: returns cache hit for glossary terms               │
    │               │                  │                    │                   │                    │
    │               │                  │   query scene by chapter_id (same chapter_id?), ──►        │
    │               │                  │   same chapter = reused from session cache                 │
    │               │                  │                    │                   │                    │
    │               │                  │   query narrative for chapter ──►same chapter?              │
    │               │                  │   scenario: not checked until new chapter                   │
    │               │                  │                    │                   │                    │
    │               │                  │◄────KnowledgeContext (possibly same scene, same chars)──    │
    │               │                  │                    │                   │                    │
    │               │                  │                    │                   │                    │
    │               │                  │Inject(KnowledgeContext, budget, policy)─────────────────────►
    │               │                  │                    │                   │                    │
    │               │              ◄──injected_prompt (reuses same context if same chapter)          │
```

### 2.3 Step-Specific Logic

| Step | Logic |
|------|-------|
| Load Package | Package is already loaded in session cache → skip verification |
| Character retrieval | Same chapter → character IDs unchanged → reuse previous query results |
| Glossary retrieval | Query by chunk text → may return 0-3 new terms not seen before |
| Scene retrieval | Same chapter ID → reuse previous scene result, unless chapter boundary detected |
| Narrative retrieval | Same chapter → reuse narrative (plot doesn't change mid-chapter) |
| Prompt injection | Same structure but possibly fewer injected sections (glossary terms only new ones) |

**Lazy invalidation**: Scene and Narrative are refreshed only when a chapter boundary or scene boundary is crossed. Within the same chapter+scene, they are cached without re-fetch.

---

## 3. Package Refresh Sequence

### 3.1 When Applied

- User switches to a new volume while in session
- Knowledge packagebuild is re-run externally (external tool updated artifacts/) 
- System detects manifest checksum change

### 3.2 Sequence

```
SessionManager      PackProvider        CacheProvider         Retriever          PromptInjector        Provider
  │                     │                     │                     │                     │                    │
  │──refresh_pkg()──►   │                     │                     │                     │                    │
  │                     │                     │                     │                     │                    │
  │                     │───load new package──│                     │                     │                    │
  │                     │                     │                     │                     │                    │
  │                     │                     │─manifest check─     │                     │                    │
  │                     │                     │ SHA-256 checksum    │                     │                    │
  │                     │                     │─────ok─────────────►│                     │                    │
  │                     │                     │                     │                     │                    │
  │                     │                     │─────invalidate_all───►                     │                    │
  │                     │                     │                     │ clear byteacters     │                    │
  │                     │                     │                     │ clear glossary cache   │                    │
  │                     │                     │                     │ clear scene cache      │                    │
  │                     │                     │                     │ clear narrative cache  │                    │
  │                     │                     │                     │ clear style cache      │                    │
  │                     │                     │                     │                       │                    │
  │                     │                     │◄────cache_empty─────│                       │                    │
  │                     │                     │                     │                       │                    │
  │                     │──update_provider()──│                     │                       │                    │
  │                     │ (new package loaded) │                     │                       │                    │
  │                     │                     │                     │                       │                    │
  │◄──ready─────────────│                     │                     │                       │                    │
  │                     │                     │                     │                       │                    │
  │                     │                     │    Then: next chunk behaves as "Initial Translation"  │
```

### 3.3 Steps

| Step | Action | Description |
|------|--------|-------------|
| 1 | Load new package | Re-call `KnowledgePackageProvider` constructor with new package path |
| 2 | Verify checksum | Manifest checksum verified (SHA-256) |
| 3 | Invalidate cache | All 5 domain caches cleared (character, glossary, scene, narrative, style) |
| 4 | Update provider reference | Cache machine resets to new provider handle |
| 5 | Continue | The next chunk request starts over the Initial Translation path |

### 3.4 ConceptState

After package refresh, the session is indistinguishable from a fresh first-chunk session in terms of knowledge retrieval. The *translation state* (what has already been translated) persists from before, but the *knowledge state* (package, cache, entity queries) is fresh.

---

## 4. Chapter Switching Sequence

### 4.1 When Applied

- The Document Analyzer detects a chapter boundary (`chapter_id` changes between two adjacent chunks)

### 4.2 Sequence

```
Source           DocAnalyzer        Provider            CacheProvider
  │                  │                    │                   │
  │── chunk_N ──►    │                    │                   │
  │                  │ detect chapter_id change               │
  │                  │ (current: B vs previous: A)            │
  │                  │                    │                   │
  │                  │───chapter_changed(A→B)──►              │
  │                  │                    │                   │
  │                  │                   notify CacheScopicInvalidate(schema)
  │                  │                    │                   │
  │                  │                    │──invalidate scene────►
  │                  │                    │   invalidate narrative► 
  │                  │                    │                    │ (character+glossary unchanged)
  │                  │                    │                    │
  │                  │                    │◄──done─────────────│
  │                  │                    │                   │
  │                  │                   update: chapter_id=B
  │                  │                    │                   │
  │                  │ retrieve for new chapter ──►           │
```

### 4.3 Cache Scope

| Domain | Chapter Switch Behavior |
|--------|------------------------|
| Character | Not invalidated (characters persistent across chapters) |
| Glossary | Not invalidated (glossary persistent across chapters) |
| Scene | Invalidated — new chapter → new scene stack |
| Narrative | Invalidated — new chapter → new narrative context |
| Style | Not invalidated (style is per-volume, not per-chapter) |

**Rationale**: Character registry and glossary terms span the entire novel. Only scene and narrative are chapter-bound context.

---

## 5. Volume Switch Sequence

### 5.1 When Applied

- Volume switch detected (e.g., Vol 1 → Vol 2)
- Manual user action (--volume switch)

### 5.2 Sequence

Same as Package Refresh Sequence (full cache invalidation). Volume switch is **indistinguishable** from a package reload.

### 5.3 Scope

All 5 domain caches are invalidated. The provider loads a new package for the new volume.

---

## 6. Sequence Constraints

| Constraint | Applies To | Rationale |
|------------|------------|-----------|
| All local (locally only) | All sequences | No network, no provider, no API — pure local compute |
| Read-only throughout | All sequences | Never write to package directory, never modify provider |
| O(N) query | Retriever | Query complexity linear to entity count |
| atomic cache | CacheProvider | Invalidation atomically resets all caches before next query |
| deterministic | PromptInjector | Same input → same injected prompt (no random variation) |

---

## 7. Reference Documents

| Document | Role |
|----------|------|
| `RM_5_9_0_RUNTIME_INTEGRATION_ARCHITECTURE.md` | Parent architecture |
| `RM_5_9_0_PROMPT_INJECTION_POLICY.md` | Injection order policy |
| `RM_5_9_0_CONTEXT_BUDGET_POLICY.md` | Token allocation policy |
| `RM_5_9_0_RUNTIME_CACHE_POLICY.md` | Caching policy |
| `RM_5_1_RUNTIME_FLOW_MAP.md` | Current production sequence |

---

*This sequence specification is FROZEN as of RM-5.9.0 (2026-08-06).*