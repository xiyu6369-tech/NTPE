# RM-4.4C — Invocation Wrapper Preflight

## Metadata
- **Stage**: RM-4.4C (Repository Cleanup — Controlled Invocation Wrappers)
- **Date**: 2026-07-31
- **Parent**: RM-4.4 Provider Wrapper Migration
- **Predecessor**: RM-4.4B (Provider Adapter Wrappers)
- **Status**: PREFLIGHT

---

## Scope (Batch C)

| # | File | Size | Type | Importers |
|---|------|------|------|:---:|
| 1 | `ntpe_controlled_real_provider_retry.py` | 2.2 KB | Thick CLI | 1 test |
| 2 | `ntpe_single_real_provider_invocation.py` | 2.1 KB | Thick CLI | 1 test |

Target: `tools/provider_controls/`

---

## Dependency Evidence

### 1. ntpe_controlled_real_provider_retry.py

```
Python imports:
  from __future__ import annotations
  import argparse, getpass, json, os
  from pathlib import Path
  from core.adaptive_context_controlled_provider_retry import (
      ControlledProviderRetryConfig,
      ControlledProviderRetryRunner,
  )

ROOT: Path(__file__).resolve().parent
CLI: if __name__ == "__main__": raise SystemExit(main())
Has def main(): YES
Has def build_parser(): YES
```

**Python importers: 1**
```
tests/integration/...v700_stage10101_...controlled_retry_test.py:27
  from ntpe_controlled_real_provider_retry import build_parser
```

**Subprocess callers: 0** — Zero CLI scripts, CI configs, Makefiles, or shell scripts.

**Manifest: 1** — `manifests/te_v700_stage10101_provider_timeout_controlled_retry_manifest.json` (frozen SHA hash of root file).

**Config: 1** — `config/project_layout_policy.json` → `allowed_root_files: "n.controlled_..._retry.py"`. NOT in permitted_compatibility_wrappers or retained_root_wrappers.

**Docs: 1** — `docs/releases/te_v7_0/TE_V7_0_STAGE10_10_1_PROVIDER_TIMEOUT_CONTROLLED_RETRY.md`

**Archive: multiple** (name-only audit refs, not runtime path dependencies).

### 2. ntpe_single_real_provider_invocation.py

**Python imports:**
```
  from __future__ import annotations
  import argparse, getpass, json, os
  from pathlib import Path
  from core.adaptive_context_real_provider_preflight import PreflightAttemptPlan
  from core.adaptive_context_single_real_invocation import (
      SingleRealInvocationConfig,
      SingleRealInvocationRunner,
  )

ROOT: Path(__file__).resolve().parent
CLI: if __name__ == "__main__": raise SystemExit(main())
Has def main(): YES
Has def build_parser(): YES
```

**Python importers: 1**
```
tests/integration/...v700_stage1010_...single_real_provider_invocation_test.py:25
  from ntpe_single_real_provider_invocation import build_parser
```

**Subprocess callers: 0** — Zero CLI scripts, CI configs, Makefiles, or shell scripts.

**Manifest: 1** — `manifests/te_v700_stage1010_single_real_provider_invocation_manifest.json` (frozen SHA hash of root file; contains immutable prior artifact cross-reference).

**Config: 1** — `config/project_layout_policy.json` → `allowed_root_files: "n.single_real_..._invocation.py"`. NOT in permitted_compatibility_wrappers or retained_root_wrappers.

**Docs: 1** — `docs/releases/te_v7_0/TE_V7_0_STAGE10_10_SINGLE_REAL_PROVIDER_INVOCATION.md`

**Archive: multiple** (name-only audit refs, not runtime path dependencies).

---

## Dependency Summary

| Check | controlled_retry | single_invocation |
|-------|:---:|:---:|
| Python imports | **1** (test) | **1** (test) |
| Subprocess calls | **0** | **0** |
| Manifest (SHA frozen) | **1** | **1** |
| Config (policy) | **1** | **1** |
| Docs / README (functional) | **1** | **1** |
| Production runtime | **0** | **0** |
## Wrapper Gate (RM-3.2)

| File | Gate | Reason |
|------|:---:|--------|
| `ntpe_controlled_real_provider_retry.py` | **WRAPPER_REQUIRED** | 1 test importer (`build_parser`), CLI entrypoint must stay invocable |
| `ntpe_single_real_provider_invocation.py` | **WRAPPER_REQUIRED** | 1 test importer (`build_parser`), CLI entrypoint must stay invocable |

### Wrapper Rationale

Both files have:
1. **CLI entrypoint** (`if __name__ == "__main__"`) — root-invocable by design
2. **Test imports** that reference `build_parser` from root path — breaking this import would require test updates
3. **Manifest SHA hashes** frozen to the root file path — moving the file without a root wrapper changes the manifest hash computation

## Implementation Review

Both files already contain:

```python
def main() -> int:          # Present, functional
def build_parser() -> ...   # Present
if __name__ == "__main__":  # Present
    raise SystemExit(main())
```

**No changes needed to the existing implementation.** Each file is already RM-3.2-ready. Migration only requires:
1. `git mv` logic to `tools/provider_controls/`
2. Create thin root wrapper that delegates to the relocated module
3. The `main()` function requires `ROOT` (Path to project root); after move, the relocation must adjust `ROOT` from `Path(__file__).resolve().parent` → `Path(__file__).resolve().parents[3]`

---

## Migration Plan

### Step 1: Directory creation
```
tools/
└── provider_controls/    ← NEW directory
```

### Step 2: Move files
```bash
git mv ntpe_controlled_real_provider_retry.py  tools/provider_controls/
git mv ntpe_single_real_provider_invocation.py tools/provider_controls/
```

### Step 3: Path fix in relocated files
Both files use `ROOT = Path(__file__).resolve().parent`.
After moving to `tools/provider_controls/`, update:
```python
# Before (root)
ROOT = Path(__file__).resolve().parent

# After (tools/provider_controls/)
ROOT = Path(__file__).resolve().parents[3]
```

### Step 4: Create RM-3.2 Root Wrappers

```python
# ntpe_controlled_real_provider_retry.py (root wrapper)
"""Compatibility wrapper. Real code at tools/provider_controls/ntpe_controlled_real_provider_retry.py"""
from tools.provider_controls.ntpe_controlled_real_provider_retry import main

if __name__ == "__main__":
    raise SystemExit(main())
```

```python
# ntpe_single_real_provider_invocation.py (root wrapper)
"""Compatibility wrapper. Real code at tools/provider_controls/ntpe_single_real_provider_invocation.py"""
from tools.provider_controls.ntpe_single_real_provider_invocation import main

if __name__ == "__main__":
    raise SystemExit(main())
```

### Step 5: Import Boundary Audit

**Wrapper must (allowed):** import → delegate → call `main()` → return exit code

**Wrapper must NOT (prohibited):** provider init, config loading, runtime state, env var operations, logging init, any business logic, any ROOT/path computation

### Step 6: Policy update
- `config/project_layout_policy.json`:
  - `retained_root_wrappers`: Add both files
  - `permitted_compatibility_wrappers`: Add both files
  - `allowed_root_files`: Keep both files (now thin wrappers)

### Step 7: Verification Gates

1. `git diff --check` → PASS
2. `python ntpe_validate.py` → ALL PASS
3. `python -m compileall` → PASS on both wrappers + relocated files
4. Wrapper Equivalence Gate:
   - `python ntpe_controlled_real_provider_retry.py --execution-mode fake` → exit 0, JSON stdout
   - `python ntpe_single_real_provider_invocation.py --execution-mode fake` → exit 0, JSON stdout

---

## Target Structure

```
root/
├── ntpe_controlled_real_provider_retry.py     ← RM-3.2 thin wrapper
└── ntpe_single_real_provider_invocation.py    ← RM-3.2 thin wrapper

tools/
└── provider_controls/                         ← NEW directory
    ├── ntpe_controlled_real_provider_retry.py ← logic (git mv, path fixed)
    └── ntpe_single_real_provider_invocation.py← logic (git mv, path fixed)
```

Sibling directories (existing):
```
tools/
├── provider_utils/     ← (RM-4.3C, RM-4.4A)
├── provider_adapters/  ← (RM-4.4B)
└── provider_controls/  ← (RM-4.4C) NEW
```

---

## Rollback Plan

```bash
# Reverse the git mv
git mv tools/provider_controls/ntpe_controlled_real_provider_retry.py  ntpe_controlled_real_provider_retry.py
git mv tools/provider_controls/ntpe_single_real_provider_invocation.py ntpe_single_real_provider_invocation.py

# Revert path fix (ROOT: .parents[3] → .parent)
git checkout -- tools/provider_controls/

# Revert policy
git checkout -- config/project_layout_policy.json

# Remove empty directory
rmdir tools/provider_controls/
```

Each wrapper is atomic — rollback is a pure inverse of actions. < 3 minutes.

---

## Risk Assessment

| Risk | Level | Mitigation |
|------|:-----:|------------|
| Break test imports (build_parser) | **Low** | Root wrapper preserves import path |
| Break CLI invocation | **Low** | Wrapper preserves `main()` pass-through |
| ROOT path break on move | **Low** | Path fix from `.parent` → `.parents[3]` |
| Manifest SHA mismatch | **None** | Source file name unchanged; harmony on next freeze |
| New directory | Minimal | same `tools/` parent as siblings |
| Runtime impact | **0** | No runtime files modified; fake mode default |
| Provider request | **0** | No API calls triggered |
---

## Validation Plan

### Preflight Verification (this phase only)

| Check | Result |
|-------|--------|
| `git diff --check` | ✅ PASS |
| `python ntpe_validate.py` | ✅ ALL PASS (19.95s) |
| Python files modified | **0** |
| Runtime modified | **0** |
| Provider Request | **0** |
| Network Request | **0** |
| Commit | No |
| Push | No |

### Post-Migration Verification

| Check | Expected |
|-------|----------|
| `git diff --check` | ✅ PASS |
| `python ntpe_validate.py` | ✅ ALL PASS |
| `python -m compileall` | ✅ Both wrappers + moved files |
| Import: `from ntpe_controlled_real_provider_retry import build_parser` | ✅ Compatible |
| Import: `from ntpe_single_real_provider_invocation import build_parser` | ✅ Compatible |
| Test: both integration tests pass or skip | ✅ |

---

## Preflight Verdict: GO ✅

Both files are well-structured direct CLI entrypoints with `def main()`, `def build_parser()`, and `if __name__ == "__main__"`. Each has exactly one test importer (importing `build_parser`), zero subprocess callers, zero production runtime dependencies, and zero real provider calls by default.

Both files follow identical structure to RM-4.4A and RM-4.4B — same `tools/` subdirectory sibling pattern, same root wrapper strategy, same risk profile.

**Decision:**

| File | Gate |
|------|:---:|
| `ntpe_controlled_real_provider_retry.py` | ✅ **WRAPPER_REQUIRED** → `tools/provider_controls/` with root thin wrapper |
| `ntpe_single_real_provider_invocation.py` | ✅ **WRAPPER_REQUIRED** → `tools/provider_controls/` with root thin wrapper |

---

*Generated by RM-4.4C Preflight — 2026-07-31*