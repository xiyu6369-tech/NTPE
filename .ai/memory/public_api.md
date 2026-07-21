# Memory: public_api

## Title
NTPE Public API Index — API Surface Documentation

## Purpose
This memory file tracks the public API surface of NTPE modules. It records function signatures, class interfaces, and contracts that other modules depend on. Changes to documented APIs require architecture decisions.

## Scope
- Public functions, classes, and constants
- Module-level import paths
- Configuration contracts
- Does not document private/internal implementation details

## API Index Template
When adding a new API entry:

```
### Module: `{module_path}`
- **Status**: {STABLE / EXPERIMENTAL / DEPRECATED}
- **Since**: {stage_id or date}

#### `{function_name}({params}) -> {return_type}`
- **Purpose**: {one-line description}
- **Consumers**: {list of modules that use this API}
```

## Currently Documented APIs

*(This index will be populated as part of API audit activities. On initialization, no APIs are documented — the workspace is new.)*

## Update Rules
- Add entries when new public APIs are created
- Mark as DEPRECATED (with migration path) before removal
- Update status when APIs stabilize or change
- Any breaking change must reference the architecture decision record

## Future Update Notes
- Populate during comprehensive API audit
- Consider automated API surface extraction
- May integrate with compatibility testing framework