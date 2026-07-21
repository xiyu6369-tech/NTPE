# Context: architecture

## Title
NTPE High-Level Architecture

## Purpose
This context file describes the high-level architecture of NTPE for AI agents. It identifies the major architectural layers, their responsibilities, and their relationships. Agents use this to understand where changes should be made and how modules interconnect.

## Scope
- High-level architectural description
- Layer definitions and boundaries
- Inter-layer dependency rules
- Referenced by all profiles for orientation

## Architecture Layers

### Layer 1: Core
Fundamental building blocks shared across all layers.
- Data structures, type definitions, utility functions
- Configuration contracts
- Shared constants and enumerations
- **Rule**: No dependencies on upper layers
- **Directory**: `core/`, `config/`

### Layer 2: Engine
Translation and quality processing logic.
- Translation engine: prompt construction, chunk management
- Quality engine: semantic verification, style evaluation, repetition detection
- Intelligence modules: context, narrative, character awareness
- **Rule**: Depends on Core only
- **Directory**: `engine/`

### Layer 3: Provider
AI provider abstraction and orchestration.
- Provider interface contracts
- Multi-provider routing and failover
- Observability, auditing, benchmarking
- Security and credential management
- **Rule**: Depends on Core, Engine interfaces
- **Directory**: `integration/`, `external_api/`

### Layer 4: Runtime
Execution management and job orchestration.
- Job scheduler and retry queue
- Resource optimizer
- Resume/recovery journal
- Performance dashboard
- **Rule**: Depends on Core, Engine, Provider
- **Directory**: `cli/`, project root launcher files

### Layer 5: Launcher
Entry points and pipeline orchestration.
- Pipeline scripts for different translation modes
- CLI interface
- Batch monitoring
- **Rule**: Depends on all lower layers
- **Directory**: Project root (`launcher*.py`, `ntpe_launcher.py`)

### Layer 6: Enterprise
Deployment, configuration, and documentation framework.
- Configuration center
- Deployment profiles and orchestration
- Documentation center
- Validation and monitoring
- **Rule**: Depends on all lower layers
- **Directory**: `enterprise/` (in docs), `manifests/`

## Dependency Direction
```
Enterprise → Launcher → Runtime → Provider → Engine → Core
```
Dependencies flow upward only. Lower layers must never import from upper layers.

## Frozen Layer Status
See `.ai/memory/frozen_layers.md` for the authoritative list of which specific modules within these layers are currently frozen.

## Future Update Notes
- Update when new architectural layers are introduced
- Update when layer boundaries are redefined
- Keep in sync with `.ai/context/module_map.md`