# NTPE S13-08 — Archive Candidate Register

Companion to `artifacts/NTPE_S13_08_TOP_LEVEL_INVENTORY.md` and
`artifacts/NTPE_S13_08_ENTRY_POINT_AUDIT.md`. Baseline HEAD `02745cf`. Audit-only;
nothing removed or moved.

## Archive safety gates

```text
G1 production caller = 0
G2 canonical (collected) test dependency = 0
G3 active entry point = 0
G4 dynamic reference = 0
G5 tooling dependency = 0
G6 compatibility/public surface = none
```

Any unknown → `UNKNOWN / DEFERRED`; removal is not authorized.

## Register

| Candidate | Classification | Evidence | Gates | Blockers | Recommended next step |
|---|---|---|---|---|---|
| `compatibility/` | TEST-ONLY LEGACY | imported only by quarantined `tests/rc_stage_02/*`; no production/tooling/dynamic ref | G1✓ G2✗(quarantined legacy) G3✓ G4✓ G5✓ G6? | quarantine-only dependency; "quarantine ≠ removable" | DEFERRED — dedicated audit |
| `analysis/` | HISTORICAL / DATA ARTIFACT | `*_glossary_auto.json`; only comment mentions in `core/*` (legacy) | n/a (data, not code) | not a code-removal candidate | DEFERRED / out of scope |
| `benchmarks/` | KEEP — ACTIVE BENCHMARK INFRA | read by `tools/knowledge_benchmark/loader.py` (`benchmarks/golden`,`spec`,`results`) | G5✗ | active tooling dependency | KEEP |
| `profiles/` | HISTORICAL / DATA ARTIFACT | `passion_profile.json`; read only by dead `engine/pipeline/production_pipeline.py` | n/a (data) | not a code-removal candidate | DEFERRED / out of scope |
| `web/` | KEEP — SECONDARY (separate product) | Next.js reader app; no Python reference | n/a (separate product) | a product surface, not dead code | KEEP |
| `engine/` | LEGACY — ARCHIVE CANDIDATE | reached only via deferred `core/translator.py` + `tools/legacy_pipeline_launchers` | G1✗(dead caller chain) G2✓ G3✓ G4✓ G5✗(tools) | S13-06: `core/translator.py` historical HIGH_RISK | DEFERRED (S13-06) |
| `cli/` | LEGACY — ARCHIVE CANDIDATE | only quarantined `tests/beta_stage_06_*` import `cli.*`; `__main__` present; `core/enterprise` existence probe | G1✓ G2✗(quarantined) G3✗ G4✓ G5✗(probe) G6? | active-entry + tooling-probe + quarantine-only dep | DEFERRED — per-subsystem audit |
| `sdk/` | LEGACY — ARCHIVE CANDIDATE | imported only by quarantined `launcher_*` tests; plugin `import_module` surface | G1✓ G2✗(quarantined) G3✓ G4✗(manifest loader) G6? | dynamic plugin surface; quarantine-only dep | DEFERRED — per-subsystem audit |
| `integration/` | LEGACY — ARCHIVE CANDIDATE | imported only by quarantined `launcher_*` tests; `extension_loader.import_module` | G1✓ G2✗ G4✗ G6? | dynamic extension surface | DEFERRED |
| `workflow/` | LEGACY — ARCHIVE CANDIDATE | imported only by quarantined `launcher_*` tests; freeze manifests | G1✓ G2✗ G6? | quarantine-only dep; freeze contract | DEFERRED |
| `platform_services/` | LEGACY — ARCHIVE CANDIDATE | imported only by quarantined `launcher_*` tests | G1✓ G2✗ G6? | quarantine-only dep | DEFERRED |
| `external_api/` | LEGACY — ARCHIVE CANDIDATE | imported only by quarantined `beta_stage_12_*` tests | G1✓ G2✗ G6? | quarantine-only dep | DEFERRED |
| `runtime_api/` | LEGACY — ARCHIVE CANDIDATE | imported by mixed `launcher_*` tests | G1✓ G2✗ G6? | quarantine-only dep | DEFERRED |
| `web_ui/` | LEGACY — ARCHIVE CANDIDATE | imported only by quarantined `beta_stage_13_*` tests | G1✓ G2✗ G6? | quarantine-only dep | DEFERRED |
| `translation/` | LEGACY — ARCHIVE CANDIDATE | imported by `cli/commands/quality.py` + quarantined tests | G1✓ G2✗ G5✗(cli) G6? | cli + quarantine-only dep | DEFERRED |
| `benchmark/` | LEGACY — ARCHIVE CANDIDATE | imported only by quarantined `launcher_*` tests | G1✓ G2✗ G6? | quarantine-only dep | DEFERRED |
| `packaging/` | LEGACY — ARCHIVE CANDIDATE | imported by mixed `launcher_*` tests; has `__main__` | G1✓ G2✗ G3✗ G6? | active-entry + quarantine-only dep | DEFERRED |
| `performance/` | LEGACY — ARCHIVE CANDIDATE | imported only by quarantined `rc_stage_03` tests | G1✓ G2✗ G6? | quarantine-only dep | DEFERRED |
| `regression/` | LEGACY — ARCHIVE CANDIDATE | imported only by quarantined `rc_stage_01` tests | G1✓ G2✗ G6? | quarantine-only dep | DEFERRED |
| `release_candidate/` | LEGACY — ARCHIVE CANDIDATE | imported only by quarantined `rc_stage_05/06` tests | G1✓ G2✗ G6? | quarantine-only dep | DEFERRED |
| `stable_release/` | LEGACY — ARCHIVE CANDIDATE | imported by mixed `launcher_*` tests | G1✓ G2✗ G6? | quarantine-only dep | DEFERRED |
| `archive/` | HISTORICAL ARTIFACT | out-of-scope evidence/tests | n/a | intentional archive | KEEP (out of scope) |

## KEEP (no archive consideration)

| Candidate | Classification | Reason |
|---|---|---|
| `core/`, `lts/`, `ui/` | KEEP — CANONICAL | reader-facing runtime |
| `config/` | KEEP — SECONDARY | config data read by provider tools |
| `manifests/`, `schemas/`, `memory/` | KEEP — CANONICAL (data) | read by `core`/`lts` |
| `ntpe/` | KEEP — SECONDARY | public API; collected `tests/unit/public_api/*` |
| `verification/` | KEEP — ACTIVE TEST INFRA | collected contract/integration tests import it |
| `tools/`, `scripts/` | KEEP — ACTIVE TOOLING | dev/one-shot tooling |
| `tests/` | KEEP — ACTIVE TEST INFRA | canonical suite |
| `docs/`, `artifacts/`, dotdirs | KEEP — documentation/output/config | — |

## Archive-safe now

```text
NONE — no candidate satisfies all of G1..G6.
```

Every legacy framework has at least one unmet/unknown gate (quarantine-only test
dependency, an active entry point, a tooling/dynamic reference, or an unverified
public/compatibility surface). Per the no-guessing rule, none is authorized for removal.

## Unknown / deferred detail

- **Quarantine is not deletion proof.** `cli`, `sdk`, `integration`, `workflow`,
  `platform_services`, `external_api`, `runtime_api`, `web_ui`, `translation`, `benchmark`,
  `packaging`, `performance`, `regression`, `release_candidate`, `stable_release`, and
  `compatibility` are imported only by quarantined legacy suites, but each still needs a
  dedicated per-subsystem audit of its entry points, dynamic/registry surfaces, and
  public API before any archive decision.
- **Dynamic surfaces** (`sdk/plugin_loader.py`, `integration/extension_loader.py`) resolve
  caller-supplied module names → a generic compatibility surface (G6 unknown).
- **Tooling references**: `core/enterprise/deployment_foundation.py` probes `cli/` and
  `config/` existence; `tools/knowledge_benchmark/*` reads `benchmarks/`.
- **`engine/`** remains DEFERRED per S13-06 (depends on `core/translator.py`, which carries
  a historical HIGH_RISK flag).

## Non-regression

No CLOSED capability (Glossary, TXT, EPUB spine/non-linear/TOC/offset, persistence,
Recovery, Output, QA, Canonical runtime, Security) is reopened or redefined. No candidate
is a dependency of any CLOSED capability.
