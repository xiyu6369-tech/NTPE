# Policy: project_boundaries

## Title
Project Boundaries — Frozen Layers and Modification Scope

## Purpose
This policy defines which parts of the NTPE codebase are frozen (immutable) and which are open for modification. It establishes the principle of layered stability: core layers are locked to prevent regressions, while outer layers remain flexible for ongoing development.

## Scope
- Applies to all agent profiles and all development stages
- Violations trigger immediate stop condition (per `.clinerules`)
- Updated only during formal release/freeze ceremonies

## Frozen Layers

Frozen layers are modules, directories, or files that must never be modified by an AI agent without explicit human authorization during a freeze ceremony.

### Currently Frozen
See `.ai/memory/frozen_layers.md` for the authoritative, up-to-date list of frozen modules.

### Freeze Criteria
A layer becomes frozen when:
- It has passed full acceptance and regression testing
- It is declared FROZEN in a formal release ceremony
- It is documented in `.ai/memory/frozen_layers.md` with version and date

### Unfreeze Process
A frozen layer can only be unfrozen through:
- A formal architecture decision (documented in `.ai/memory/architecture_decisions.md`)
- Explicit human authorization
- A new stage that explicitly lists the layer as allowed modification

## Allowed Modification Principle

### What Can Be Modified
- Non-frozen Python modules
- Test files (any, including tests for frozen modules)
- Configuration files (non-production)
- Documentation files
- `.ai/` workspace files (per profile permissions)

### What Cannot Be Modified
- Frozen layers (see `.ai/memory/frozen_layers.md`)
- `.clinerules` (unless stage explicitly authorizes workspace infrastructure changes)
- `.clineignore` (unless stage explicitly authorizes)
- `.editorconfig` (unless stage explicitly authorizes)
- Production configuration files
- Manifests of released/frozen stages

## Backward Compatibility

All modifications to non-frozen code must maintain backward compatibility with frozen layers:
- Public APIs of frozen modules must not be broken
- Import paths of frozen modules must remain valid
- Data formats consumed by frozen modules must remain compatible
- Test suites for frozen modules must continue to pass

Any change that requires modifying a frozen layer to maintain compatibility must be escalated to human review.

## Future Update Notes
- Frozen layer list will grow as more stages reach release/freeze
- Consider adding compatibility contract definitions for major module boundaries
- May introduce "soft freeze" concept for modules in pre-release stabilization