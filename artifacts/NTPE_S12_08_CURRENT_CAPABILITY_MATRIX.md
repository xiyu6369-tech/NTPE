# NTPE S12-08 — Current Capability Matrix

Companion to `artifacts/NTPE_S12_08_PROGRAM_AUDIT.md`. Baseline HEAD `5ea85b4`,
branch `main`. Supersedes `NPTE_S11_11_CURRENT_CAPABILITY_MATRIX.md` (S11-11 baseline
`1273190`).

State legend: CLOSED = implemented + evidence-locked · PASS = capability healthy ·
LIMITATION = usable with documented non-correctness bound · DEBT = quality/maintenance ·
EXPERIMENTAL = default-off · DEFERRED = not scheduled · LEGACY = archive candidate.

| Capability | Current State | Correctness | UX | Persistence | Test Confidence | Remaining Gap | Decision |
|---|---|---|---|---|---|---|---|
| TXT | CLOSED | PASS | Real path, Open Result | ReaderProject + resume | Strong (unit/integration/E2E) | None for S12 MVP | KEEP |
| EPUB | CLOSED | PASS | Reader-first usable | Persisted artifact + read-back | Strong (S11/12 E2E, real adapter) | Original TOC fidelity; fixed-layout; launcher glossary-off (limitations) | KEEP |
| Project | CLOSED | PASS | Reader dashboard | schema v1, atomic, SHA-256 | Strong (reader_project 86) | Orphan/TTL cleanup absent | KEEP |
| Recovery | CLOSED | PASS | Recovery action | resume + glossary-hash gate | Strong (S10-03, S12-02/04) | None | KEEP |
| Output | LIMITATION | PASS (render-time) | Open Result/Folder | OutputRecord persisted | Strong (S10-03, S12-07) | Absolute-path portability; stale `available` (mitigated) | DEFER |
| Translation Studio | PASS | PASS | Real controls | Project-backed | UI wiring + E2E | None | KEEP |
| Launcher | PASS | PASS | Canonical route | N/A | wiring tests | Shell glossary-off (scope boundary) | KEEP |
| CLI | PASS (limited) | PASS | Internal + `translate` | N/A | CLI tests | Separate workspace model by design | KEEP |
| Glossary | CLOSED | PASS | Import/replace/detach panel | Project snapshot + hash | S12-02/03/04/06/07 | EPUB prompt parity; CSV (deferred) | KEEP |
| Character Memory | EXPERIMENTAL | N/A | none | runtime-referenced | feature-gated tests | default-off | DEFER |
| Context/Scene Memory | EXPERIMENTAL | N/A | none | runtime-referenced | feature-gated tests | default-off | DEFER |
| Literary Quality | DEFERRED | Observational | advisory only | report artifacts | S7 method closed | external evaluators + data missing | DEFER |
| QA | DEBT | advisory | none | N/A | QA tests | guard duplication; dead `core/validator.py`/Stage-15 | CONSOLIDATE |
| Runtime | PASS | PASS | N/A | N/A | broad | none | KEEP (frozen model) |
| Security | PASS | PASS | N/A | N/A | security tests | none | KEEP |
| Testing | PASS + DEBT | N/A | N/A | N/A | S12 real-adapter regressions added | Qt e2e session; legacy collection; stale expectations | RELIABILITY WORKSTREAM |
| Legacy | LEGACY | N/A | N/A | N/A | N/A | `engine/`, `core/translator.py`, orphan dirs; `translation_release` split first | ARCHIVE (not authorized) |

## Key current facts

- Frozen production model: `meta/llama-3.2-90b-vision-instruct`
  (`core/config.py:19`, `lts/txt_translation_runtime.py:83`,
  `core/epub_translation/runtime/adapter.py:56`).
- Single canonical runtime route; glossary adds no second runtime (no `glossary` import in
  `core/runtime_orchestrator`, `core/translation_engine`, `provider`).
- Glossary backward compatibility: `ReaderProject.glossary` defaults to `None`;
  `from_dict` tolerates a missing key (`models.py:310,334-343`).
- EPUB chunk offset contract: body = chapter-relative, extracted = absolute;
  validator enforces `body_range == extracted_range` (S12-06).
- Output availability recomputed at render from the filesystem
  (`ui/translation_studio/project_view_model.py:69-95`).

## Classification summary

```text
Correctness: TXT PASS · EPUB PASS · Project PASS · Recovery PASS · Runtime PASS · Security PASS
Limitations: Output portability · EPUB TOC fidelity · EPUB fixed-layout · launcher glossary-off
Feature/deferred: Glossary prompt parity + CSV · literary calibration
Experimental: Character / Context-Scene memory
Debt: QA consolidation · test infrastructure (Qt e2e, legacy collection, stale expectations)
Legacy: engine/ · core/translator.py · orphan dirs · translation_release (split first)
Blockers: NONE
```
