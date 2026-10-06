# NTPE S11-11 — Current Capability Matrix

Companion to `artifacts/NTPE_S11_11_PROGRAM_AUDIT.md`.
Baseline: HEAD `1273190`, branch `main`. Supersedes `NPTE_S11_01_CAPABILITY_MATRIX.md`
(S11-01 baseline `1655b25`).

State codes: `A` production ready · `B` usable with documented limitation ·
`C` backend-only · `D` experimental/observational · `E` deferred · `G` legacy/archive.

Decision codes: `KEEP` · `INTEGRATE` · `REFACTOR` · `ARCHIVE` · `REMOVE` · `DEFER`.

## 1. Capability Matrix

| Capability | Current State | Evidence | Correctness | UX | Test Confidence | Decision |
|---|---|---|---|---|---|---|
| TXT translation | A | `lts/txt_translation_runtime.py`; reader flow E2E | PASS (no S11 change) | Real | Strong | KEEP |
| EPUB translation | B | S11-03/04, S11-06/07, S11-09/10; `core/epub_translation/*` | PASS — S11 chains CLOSED | Real (correctness clean) | Strong (contract + E2E) | KEEP |
| Project persistence | A | `core/reader_project/{store,manager,models}.py`; S11-10 restart read-back | PASS | Real (library/cards) | Strong | KEEP |
| Recovery | A | `core/reader_project/recovery.py`; S10-03 recovery E2E | PASS | Real (繼續翻譯) | Strong | KEEP |
| Output / artifact | B | `models.py:218`; `project_view_model.py:69-105` | PASS (availability recomputed at render) | Real | Strong | REFACTOR (optional, deferred) |
| Translation Studio | A | `ui/translation_studio/*`; S8 honesty reports | PASS | Real | UI wiring mocked by design; E2E partial | KEEP |
| Launcher | A | `ui/translation_studio`, `ui/translation_launcher` | PASS | Real | Via studio/runtime | KEEP |
| CLI | B (limited) | `cli/`; CLI workspace model ≠ ReaderProject | PASS | Partial (`translate`, internal cmds) | Tool suites | KEEP |
| Glossary | C / product NOT IMPLEMENTED | `glossary_path=None` at all UI call sites; no Project contract; no runtime wiring | N/A (not wired) | None | Builder/schema only | INTEGRATE or DEFER (product decision) |
| Character Memory | D (default-off) | `quality_character_memory_v72: bool = False` (4 option surfaces) | N/A | None | Library tests | DEFER |
| Context / Scene Memory | D (default-off) | `quality_context_scene_v72: bool = False` (4 surfaces) | N/A | None | Library tests | DEFER |
| Literary Quality | D (observational) | S7-14 blocker `NOT AUTHORIZED`; advisory QA only | N/A | None | Pilot/regression infra | DEFER (quality program) |
| QA / Validation | B (advisory) | `BasicTranslationQA` + `runtime_qa`; `core/validator.py`/Stage-15 not imported | PASS (advisory, non-blocking) | Indirect | Mixed | REFACTOR (maintenance) |
| Runtime architecture | A (canonical single route) | `runtime.py → manager.py → translation_engine.py → provider_runtime.py → nvidia_client.py` | PASS | n/a | Strong | KEEP |
| Frozen model | A | `meta/llama-3.2-90b-vision-instruct` (`core/config.py:19`, `lts/...:83`, `adapter.py:56`) | PASS | n/a | Strong | KEEP (no re-decision) |
| Security | A | `_validate_zip_security`; extraction/E2E security tests | PASS | n/a | Strong | KEEP |
| Testing architecture | B (debt) | broad suite pre-existing failures; Qt e2e session flaky | PASS with debt | n/a | Mixed | REFACTOR (test infra) |
| Legacy / orphan surface | G | `core/translator.py`, `engine/`, `core/validator.py`, `core/context/`, orphan dirs | N/A | None | Legacy tests | ARCHIVE (REMOVE later) |
| `core/translation_release` | G (parallel) + live models | delivery reached only via test-only `rm8_delivery_adapter`; `reader_structure.models` imported by canonical `reader_chapter_map.py:19` | N/A | None | env-sensitive | ARCHIVE candidate (split models first) |
| Orphan top-level dirs | G | no production imports | N/A | None | Legacy | ARCHIVE |

## 2. EPUB Detail (post-S11)

| Aspect | Status |
|---|---|
| Spine ordering (interspersed `linear="no"`) | CLOSED (S11-03/04/10) |
| Non-linear semantics | CLOSED (S11-06/07/10) |
| TOC fallback (nav/NCX, precedence, empty rejection) | CLOSED (S11-08/09/10) |
| Resource / href mapping | PASS |
| Final packaging + persisted artifact + fresh read-back | PASS |
| Original TOC structural fidelity (`toc_entries=()`) | LIMITATION (deferred enhancement) |
| Fixed-layout rendering | LIMITATION (detected/recorded only) |

## 3. Production Readiness

| Capability | Production Ready | Reader-facing | Persisted | Recovery-safe |
|---|---|---|---|---|
| TXT | YES | YES | YES | YES |
| EPUB | YES (correctness clean; documented limitations) | YES | YES | YES |
| Project | YES | YES | YES (schema v1 sufficient) | YES |
| Recovery | YES | YES | YES | YES |
| Output | YES (portability limitation) | YES | YES | YES |
| Studio / Launcher | YES | YES | via Project | YES |
| CLI | YES (limited surface) | Partial | CLI workspace | N/A |
| Glossary | NO | NO | Partial (backend) | N/A |
| Memory (Character/Context) | NO (default-off) | NO | gated | N/A |
| Literary Quality | NO (observational) | NO | evidence only | N/A |

## 4. Program Decision Summary

```text
S11 Program = COMPLETE (recommendation only; no s11-complete tag)
Active production correctness blockers = NONE
Remaining = limitations / deferred features / experimental / maintenance debt / test-infra debt / legacy
```

Next bounded workstreams (evidence-ranked): Glossary integration (needs product contract);
E2E test-infrastructure reliability; legacy/orphan archive (split `translation_release`);
output portability (if product requires); QA consolidation; S7 calibration (external data).
