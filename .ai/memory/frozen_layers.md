# Memory: frozen_layers

## Title
NTPE Frozen Layers — Immutable Module Registry

## Purpose
This memory file maintains the authoritative registry of frozen (immutable) modules in NTPE. Frozen layers are locked during release/freeze ceremonies and must never be modified by AI agents without explicit human authorization and a formal unfreeze process.

## Scope
- Lists all currently frozen modules with version and freeze date
- References the freeze ceremony that declared each layer frozen
- Referenced by `.ai/policies/project_boundaries.md` for modification enforcement

## Frozen Layers

*(No layers are frozen at workspace initialization. Entries will be added as stages complete and layers are declared frozen.)*

### Freeze Entry Template
When adding a new frozen layer:

```
| Module | Path | Stage | Version | Frozen Date |
|--------|------|-------|---------|-------------|
| {name} | {path} | {stage_id} | {version} | {YYYY-MM-DD} |
```

## Frozen Layer List

| Module | Path | Stage | Version | Frozen Date |
|--------|------|-------|---------|-------------|
| *(none yet)* | | | | |

## Frozen Layer Map
```
(No layers currently frozen)
```

## Update Rules
- Only add entries during release/freeze ceremonies
- Only remove entries through formal unfreeze process (see `.ai/policies/project_boundaries.md`)
- Each freeze must reference the architecture decision that authorized it

## Future Update Notes
- Populate as stages reach freeze status
- Consider adding dependency impact analysis for each frozen layer
- May integrate with automated frozen layer violation detection