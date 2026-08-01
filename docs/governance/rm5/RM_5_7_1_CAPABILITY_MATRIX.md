# RM-5.7.1 Capability Matrix

**Baseline**: RM-5.7.0 Knowledge Generation Architecture Baseline  
**Version**: RM-5.7.1  
**Status**: Capability Audit Consolidation  
**Created**: 2026-08-02  
**Purpose**: Consolidated capability matrix across all 5 knowledge domains from individual audits.

---

## 1. Module Coverage Matrix

| Module | Character | Glossary | Scene | Narrative | Style | Lines of Code |
|--------|-----------|----------|-------|-----------|-------|---------------|
| character_memory_engine.py | ✅ Primary | — | — | — | — | 380 |
| character_memory_v2/ | ✅ Store v2 | — | ✅ Types | ✅ Types | — | ~5,500 |
| character_resolver.py | ✅ Runtime | — | — | — | — | 280 |
| character_database.py | ✅ Builder | — | — | — | — | 120 |
| glossary_builder.py | — | ✅ Primary | — | — | — | 480 |
| glossary.py | — | ✅ Runtime | — | — | — | 48 |
| knowledge_base_builder.py | ✅ Consumer | ✅ Consumer | — | — | — | 350 |
| context_scene_memory/ | — | — | ✅ Store v2 | ✅ Types | — | ~5,500 |
| context/scene_state.py | — | — | ❌ Legacy | — | — | 50 |
| translation_engine/context_intelligence.py | — | — | ✅ Runtime | ✅ Runtime | ✅ Runtime | 330 |
| translation_engine/prompt_intelligence.py | — | — | — | ✅ Runtime | ✅ Runtime | 190 |
| translation_naturalness/ | — | — | — | — | ✅ Guards | ~1,500 |
| translation_quality_integration_v72/ | ✅ Flags | ✅ Flags | ✅ Flags | ✅ Flags | ✅ Flags | ~1,500 |

---

## 2. Schema Coverage Matrix

| RM-5.7.0 Schema Field | Character v1.0 | Character v2 | Glossary Builder | Scene Memory v2 | Narrative (types) | Style (all) | Status |
|----------------------|----------------|--------------|------------------|-----------------|-------------------|-------------|--------|
| **Core Identity** |
| **Character** |
| canonical_name | ✅ | ✅ FACT | — | — | — | — | ✅ v2 |
| source_name | ✅ | ✅ evidence | — | — | — | — | ✅ v2 |
| aliases | ✅ list | ✅ FACT | — | — | — | — | ✅ v2 |
| role | ❌ | ✅ FACT | — | — | — | — | v2 only |
| traits | ❌ | ✅ FACT | — | — | — | — | v2 only |
| relationships | ❌ | ✅ FACT | — | — | — | — | v2 only |
| arc_summary | ❌ | ❌ | — | — | — | — | **Gap** |
| first_appearance | ❌ | ❌ | — | — | — | — | **Gap** |
| knowledge_tags | ❌ | ❌ | — | — | — | — | **Gap** |
| **Glossary** |
| canonical_translation | ✅ | — | ✅ | — | — | — | Builder |
| source_term | ✅ | — | ✅ | — | — | — | ✅ |
| domain_tags | ❌ | — | ❌ (category) | — | — | — | **Gap** |
| part_of_speech | ❌ | — | ❌ | — | — | — | **Gap** |
| context_rules | ❌ | — | ✅ basic | — | — | — | Builder |
| forbidden_forms | ❌ | — | ✅ | — | — | — | Builder |
| **Scene** |
| scene_id | — | — | — | ✅ SC-\\d+ | — | — | v2 only |
| title | — | — | — | ❌ | — | — | **Gap** |
| volume/chapter_range | — | — | — | ✅ chapter_id | — | — | v2 only |
| location | — | — | — | ✅ | — | — | v2 + legacy |
| time_of_day | — | — | — | ✅ time_state | — | — | v2 only |
| participants | — | — | — | ✅ SceneParticipant | — | — | v2 only |
| plot_points | — | — | — | ❌ | ✅ PlotPoint | — | Types only |
| summary | — | — | — | ❌ | ❌ | — | **Gap** |
| tone | — | — | — | ❌ | ❌ | — | **Gap** |
| unresolved_refs | — | — | — | ✅ | — | — | v2 only |
| **Narrative** |
| plot_points | — | — | — | ✅ types | ✅ types | — | Types only |
| timeline | — | — | — | ✅ types | ✅ types | — | Types only |
| world_rules | — | — | — | ✅ types | ✅ types | — | Types only |
| character_milestones | — | — | — | ❌ | ❌ | — | **Gap** |
| **Style** |
| style_fingerprint | — | — | — | — | — | ❌ | **Gap** |
| author_profile | — | — | — | — | — | ❌ | **Gap** |
| genre_profile | — | — | — | — | — | ❌ | **Gap** |
| register_rules | — | — | — | — | — | ❌ hardcoded | **Gap** |
| collocation_patterns | — | — | — | — | — | ❌ 7 fixed | **Gap** |
| positive_patterns | — | — | — | — | — | ❌ | **Gap** |

---

## 3. Extraction Pipeline Coverage Matrix

| Pipeline Stage | Character | Glossary | Scene | Narrative | Style |
|----------------|-----------|----------|-------|-----------|-------|
| **Source Ingestion** | ✅ Document Analyzer output | ✅ Document Analyzer output | ❌ None | ❌ None | ❌ None |
| **Extraction Agents** | ❌ None (merge only) | ❌ None (merge only) | ❌ None (store only) | ❌ None (types only) | ❌ None (guards only) |
---

## 4. Gap Consolidation (Critical/High Only)

| Domain | Gap ID | Description | Severity | Module |
|--------|--------|-------------|----------|--------|
| Character | CHAR-003 | No LLM-based extraction agent | Critical | All |
| Character | CHAR-001 | v1.0 lacks UUID, schema_version, timestamps | High | character_memory_engine |
| Character | CHAR-002 | v1.0 lacks fact-type granularity | High | character_memory_engine |
| Character | CHAR-004 | No segment-level evidence chain | High | character_memory_engine |
| Character | CHAR-005 | No validation engine (CH-001 to CH-005) | High | All |
| Character | CHAR-007 | v1.0 and v2 disconnected | High | Both stores |
| Glossary | GLOSS-003 | No LLM-based extraction agent | Critical | All |
| Glossary | GLOSS-001 | No UUID, schema_version, timestamps | High | glossary_builder |
| Glossary | GLOSS-002 | Single category; missing domain_tags, POS | High | glossary_builder |
| Glossary | GLOSS-004 | No segment-level evidence chain | High | glossary_builder |
| Glossary | GLOSS-005 | No validation engine (GL-001 to GL-005) | High | All |
| Glossary | GLOSS-007 | Runtime uses text file, not artifact | High | glossary.py |
| Scene | SCENE-002 | No LLM-based scene boundary detection | Critical | All |
| Scene | SCENE-001 | Missing title, summary, plot_points, tone | High | context_scene_memory |
| Scene | SCENE-003 | No participant/role extraction | High | All |
| Scene | SCENE-004 | Three disconnected modules | High | All 3 |
| Scene | SCENE-005 | No validation engine (NR-001 to NR-004) | High | All |
| Narrative | NARR-002 | No LLM-based plot point extraction | Critical | All |
| Narrative | NARR-003 | No timeline construction | Critical | All |
| Narrative | NARR-004 | No world rule extraction | Critical | All |
| Narrative | NARR-001 | Types defined but no narrative.schema.json | High | context_scene_memory |
| Narrative | NARR-005 | No character milestone tracking | High | All |
| Narrative | NARR-006 | No validation engine (NR-001 to NR-004) | High | All |
| Style | STYLE-001 | No style.schema.json; no artifacts | Critical | All |
| Style | STYLE-002 | No LLM-based style/profile extraction | Critical | All |
| Style | STYLE-003 | No author style fingerprinting | High | All |
| Style | STYLE-004 | No genre-specific style modeling | High | All |
| Style | STYLE-005 | Only defensive guards, no positive patterns | High | translation_naturalness |
| Style | STYLE-007 | No validation engine (ST-001 to ST-005) | High | All |
| Style | STYLE-008 | 6 disconnected runtime modules | Medium | All 6 |

**Total Gaps**: 30 (8 Critical, 18 High, 4 Medium)

---

## 5. Implementation Priority (RM-5.7.2+)

| Phase | Focus | Deliverables |
|-------|-------|--------------|
| **RM-5.7.2** | Schema & Extraction Agents | 5 schema.json files, 5 extractor agents (Character, Glossary, Scene, Narrative, Style) |
| **RM-5.7.3** | Validation & Review | 5 validation engines (CH/GL/NR/ST rules), review workflow |
| **RM-5.7.4** | Compilation & Runtime Switch | Unified artifact compilation, runtime config to load from knowledge/ |
| **RM-5.7.5** | Integration & Migration | v1.0→v2 migration, legacy module deprecation |

---

## 6. Validation

- Production Code Modified: **0** (audit only)
- Provider Requests: **0**
- Network Requests: **0**