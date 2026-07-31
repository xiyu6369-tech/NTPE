# RM-4 Repository Cleanup — Freeze

## Metadata

| 欄位 | 值 |
|------|-----|
| **Freeze ID** | RM-4-FREEZE |
| **Date** | 2026-07-31 |
| **Freeze Commit** | `665507f` (RM-4.4C Invocation wrapper migration) |
| **Audit Report** | `docs/governance/migration/RM_4_5_0_FINAL_ROOT_AUDIT.md` |
| **Predecessor** | RM-3 Repository Governance Baseline |
| **Successor** | RM-5 (next development cycle) |
| **Status** | ❄️ **FROZEN — READ-ONLY BASELINE** |

---

## Scope

RM-4 covers the complete repository de-historicization migration:

| Stage | Date | Commit | Description |
|-------|------|--------|-------------|
| RM-4.0 | 2026-07-30 | `7b98b35` | Preflight inventory + migration plan |
| RM-4.1 | 2026-07-30 | — | Migration manifest (companion to RM-4.0) |
| RM-4.2A | 2026-07-30 | `7b98b35` | SAFE_MOVE migration (581 items → `archive/`) |
| RM-4.2B | 2026-07-30 | `7b98b35` | Review classification (300 root files) |
| RM-4.2C | 2026-07-30 | `7b98b35` | Test migration (285 tests → `archive/stage_tests/`) |
| RM-4.2D | 2026-07-30 | `7b98b35` | Wrapper migration plan (35 → reclassified) |
| RM-4.3A | 2026-07-31 | `8f3ffae` | 17 one-shot launchers → `tools/one_shots/` |
| RM-4.3B | 2026-07-31 | `ac3b6da` | 4 legacy pipeline demos → `tools/legacy_pipeline_launchers/` |
| RM-4.3C | 2026-07-31 | `a9560d6` | 1 provider utility → `tools/provider_utils/` |
| RM-4.3D | 2026-07-31 | `9aeeb4f` | Root final review → 8 KEEP + 9 Wrapper + 2 Archive |
| RM-4.3E | 2026-07-31 | `bd5babb` | Archive 2 legacy obsolete root tools |
| RM-4.4A | 2026-07-31 | `2870b1d` | Provider utility wrappers (3) |
| RM-4.4B | 2026-07-31 | `f76d3cb` | Provider adapter wrappers (2) |
| RM-4.4C | 2026-07-31 | `665507f` | Invocation wrappers (2) |
| RM-4.5.0 | 2026-07-31 | Audit | Final governance preflight audit |

**Total: 9 commits, 16 stages across RM-4.**

---

## Final Metrics

| Metric | Before RM-4 | After RM-4 | Change |
|--------|------------:|----------:|-------:|
| Root Python Files | 42 | 16 | **−61.9%** |
| Root Launchers | 25+ | 0 | **−25** |
| Root Test Files | ~300 | 0 | **−300** |
| Root Legacy Tools | 18 | 0 | **−18** |
| Thin Wrappers | 0 | 11 | **+11** |
| Retained Root Scripts | N/A | 5 | — |
| Archive Items | 0 | 325 | **+325** |
| tools/ Subdirectories | ~4 | 5 | **+1** |

---

## Root Layout (Frozen)

### KEEP_ROOT (8)

| File | Type |
|------|------|
| `launcher.py` | Production wrapper |
| `launcher_translate.py` | Production entry |
| `ntpe_production_translate.py` | Production CLI core |
| `ntpe_validate.py` | Validation entry |
| `ntpe_translate_batch.py` | Compat wrapper |
| `ntpe_translate_txt.py` | Compat wrapper |
| `ntpe_literary_evaluation.py` | Retained wrapper |
| `ntpe_literary_regression.py` | Retained wrapper |

### WRAPPER (6 thin, RM-3.2 compliant)

| File | Delegates To |
|------|-------------|
| `ntpe_batch_monitor.py` | `lts.batch_runtime_monitor.main` |
| `ntpe_launcher.py` | (retained thick — GUI launcher) |
| `ntpe_controlled_real_provider_retry.py` | `tools.provider_controls.ntpe_controlled_real_provider_retry.main` |
| `ntpe_single_real_provider_invocation.py` | `tools.provider_controls.ntpe_single_real_provider_invocation.main` |
| `ntpe_provider_setup.py` | `tools.provider_utils.ntpe_provider_setup.main` |
| `ntpe_provider_verify.py` | `tools.provider_utils.ntpe_provider_verify.main` |
| `ntpe_provider_audit.py` | `tools.provider_utils.ntpe_provider_audit.main` |
| `ntpe_provider_benchmark_session.py` | `tools.provider_controls.ntpe_provider_benchmark_session.main` |

---

## Archive Statistics

| Category | Items |
|----------|:----:|
| `stage_tests/` | ~285 |
| `historical/` (audits, memory, quality reports, sessions) | ~30 |
| `legacy_tools/` | 3 |
| `lts_duplicates/` | ~10 |
| `one_shot_creation/` | 3 |
| `data_artifacts/`, `legacy_config/`, `legacy/`, `release_artifacts/` | misc |
| **Total** | **325** |

---

## Validation (Freeze Gate)

| Gate | Result |
|------|--------|
| `git diff --check` | ✅ PASS |
| `python ntpe_validate.py` | ✅ ALL PASS (8/8) |
| `python -m compileall .` | ✅ PASS (3039 files) |
| Python Logic Modified | ✅ 0 |
| Runtime Modified | ✅ 0 |
| Provider Requests | ✅ 0 |
| Import Integrity | ✅ 0 broken imports |

---

## Rollback Baseline

To return to the pre-RM-4 state:

```
git checkout 6b0fe49
```

All RM-4 commits are reversible via `git revert`.

---

## Governance Documents

All RM-4 migration documents reside in `docs/governance/migration/`:

- `RM_4_0_PREFLIGHT_REPORT.md`
- `RM_4_1_MIGRATION_PLAN.md` + `RM_4_1_MIGRATION_MANIFEST.json`
- `RM_4_2A_MIGRATION_REPORT.md` + `RM_4_2A_EXECUTION_LOG.json` + `RM_4_2A_MOVE_MAPPING.json`
- `RM_4_2B_REVIEW_CLASSIFICATION_REPORT.md` + `RM_4_2B_CLASSIFICATION_DATA.json`
- `RM_4_2C_TEST_MIGRATION_REPORT.md` + `RM_4_2C_TEST_MIGRATION_PREFLIGHT.md`
- `RM_4_2D_WRAPPER_MIGRATION_PLAN.md`
- `RM_4_3A_ONE_SHOT_MIGRATION_REPORT.md`
- `RM_4_3B_LEGACY_PIPELINE_MIGRATION_REPORT.md`
- `RM_4_3C_PROVIDER_UTILITY_MIGRATION_REPORT.md` + `RM_4_3C_PROVIDER_UTILITY_PREFLIGHT.md`
- `RM_4_3D_ROOT_FINAL_REVIEW_REPORT.md`
- `RM_4_3E_ARCHIVE_LEGACY_ROOT_PREFLIGHT.md`
- `RM_4_4_0_WRAPPER_PREFLIGHT_REPORT.md`
- `RM_4_4A_PROVIDER_WRAPPER_PREFLIGHT.md` + `RM_4_4A_PROVIDER_WRAPPER_REPORT.md`
- `RM_4_4B_PROVIDER_ADAPTER_PREFLIGHT.md` + `RM_4_4B_PROVIDER_ADAPTER_MIGRATION_REPORT.md`
- `RM_4_4C_INVOCATION_WRAPPER_PREFLIGHT.md`
- `RM_4_5_0_FINAL_ROOT_AUDIT.md`

Policy: `config/project_layout_policy.json`

---

## Freeze Declaration

RM-4 Repository Cleanup is hereby **FROZEN**.

- All relocation operations are complete.
- All validation gates have passed.
- No further RM-4 modifications are permitted.
- RM-5 begins from this freeze baseline.

---

*Frozen — 2026-07-31*