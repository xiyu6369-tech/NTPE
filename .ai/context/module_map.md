# Context: module_map

## Title
NTPE Module Map — Key Module Responsibilities

## Purpose
This context file maps the major modules and directories in NTPE to their responsibilities. AI agents use this to locate where to make changes and understand which modules are affected by modifications.

## Scope
- Key directories and their purposes
- Major module families and their roles
- Does not enumerate every file; see `.ai/memory/module_index.md` for detailed index

## Module Map

### Project Root (`/`)
| Module Family | Responsibility |
|---------------|----------------|
| `launcher*.py` | Pipeline entry points, orchestration scripts |
| `ntpe_launcher.py` | Main launcher / CLI entry |
| `ntpe_batch_monitor.py` | Batch translation monitoring |
| `ntpe_plugin_marketplace.py` | Plugin marketplace integration |
| `ntpe_literary_*.py` | Literary evaluation and regression |
| `ntpe_provider_*.py` | Provider setup, audit, verification |
| `ntpe_production_*.py` | Production translation execution |
| `ntpe_lts_*.py` | Long-term support release management |
| `ntpe_te_*.py` | Translation Engine stage tests and freeze |
| `ntpe_ter_*.py` | Translation Engine Refinement tests |
| `ntpe_stage*.py` | Stage-specific test suites |
| `ntpe_lcr_*.py` | Legacy Capability Recovery tests |

### `core/`
Foundation modules: data structures, type contracts, shared utilities.

### `engine/`
Translation engine, quality engine, intelligence modules, prompt construction.

### `config/`
Configuration files and contracts.

### `integration/`
External service integration, provider abstraction.

### `external_api/`
Provider API adapters.

### `cli/`
Command-line interface modules.

### `gui/`
Graphical user interface modules.

### `data/`
Data files: character databases, glossaries, overrides.

### `input/`
Input novels / source text.

### `final_output/`
Translation output.

### `memory/`
Translation memory and state persistence.

### `manifests/`
Release manifests and version documents.

### `docs/`
Project documentation.

### `.ai/`
AI workspace governance files (this workspace).

## Future Update Notes
- Update when new major modules or directories are added
- Keep in sync with `.ai/memory/module_index.md` for detailed listing
- Consider adding dependency graph visualization