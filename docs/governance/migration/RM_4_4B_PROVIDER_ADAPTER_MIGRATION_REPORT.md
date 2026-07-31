# RM-4.4B — Provider Adapter Wrapper Execution Report

## Metadata
- **Stage**: RM-4.4B
- **Date**: 2026-07-31
- **Status**: ✅ COMPLETE
- **Parent**: RM-4.4 Provider Wrapper Migration
- **Predecessor**: RM-4.4A ✅ `2870b1d`

---

## Migration Mapping

### A — `ntpe_authorized_provider_invocation.py` (SAFE_MOVE)

| Step | Detail |
|------|--------|
| Source | root `ntpe_authorized_provider_invocation.py` |
| Destination | `tools/provider_controls/ntpe_authorized_provider_invocation.py` |
| Method | `git mv` (rename detected by Git) |
| Wrapper | ❌ None needed (0 importers, 0 subprocess) |
| Path fix | `ROOT = Path(__file__).resolve().parent` → `.parent.parent.parent` |

### B — `ntpe_provider_benchmark_session.py` (WRAPPER_REQUIRED)

| Step | Detail |
|------|--------|
| Source | root `ntpe_provider_benchmark_session.py` |
| Destination | `tools/provider_controls/ntpe_provider_benchmark_session.py` |
| Method | `git mv` |
| Impl change | Added `def main(): return run_harness()`, updated `__main__` block |
| Root wrapper | `from tools.provider_controls.ntpe_provider_benchmark_session import main` |
| Reason | 1 subprocess call in integration test at root path |

---

## Wrapper Code (RM-3.2 Compliant)

```python
from tools.provider_controls.ntpe_provider_benchmark_session import main

if __name__ == "__main__":
    raise SystemExit(main())
```

**Import boundary audit:**
| Check | Result |
|-------|:---:|
| Only import main | ✅ |
| No provider init | ✅ |
| No config loading | ✅ |
| No env operations | ✅ |
| No logging | ✅ |
| No runtime state | ✅ |

---

## Policy Update

| Section | Change |
|---------|--------|
| `allowed_root_files` | Removed `ntpe_authorized_provider_invocation.py` |
| `retained_root_wrappers` | Removed both files |
| `permitted_compatibility_wrappers` | Added `ntpe_provider_benchmark_session.py` |

---

## Equivalence Gate

### ntpe_authorized_provider_invocation.py (SAFE_MOVE)
No wrapper — equivalence is native. Path fix preserves `config/` resolution.

### ntpe_provider_benchmark_session.py (WRAPPER)

| Test | Result |
|------|:---:|
| `--help` exit code | 0 ✅ |
| `--help` shows usage | ✅ |
| import `main()` from wrapper | ✅ |
| subprocess test passes | ✅ 1/1 |
| argv passthrough | ✅ |

---

## Validation Chain

| Check | Result |
|-------|--------|
| `python -m compileall .` | ✅ 3037 files, 0 errors |
| `python ntpe_validate.py` | ✅ ALL PASS (8/8) |
| `git diff --check` | ✅ PASS |
| `git diff --stat` | 3 files, +9/-6 |
| Root Python files | 16 (down from 17) |
| Subprocess integration test | ✅ 1 passed |
| Runtime impact | **0** |
| Provider execution | **0** |
| Network | **0** |

### Git Status
```
RM ntpe_authorized_provider_invocation.py → tools/provider_controls/
RM ntpe_provider_benchmark_session.py → tools/provider_controls/
M  config/project_layout_policy.json
?? ntpe_provider_benchmark_session.py    (root wrapper — new)
```

---

## Structure

```
root/
└── ntpe_provider_benchmark_session.py    ← RM-3.2 wrapper (3 lines)

tools/
└── provider_controls/                    ← NEW
    ├── ntpe_authorized_provider_invocation.py   (SAFE_MOVE)
    └── ntpe_provider_benchmark_session.py       (WRAPPER_REQUIRED — has main())
```

---

## Impact Assessment

| Domain | Impact |
|--------|:---:|
| Runtime | 0 |
| Provider | 0 |
| Network | 0 |
| Production | 0 |
| Frozen Layers | 0 |

---

## Final Verdict: ✅ PASS

2 files migrated:
- 1 SAFE_MOVE (no wrapper)
- 1 WRAPPER_REQUIRED (RM-3.2 thin wrapper)

RR-3.2 process — all wrappers use `from imp import main` + `raise SystemExit(main())`.

**Ready for RM-4.4C — Provider Controls Wrappers.**