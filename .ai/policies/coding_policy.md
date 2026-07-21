# Policy: coding_policy

## Title
Coding Policy — Python Style and Public API Standards

## Purpose
This policy defines the coding standards that all AI agents must follow when writing or modifying Python code in the NTPE project. It ensures consistency, readability, and maintainability across all agent contributions.

## Scope
- Applies to implement and architecture profiles when producing code
- Referenced during review and audit profiles when evaluating code
- All new and modified Python code must comply

## Python Style

### Formatting (per `.editorconfig`)
- UTF-8 encoding for all source files
- LF line endings
- 4-space indentation (no tabs)
- Trailing whitespace trimmed

### Naming Conventions
- **Modules**: `snake_case` (e.g., `launcher_pipeline.py`, `ntpe_batch_monitor.py`)
- **Classes**: `PascalCase` (e.g., `TranslationPipeline`, `ProviderOrchestrator`)
- **Functions/Methods**: `snake_case` (e.g., `run_translation()`, `validate_input()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`)
- **Private Members**: `_leading_underscore` (e.g., `_internal_cache`, `_validate_token()`)
- **Test Files**: `*_test.py` suffix

### File Structure (recommended order)
1. Module docstring
2. Imports (stdlib → third-party → project modules)
3. Constants and type aliases
4. Classes and functions
5. `if __name__ == "__main__":` block (if applicable)

### Documentation
- All public functions and classes must have docstrings
- Use PEP 257 conventions for docstrings
- Complex logic should have inline comments explaining intent (not mechanics)

## Public API Compatibility

### Stability Rule
Once a public API is documented in `.ai/memory/public_api.md`, it must not be broken without:
- An architecture decision record (`.ai/memory/architecture_decisions.md`)
- Explicit human authorization
- A migration path for existing consumers

### What Constitutes a Public API
- Function/class names imported by other modules
- Function signatures (parameter names, types, defaults)
- Return types and exception contracts
- Module import paths
- Configuration file formats consumed by multiple modules

### Backward Compatibility Requirements
- New parameters must have default values (no breaking existing callers)
- Deprecated APIs must emit warnings for at least one release cycle before removal
- Return types may be extended but not narrowed
- Exception types may be specialized but not generalized (catch existing handlers)

## Code Quality Principles
- Prefer readability over cleverness
- Single responsibility: each function/class should do one thing well
- Avoid deep nesting (prefer early returns/guard clauses)
- Keep functions focused and reasonably sized
- Use type hints where they add clarity
- Handle errors explicitly; avoid bare `except:`

## Future Update Notes
- May adopt a formal style guide (e.g., PEP 8 with project-specific amendments)
- Consider adding automated linting to validation workflow
- Type hint coverage may become mandatory as the codebase matures