# Memory: module_index

## Title
NTPE Module Index — Public Modules and Locations

## Purpose
This memory file indexes the public modules of NTPE, their file locations, and their primary responsibilities. AI agents use this to locate where to make changes and understand module relationships.

## Scope
- Public modules (importable by other modules)
- Core infrastructure files
- Does not document every function/class; see `.ai/memory/public_api.md` for API details

## Module Index

| Module | Location | Responsibility | Status |
|--------|----------|----------------|--------|
| (To be populated as modules are indexed) | | | |
| `.ai/` | `.ai/` | AI workspace governance | ACTIVE |
| `docs/` | `docs/` | Documentation | ACTIVE |

## Index Template
When adding a new module entry:

```
| {Module Name} | {file path} | {one-line responsibility} | {ACTIVE / FROZEN / DEPRECATED} |
```

## Update Rules
- Add entries when new public modules are created
- Update status when modules are frozen or deprecated
- Do not remove entries—mark as DEPRECATED instead

## Future Update Notes
- Populate comprehensively as part of module audit
- Consider adding import dependencies for each module
- May integrate with automated module discovery