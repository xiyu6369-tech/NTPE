# NTPE Foundation Compatibility Policy

Foundation v1.0 is a stable baseline. Product stages, CLI, SDK, GUI, and future integrations must depend on Foundation through the frozen contracts.

## Compatibility Rules

1. Existing public APIs remain available.
2. New behavior must be additive unless a compatibility fix requires otherwise.
3. Foundation contracts must not depend on upper product layers.
4. Product layers may depend on Foundation, but Foundation must remain independent.
5. Any future Foundation v1.0.x patch must preserve API level 1 compatibility.

## Stable Contract Areas

- Runtime
- Context Pipeline
- Prompt Pipeline
- Plugin System
- Production Pipeline
- Translation Runtime Core
- Intelligence Layer
- Knowledge Layer
- Snapshot and persistence contracts

## Patch Versioning

Use patch tags for fixes:

```text
foundation-v1.0.1
foundation-v1.0.2
foundation-v1.0.3
```
