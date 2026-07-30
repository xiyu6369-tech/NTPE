# RM-4.3D — Root Final Review Report

## Phase
RM-4: Repository De-Historicization  
`RM-4.3D` — Audit: Root Final Review & RM-4.4 Preparation

## Date
2026-07-31

## Baseline
- **RM-4.3A**: COMMITTED (`8f3ffae`) — 17 one-shot launchers → `tools/one_shots/`
- **RM-4.3B**: COMMITTED (`ac3b6da`) — 4 legacy pipeline + 1 archive
- **RM-4.3C**: COMMITTED (`a9560d6`) — 1 provider utility → `tools/provider_utils/`

---

## Root Inventory (Post RM-4.3C)

### Root Files (Total: 27)

| Type | Count | Items |
|------|:---:|------|
| Python | 19 | See classification below |
| Config/Text | 4 | `.clineignore`, `.clinerules`, `.editorconfig`, `.gitattributes`, `.gitignore`, `README.md`, `VERSION.txt`, `requirements.txt` |
| JSON data | 1 | `original_ko_chunk_000001.json` |

### Root Directories (Total: 50)

All 50 directories in `config/project_layout_policy.json` `allowed_root_directories` plus `__pycache__` (ignored). No unexpected directories detected.

### Reduction Summary

| Stage | Root Python | Change |
|-------|------------:|-------:|
| RM-4.2A (initial) | 42 | — |
| RM-4.3A (one-shots) | 25 | −17 |
| RM-4.3B (legacy pipeline) | 20 | −5 |
---

## Remaining Root Python Classification

### Classification Table

| # | File | Policy | Importers | CI/Subprocess | Classification |
|---|------|---|:---:|:---|------|
| 1 | `launcher.py` | permitted wrapper | REQUIRED_ENTRYPOINTS | — | **KEEP_ROOT** |
| 2 | `launcher_translate.py` | production | REQUIRED_ENTRYPOINTS | — | **KEEP_ROOT** |
| 3 | `ntpe_production_translate.py` | production | 3 wrappers + tests | ✅ subprocess | **KEEP_ROOT** |
| 4 | `ntpe_validate.py` | validation | — | — | **KEEP_ROOT** |
| 5 | `ntpe_translate_batch.py` | permitted wrapper | — | ✅ lts/ subprocess | **KEEP_ROOT** |
| 6 | `ntpe_translate_txt.py` | permitted wrapper | — | ✅ lts/ subprocess | **KEEP_ROOT** |
| 7 | `ntpe_literary_evaluation.py` | retained wrapper | 3 (prod + regression) | — | **KEEP_ROOT** |
| 8 | `ntpe_literary_regression.py` | retained wrapper | 5 (prod + tests) | — | **KEEP_ROOT** |
| 9 | `ntpe_authorized_provider_invocation.py` | retained wrapper | 0 | — | **→ RM-4.4** |
| 10 | `ntpe_controlled_real_provider_retry.py` | retained wrapper | 1 test | — | **→ RM-4.4** |
| 11 | `ntpe_provider_benchmark_session.py` | retained wrapper | 0 | — | **→ RM-4.4** |
| 12 | `ntpe_single_real_provider_invocation.py` | retained wrapper | 1 test | — | **→ RM-4.4** |
| 13 | `ntpe_provider_setup.py` | retained wrapper | 1 test | — | **→ RM-4.4** |
| 14 | `ntpe_provider_verify.py` | retained wrapper | 1 test | — | **→ RM-4.4** |
| 15 | `ntpe_provider_audit.py` | retained wrapper | 2 tests | — | **→ RM-4.4** |
| 16 | `ntpe_batch_monitor.py` | retained wrapper | 0 | ✅ lts/ subprocess | **→ RM-4.4** |
| 17 | `ntpe_launcher.py` | retained wrapper | 0 | ✅ test subprocess | **→ RM-4.4** |
| 18 | `ntpe_long_run_recovery.py` | retained wrapper | 0 | — | ⚠️ **ARCHIVE** |
| 19 | `ntpe_plugin_marketplace.py` | retained wrapper | 0 | — | ⚠️ **ARCHIVE** |

### Notes

- **#18 `ntpe_long_run_recovery.py`** — RM-4.2B: ARCHIVE_ONLY, RM-3.2: SAFE_MOVE. 0 importers. LTS freeze hash exists but in `archive/lts_duplicates/` (historical). **Recommend: ARCHIVE → `archive/legacy_tools/`**
- **#19 `ntpe_plugin_marketplace.py`** — RM-4.2B: ARCHIVE_ONLY, RM-3.2: SAFE_MOVE. 0 importers. Doc/historical refs only. **Recommend: ARCHIVE → `archive/legacy_tools/`**

These 2 are gate-clean for immediate archiving (RM-4.3E optional).
| RM-4.3C (provider utils) | 19 | −1 |
| **Total reduction** | **19** | **−23 (−54.8%)** |
---

## RM-4.4 Preparation Summary

### Wrapper Candidates (9 files → `tools/provider_utils/` or `tools/`)

| File | Challenge | Strategy |
|------|:---|------|
| `ntpe_authorized_provider_invocation.py` | 0 importers | Thin root stub → `tools/provider_utils/` |
| `ntpe_controlled_real_provider_retry.py` | 1 test | Thin root stub → `tools/provider_utils/` |
| `ntpe_provider_benchmark_session.py` | 0 importers | Thin root stub → `tools/provider_utils/` |
| `ntpe_single_real_provider_invocation.py` | 1 test | Thin root stub → `tools/provider_utils/` |
| `ntpe_provider_setup.py` | 1 test | Thin root stub → `tools/provider_utils/` |
| `ntpe_provider_verify.py` | 1 test | Thin root stub → `tools/provider_utils/` |
| `ntpe_provider_audit.py` | 2 tests | Thin root stub → `tools/provider_utils/` |
| `ntpe_batch_monitor.py` | lts/ subprocess refs | Thin root stub (CLI contract) |
| `ntpe_launcher.py` | verification test subprocess | Thin root stub (CLI contract) |

All 9 use the same wrapper pattern: `from tools.provider_utils.X import main; raise SystemExit(main())`

### Archive Candidates (2 files)

| File | Target |
|------|--------|
| `ntpe_long_run_recovery.py` | `archive/legacy_tools/` |
| `ntpe_plugin_marketplace.py` | `archive/legacy_tools/` |

---

## Policy Alignment

| Area | Status |
|------|--------|
| `allowed_root_files` (319) | ✅ Matches actual root |
| `retained_root_wrappers` (12) | ✅ Correct inventory |
| `production_entrypoints` (2) | ✅ `launcher_translate.py`, `ntpe_production_translate.py` |
| `validation_entrypoints` (1) | ✅ `ntpe_validate.py` |
| `permitted_compatibility_wrappers` (3) | ✅ `launcher.py`, `ntpe_translate_batch.py`, `ntpe_translate_txt.py` |
| Orphan entries | ✅ 0 |
| Unexpected directories | ✅ 0 of 50 |

---

## Final Verdict

```
RM-4.3D Root Final Review  ✅ COMPLETE
```

- Root Python: **42 → 19** (−54.8% across RM-4.3A/B/C)
- **8 KEEP_ROOT** confirmed
- **9 WRAPPER** candidates ready for RM-4.4
- **2 ARCHIVE** candidates ready (RM-4.3E optional)
- Policy fully aligned

### Next Options

| Option | Stage | Scope |
|--------|-------|-------|
| A | RM-4.3E | Archive 2 (low risk, no wrapper) |
| B | RM-4.4 | Execute 9 Wrapper Migrations |
| C | RM-4.3E → RM-4.4 | Archive first, then wrappers |

## Compliance (Audit Only)

| Operation | Status |
|-----------|--------|
| Git mv / Python / Runtime / Provider / Network / Commit | ❌ All |