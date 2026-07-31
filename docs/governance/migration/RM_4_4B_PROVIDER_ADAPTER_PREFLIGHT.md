# RM-4.4B — Provider Adapter Wrapper Preflight

## Metadata
- **Stage**: RM-4.4B (Repository Cleanup — Provider Adapter Wrappers)
- **Date**: 2026-07-31
- **Parent**: RM-4.4 Provider Wrapper Migration
- **Predecessor**: RM-4.4A (Provider Utility Wrappers — ✅ `2870b1d`)
- **Status**: PREFLIGHT

---

## Scope (Batch B)

| # | File | Size | Type | Importers |
|---|------|------|------|:---:|
| 1 | `ntpe_authorized_provider_invocation.py` | 392 B | Thin delegate → `core/` | **0** |
| 2 | `ntpe_provider_benchmark_session.py` | 168 B | Thin delegate → `core/` | **0** |

Target: `tools/provider_adapters/`
Root wrappers: only if WRAPPER_REQUIRED per Wrapper Gate.

---

## Dependency Scan

### ntpe_authorized_provider_invocation.py

```
Size: 392 B (18 lines)
Imports: json, pathlib, core.adaptive_context_authorized_provider_cli
CLI: if __name__ == "__main__": raise SystemExit(main())
ROOT: Path(__file__).resolve().parent (needs fix if moved)
```

**Python importers: 0** — Zero files import this module.
**Subprocess: 0** — Zero subprocess calls referencing this file.
**Manifest: 1** — `manifests/te_v700_stage106...json` (SHA hash, frozen)
**Config: 1** — `config/project_layout_policy.json` (allowed_root_files)
**Docs: multiple** — governance/README references (name only)

### ntpe_provider_benchmark_session.py

```
Size: 168 B (7 lines）
Imports: from core.adaptive_context_provider_session_cli import run_harness
No ROOT — fully delegates to core
CLI: if __name__ == "__main__": raise SystemExit(run_harness())
```

**Python importers: 0** — Zero files import this module.
**Subprocess: 1 &#x;** 
`tests/integration/...v700_stage103_...erversion_test.py:107`
```python
subprocess.run([sys.executable, "ntpe_provider_benchmark_session.py", ...], cwd=ROOT)
```
**Manifest: 1** — `manifests/te_v700_stage103...json`
**Docs: 1** — `docs/releases/te_v7_0/TE_V7_0_STAGE10_3_*.md`
---

## Compatibility Gate

| Check | authorized_provider_invocation | benchmark_session |
|-------|:---:|:---:|
| Python imports | 0 | 0 |
| Subprocess calls | 0 | **1** |
| Manifest SHA (frozen) | 1 | 1 |
| Release docs | 0 | 1 |

---

## Wrapper Gate (RM-3.2)

| File | Gate | Reason |
|------|:---:|--------|
| `ntpe_authorized_provider_invocation.py` | **SAFE_MOVE** | 0 importers, 0 subprocess, 0 production runtime |
| `ntpe_provider_benchmark_session.py` | **WRAPPER_REQUIRED** | 1 subprocess from integration test |

---

## Migration Strategy

**ntpe_authorized_provider_invocation.py — SAFE_MOVE**
- `git mv` root → `tools/provider_adapters/`
- No root wrapper needed
- Path fix: `ROOT = Path(__file__).resolve().parent` → `.parent.parent.parent`

**ntpe_provider_benchmark_session.py — WRAPPER_REQUIRED**
- `git mv` root → `tools/provider_adapters/`
- Root RM-3.2 thin wrapper delegates to `run_harness()`
- Subprocess test at root path stays valid (wrapper replaces old file)
- No path fix (no ROOT variable)

---

## Target Structure

```
root/
└── ntpe_provider_benchmark_session.py    ← RM-3.2 wrapper

tools/
└── provider_adapters/                    ← NEW directory
    ├── ntpe_authorized_provider_invocation.py
    └── ntpe_provider_benchmark_session.py
```

---

## Policy Update Plan

- `retained_root_wrappers`: Remove both files
- `allowed_root_files`: Remove `ntpe_authorized_provider_invocation.py`, keep `ntpe_provider_benchmark_session.py`
- `permitted_compatibility_wrappers`: Add `ntpe_provider_benchmark_session.py`

---

## Rollback

```bash
git mv tools/provider_adapters/ntpe_authorized_provider_invocation.py root/
git mv tools/provider_adapters/ntpe_provider_benchmark_session.py root/
git checkout -- config/project_layout_policy.json
```

---

## Risk Assessment

| Risk | Level | Note |
|------|:---:|------|
| SAFE_MOVE without wrapper | Low | 0 importers, 0 subprocess |
| Wrapper equivalence | Low | Same pattern as RM-4.4A (proven) |
| Subprocess test break | None | Root wrapper preserves exact CLI path |
| New directory | Minimal | `tools/provider_adapters/` same parent as `provider_utils/` |

---

## Prelight Verdict

| Decision | File |
|----------|------|
| ✅ **SAFE_MOVE** | `ntpe_authorized_provider_invocation.py` |
| ✅ **WRAPPER_REQUIRED** | `ntpe_provider_benchmark_session.py` |

---

## Preflight Verification (this phase only)

| Check | Result |
|-------|--------|
| `git diff --check` | ✅ PASS |
| `python ntpe_validate.py` | ✅ ALL PASS |
| Python files modified | **0** |
| Runtime modified | **0** |
| Provider Request | **0** |
| Network Request | **0** |
| Commit | No |
| Push | No |