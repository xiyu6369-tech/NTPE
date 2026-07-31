# RM-4.4A — Provider Utility Wrapper Preflight

## Metadata
- **Stage**: RM-4.4A (Repository Cleanup — Provider Utility Wrappers)
- **Date**: 2026-07-31
- **Parent**: RM-4.4 Provider Wrapper Migration
- **Predecessor**: RM-4.3C (1 SAFE_MOVE → tools/provider_utils/)
- **Status**: PREFLIGHT

---

## Scope (Batch A)

| # | File | Size | Importers | CLI Surface |
|---|------|------|:---:|:---:|
| 1 | `ntpe_provider_setup.py` | 3.6 KB | 1 test | ✅ (`--export`, interactive) |
| 2 | `ntpe_provider_verify.py` | 1.9 KB | 1 test | ✅ (`--provider`, `--allow-missing-key`) |
| 3 | `ntpe_provider_audit.py` | 8.9 KB | 2 tests | ✅ (`--provider`, `--strict`) |

**Excluded**: Batch B/C/D files are not in scope.

---

## Dependency Graph

### ntpe_provider_setup.py
```
External: json, argparse, os, subprocess, pathlib, typing
Internal: config/provider_config.json
             └── load_providers() → dict
Imported by: tests/regression/provider_environment_regression_test.py
```

### ntpe_provider_verify.py
```
External: json, os, pathlib, typing
Internal: config/provider_config.json
             └── load_provider() → dict
Imported by: tests/regression/provider_environment_regression_test.py
```

### ntpe_provider_audit.py
```
External: json, os, re, dataclasses, pathlib, typing
Internal: config/provider_config.json → load_provider_config()
Imported by:
  - tests/integration/provider_configuration_test.py
  - archive/stage_tests/ntpe_ter_v23_provider_configuration_audit_test.py
```

**Zero production/runtime imports.** All import references are from test infrastructure.

---

## Wrapper Necessity

Per RM-3.2 rules:
- Test imports alone do **not** require root wrappers if the file is only imported by test infrastructure.
- However, these three files have **CLI entrypoint** surfaces (`if __name__ == "__main__"` with `main()`).
- CLI entrypoints must remain invocable from root for backward compatibility.

**Decision: WRAPPER_REQUIRED** — Thin wrappers at root that delegate to `tools/provider_utils/`. Test imports will be updated to reference the new location.

---

## CLI Contract

### ntpe_provider_setup.py
```
Usage: python ntpe_provider_setup.py [--export]
--export: Write config/provider_environment_template.env (non-interactive)
(no flag): Interactive provider selection + API key setup
Exit 0 on success; SystemExit on invalid selection
```

### ntpe_provider_verify.py
```
Usage: python ntpe_provider_verify.py [--provider PROVIDER] [--allow-missing-key]
Default: --provider nvidia
Exit 0 = PASS; Exit 1 = FAIL
```

### ntpe_provider_audit.py
```
Usage: python ntpe_provider_audit.py [--provider nvidia] [--strict]
Exit 0 = PASS or PASS_WITH_WARNINGS; Exit 1 = FAIL
--strict: warnings → exit 1
```

---

## Target Structure

```
root/
├── ntpe_provider_setup.py          ← thin wrapper (RM-3.2 compliant)
├── ntpe_provider_verify.py         ← thin wrapper (RM-3.2 compliant)
└── ntpe_provider_audit.py          ← thin wrapper (RM-3.2 compliant)

tools/
└── provider_utils/
    ├── ntpe_provider_setup.py      ← logic (git mv from root)
    ├── ntpe_provider_verify.py     ← logic (git mv from root)
    ├── ntpe_provider_audit.py      ← logic (git mv from root)
    └── ntpe_lcr_batch107_real_provider_validation.py  ← prior (RM-4.3C)
```

---

## Import Boundary Audit (Wrappers)

Each wrapper must comply with RM-3.2 compatibility framework:

**Allowed**:
- `import` (delegate to relocated module)
- Call `main()`
- Return exit code

**Prohibited**:
- Provider initialization
- Config file loading
- Runtime state manipulation
- Environment variable operations
- Logging initialization
- Any business logic

---

## Migration Checklist

1. `git mv` 3 files → `tools/provider_utils/`
2. Create 3 root thin wrappers (RM-3.2)
3. Update test imports:
   - `tests/regression/provider_environment_regression_test.py`
   - `tests/integration/provider_configuration_test.py`
   - `archive/stage_tests/ntpe_ter_v23_provider_configuration_audit_test.py`
4. Update `config/project_layout_policy.json`
5. Wrapper Equivalence Gate (Exit Code, argv, stdout, stderr)
6. `python -m compileall`
7. `python ntpe_validate.py`
8. `git diff --check`
9. Execution Report

---

## Rollback Plan

```bash
git mv tools/provider_utils/ntpe_provider_setup.py ntpe_provider_setup.py
git mv tools/provider_utils/ntpe_provider_verify.py ntpe_provider_verify.py
git mv tools/provider_utils/ntpe_provider_audit.py ntpe_provider_audit.py
git checkout -- config/project_layout_policy.json
git checkout -- tests/regression/provider_environment_regression_test.py
git checkout -- tests/integration/provider_configuration_test.py
git checkout -- archive/stage_tests/ntpe_ter_v23_provider_configuration_audit_test.py
```

Each wrapper is atomic — rollback is a pure reverse of actions.

---

## Risk Assessment

| Risk | Level | Mitigation |
|------|:-----:|------------|
| Break existing CLI invocation | Low | Wrappers preserve argv passthrough |
| Test import breakage | Low | Tests updated to new import path |
| Runtime impact | **0** | No runtime files modified |
| Provider execution | **0** | No API calls triggered |
| Network impact | **0** | Local-only operations |

---

## Preflight Verdict: GO ✅

All three files are self-contained utilities with known CLI contracts, zero runtime dependencies, and only test imports. Migration is low-risk.