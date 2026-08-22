# P0 Official UI Directory Proposal

**Generated**: 2026-08-14  
**Baseline Commit**: 1ee85bf80c23f0fb38b783dab2ba3cfd12736d6b

---

## Official Reader UI Decision

**Official Reader UI**: **NTPE Reader Web App**  
**Status**: To be implemented in P0 Productization  
**Current State**: Does not exist — only legacy surfaces present

---

## Governance Check

### Repository Governance Baseline

**Files**: `docs/governance/repository/`
- `REPOSITORY_STRUCTURE_SPEC.md`
- `ROOT_POLICY.md`
- `ARCHIVE_POLICY.md`
- `TOOLS_POLICY.md`
- `DIRECTORY_OWNERSHIP.md`
- `REPOSITORY_GOVERNANCE_BASELINE.md`

### Root Policy (ROOT_POLICY.md)

> NTPE Root directory **permanently prohibited** from:
> - Stage Scripts
> - Verification Scripts
> - Temporary Utilities
> - Experimental Modules
> - One-shot Tools
>
> **Only allowed**:
> - Entry Point
> - Compatibility Wrapper
> - README, LICENSE, Git metadata
> - Minimal configuration

### Tools Policy (TOOLS_POLICY.md)

> All developer tools must be in `tools/` with subcategories:
> - `launchers/`, `validators/`, `maintenance/`, `monitoring/`, `recovery/`, `migration/`, `utilities/`

### Directory Ownership (DIRECTORY_OWNERSHIP.md)

| Directory | Owner | Purpose |
|-----------|-------|---------|
| `core/` | Runtime Team | Production runtime, translation engine |
| `lts/` | Runtime Team | Long-term support runtimes |
| `ui/` | **QUARANTINED** | Legacy desktop GUI |
| `web_ui/` | **LEGACY** | Legacy web UI facade |
| `runtime_api/` | **LEGACY** | Legacy REST API |
| `tools/` | Tooling Team | Developer tools |

---

## Proposed Directory: `web/reader/`

### Structure

```
web/
  reader/
    app/                    # Next.js / React application
      src/
        app/                # App Router pages
        components/         # Shared components
        lib/                # Utilities, API clients
        hooks/              # React hooks
      public/               # Static assets
      package.json
      next.config.js
      tsconfig.json
    api/                    # API routes (if needed)
      translation/          # Proxy to ntpe_production_translate
    tests/                  # E2E, component tests
    Dockerfile
    docker-compose.yml
```

### Ownership

| Component | Owner |
|-----------|-------|
| `web/reader/app/` | Product Team (Reader Web App) |
| `web/reader/api/` | Platform Team (API gateway) |
| `web/reader/tests/` | QA Team |

### Rationale for `web/reader/`

1. **Separation from legacy** — `web_ui/` is explicitly LEGACY_LIFECYCLE_FACADE, not a product
2. **Clear ownership** — `reader/` subdirectory signals "Reader Web App" product
3. **Governance compliant** — Not in root, not in `tools/`, not in `ui/`
4. **Scalable** — Can add `web/admin/`, `web/api/` later without conflict
5. **Framework standard** — `web/` is common top-level for web applications

---

## Conflict Analysis: Reuse `web_ui/`?

### Option A: Reuse `web_ui/`

| Pros | Cons |
|------|------|
| Existing directory | **Classified as LEGACY_LIFECYCLE_FACADE** |
| Some components exist | Framework-neutral, no actual frontend |
| REST client exists | No build system, no framework, no UI |
| | **Governance: legacy classification blocks product use** |
| | Would require reclassification + major rewrite |

### Option B: New `web/reader/` (RECOMMENDED)

| Pros | Cons |
|------|------|
| Clean slate for product | New directory to create |
| No legacy baggage | Must build from scratch |
| Clear product boundary | |
| Governance compliant | |
| Can coexist with legacy during transition | |

**Decision**: **NEW `web/reader/`** — Do not reuse `web_ui/`

---

## Governance Compliance Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| Not in root directory | ������ PASS | `web/reader/` is subdirectory |
| Not in `tools/` | ������ PASS | Separate top-level |
| Not in `ui/` (quarantined) | ������ PASS | Different tree |
| Not in `web_ui/` (legacy) | ������ PASS | Different tree |
| Clear ownership | ������ PASS | Product Team |
| Scalable structure | ������ PASS | `web/` can hold multiple apps |
| No stage scripts in root | ������ PASS | Build artifacts in `web/reader/app/` |

---

## Migration Path

1. **Stage 0** (this): Propose `web/reader/` — no implementation
2. **P0 Implementation**: Create `web/reader/app/` with Next.js + TypeScript
3. **Integration**: API proxy to `ntpe_production_translate.py` (or future REST service)
4. **Legacy coexistence**: `web_ui/` remains for reference, not removed
5. **Future**: `web_ui/` → archive when Reader Web App reaches parity

---

## Required Governance Updates (Post-P0)

After P0 implementation, update:
- `DIRECTORY_OWNERSHIP.md` — Add `web/reader/` ownership
- `REPOSITORY_STRUCTURE_SPEC.md` — Document `web/` top-level purpose
- `TOOLS_POLICY.md` — Clarify web apps are not `tools/`