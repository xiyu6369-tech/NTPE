# NTPE S13-09 — Archive Decision (Batch A)

Companion to `artifacts/NTPE_S13_09_LEGACY_FRAMEWORK_BATCH_A_AUDIT.md` and `artifacts/NTPE_S13_09_DYNAMIC_SURFACE_REGISTER.md`. Baseline HEAD `1dd6bf3`.

## Archive Safety Gates (G1–G6)

| Gate | Requirement |
|---|---|
| G1 | production caller = 0 |
| G2 | canonical (collected) test dependency = 0 |
| G2a | legacy/quarantined test dependency = 0 (or explicitly documented) |
| G3 | active entry point = 0 |
| G4 | dynamic reference = 0 |
| G5 | tooling dependency = 0 |
| G6 | compatibility/public surface = none (or explicitly documented) |

**Any unknown → UNKNOWN / DEFERRED**. Removal not authorized if any gate is unknown or fails.

---

## Subsystem Archive Decisions

### 1. `compatibility/`

| Gate | Status | Evidence |
|---|---|---|
| G1 production caller | ✅ 0 | No canonical production imports |
| G2 canonical test dep | ✅ 0 | All importers in `tests/rc_stage_02/*` (quarantined) |
| G2a legacy test dep | ❌ 4 files | `tests/rc_stage_02/*` (quarantined by `rc_stage_*`) |
| G3 active entry point | ✅ 0 | No `__main__`, no `if __name__`, no console scripts |
| G4 dynamic reference | ✅ 0 | No `importlib`, `__import__`, etc. |
| G5 tooling dependency | ✅ 0 | No tooling references |
| G6 public surface | ❌ Yes | `__init__.py` exports 8 public symbols |

**Classification**: **TEST-ONLY LEGACY** — G2a fails (legacy quarantined test dep). G6 fails (public surface exists). **Not archive-safe.**

**Next step**: DEFERRED — requires explicit decision on compatibility audit surface and quarantined test cleanup.

---

### 2. `cli/`

| Gate | Status | Evidence |
|---|---|---|
| G1 production caller | ✅ 0 | No canonical production imports |
| G2 canonical test dep | ✅ 0 | All importers in `tests/beta_stage_06_*` (quarantined) |
| G2a legacy test dep | ❌ 11 files | `tests/beta_stage_06_*` (quarantined by `beta_stage_*` and `launcher_*_test.py`) |
| G3 active entry point | ❌ Yes | `cli/__main__.py` → `raise SystemExit(main())`; `cli/main.py:159` `if __name__ == "__main__"` |
| G4 dynamic reference | ✅ 0 | No dynamic imports |
| G5 tooling dependency | ❌ Yes | `core/enterprise/deployment_foundation.py` probes `cli/` existence |
| G6 public surface | ❌ Yes | `__init__.py` exports 8 symbols; internal `cli/freeze/compatibility.py` uses `cli.main` |

**Classification**: **LEGACY** — G3 fails (active entry point), G2a fails (legacy test deps), G5 fails (tooling probe), G6 fails (public surface).

**Next step**: DEFERRED — entry point is legacy (canonical CLI is `ntpe_production_translate.py`), but existence probe and public surface require explicit decision.

---

### 3. `runtime_api/`

| Gate | Status | Evidence |
|---|---|---|
| G1 production caller | ✅ 0 | No canonical production imports. Indirect via `external_api/` → `web_ui/` (separate product). |
| G2 canonical test dep | ✅ 0 | All importers in `tests/beta_stage_11_*`, `beta_stage_12_*` (quarantined) |
| G2a legacy test dep | ❌ 20+ files | All in quarantined `beta_stage_11_*`, `beta_stage_12_*` |
| G3 active entry point | ✅ 0 | No `__main__`, no `if __name__`, no console scripts |
| G4 dynamic reference | ✅ 0 | No dynamic imports |
| G5 tooling dependency | ✅ 0 | No tooling references |
| G6 public surface | ❌ Yes | Extensive `__init__.py` exports (50+ symbols) |

**Classification**: **LEGACY** — G2a fails (legacy test deps), G6 fails (public surface). Indirect use by `external_api/` → `web_ui/` (separate product).

**Next step**: DEFERRED — requires decision on `external_api/` / `web_ui/` product surface.

---

### 4. `integration/`

| Gate | Status | Evidence |
|---|---|---|
| G1 production caller | ✅ 0 | No production imports |
| G2 canonical test dep | ✅ 0 | All importers in `tests/beta_stage_08_*`, `beta_stage_09_*`, `beta_stage_10_0` (quarantined) |
| G2a legacy test dep | ❌ 20+ files | All in quarantined `beta_stage_08_*`, `beta_stage_09_*`, `beta_stage_10_0` |
| G3 active entry point | ✅ 0 | No entry points |
| G4 dynamic reference | ❌ Yes | `extension_loader.py` uses `import_module` (manifest-driven) |
| G5 tooling dependency | ✅ 0 | No tooling references |
| G6 public surface | ❌ Yes | Extensive `__init__.py` exports (100+ symbols) |

**Classification**: **LEGACY** — G4 fails (manifest-driven dynamic loader), G2a fails, G6 fails.

**Next step**: DEFERRED — dynamic loader is manifest-driven (not hardcoded), but dynamic reference exists. Requires decision on extension framework.

---

### 5. `workflow/`

| Gate | Status | Evidence |
|---|---|---|
| G1 production caller | ✅ 0 | No production imports |
| G2 canonical test dep | ✅ 0 | All importers in `tests/beta_stage_09_*`, `beta_stage_10_0` (quarantined) |
| G2a legacy test dep | ❌ 10 files | All in quarantined `beta_stage_09_*`, `beta_stage_10_0` |
| G3 active entry point | ✅ 0 | No entry points |
| G4 dynamic reference | ✅ 0 | No dynamic imports |
| G5 tooling dependency | ✅ 0 | No tooling references |
| G6 public surface | ❌ Yes | Extensive `__init__.py` exports (100+ symbols) |

**Classification**: **LEGACY** — G2a fails, G6 fails.

**Next step**: DEFERRED — requires decision on workflow framework archive.

---

### 6. `platform_services/`

| Gate | Status | Evidence |
|---|---|---|
| G1 production caller | ✅ 0 | No production imports |
| G2 canonical test dep | ✅ 0 | All importers in `tests/beta_stage_10_*` (quarantined) |
| G2a legacy test dep | ❌ 9 files | All in quarantined `tests/beta_stage_10_*` |
| G3 active entry point | ✅ 0 | No entry points |
| G4 dynamic reference | ✅ 0 | No dynamic imports |
| G5 tooling dependency | ✅ 0 | No tooling references |
| G6 public surface | ❌ Yes | Extensive `__init__.py` exports (100+ symbols) |

**Classification**: **LEGACY** — G2a fails, G6 fails.

**Next step**: DEFERRED — requires decision on platform services framework archive.

---

### 6. `external_api/`

| Gate | Status | Evidence |
|---|---|---|
| G1 production caller | ✅ 0 | No canonical production imports. Used by `web_ui/` (separate Next.js product). |
| G2 canonical test dep | ✅ 0 | All importers in `tests/beta_stage_12_*` (quarantined) |
| G2a legacy test dep | ❌ 16+ files | All in quarantined `tests/beta_stage_12_*` |
| G3 active entry point | ✅ 0 | No entry points |
| G4 dynamic reference | ✅ 0 | No dynamic imports |
| G5 tooling dependency | ✅ 0 | No tooling references |
| G6 public surface | ❌ Yes | Extensive `__init__.py` exports (40+ symbols) |

**Classification**: **LEGACY** — G2a fails, G6 fails. Used by `web_ui/` (separate Next.js product surface).

**Next step**: DEFERRED — requires decision on `external_api/` + `web_ui/` product surface.

---

## Summary: Gate Compliance Matrix

| Subsystem | G1 | G2 | G2a | G3 | G4 | G5 | G6 | Verdict |
|---|---|---|---|---|---|---|---|---|
| `compatibility/` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | DEFERRED |
| `cli/` | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | DEFERRED |
| `runtime_api/` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | DEFERRED |
| `integration/` | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | DEFERRED |
| `workflow/` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | DEFERRED |
| `platform_services/` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | DEFERRED |
| `external_api/` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | DEFERRED |

---

## Archive Decision

### Archive-Safe Candidates: **NONE**

**No subsystem satisfies all G1–G6 gates.** Every subsystem fails at least one gate (typically G2a legacy test dependency and/or G6 public surface).

### Deferred / Unknown: **ALL SEVEN**

| Subsystem | Primary Blockers | Required for Archive |
|---|---|---|
| `compatibility/` | G2a (quarantined test deps), G6 (public surface) | Explicit decision on compatibility audit surface + test cleanup |
| `cli/` | G3 (entry point), G2a (quarantined tests), G5 (tooling probe), G6 (public surface) | Decision on legacy CLI entry + tooling probe + public API |
| `runtime_api/` | G2a (quarantined tests), G6 (public surface) | Decision on `external_api`/`web_ui` product surface |
| `integration/` | G2a, G4 (dynamic loader), G6 | Decision on extension framework + dynamic loader |
| `workflow/` | G2a, G6 | Decision on workflow framework archive |
| `platform_services/` | G2a, G6 | Decision on platform services framework archive |
| `external_api/` | G2a, G6 | Decision on `web_ui` product surface + REST API surface |

---

## Recommended Next Implementation Boundary

**No archive actions authorized by this audit.**

**Required next step**: A **per-subsystem archive readiness review** for each of the seven subsystems, addressing:
1. Quarantined test dependency cleanup (or explicit acceptance of G2a failure with documented rationale)
2. Public surface deprecation/removal plan (G6) or explicit acceptance with documented rationale
3. For `cli/`: entry point retirement plan (G3) and tooling probe removal (G5)
4. For `integration/`: dynamic loader deprecation or migration plan (G4)
5. For `runtime_api/` / `external_api/` / `web_ui/`: product surface decision

**No archive actions** should proceed until each subsystem has a dedicated, evidence-based archive readiness review with explicit stakeholder sign-off on each unmet gate.

---

## Verification

```text
pytest --collect-only         : 3954 collected, 0 errors
pytest tests/contract         : 338 passed
pytest tests/reader_project   : 86 passed
pytest tests/e2e              : 55 passed
pytest tests/runtime          : 10 passed
python -m compileall core lts ui : exit 0
```

All canonical baselines preserved. No code modified.