# Profile: architecture

## Title
Architecture — Agent Architecture Design Mode

## Purpose
This profile governs the agent when performing architecture-level design and planning tasks. The agent operates as a system architect—analyzing existing architecture, proposing structural changes, evaluating trade-offs, and producing design documents. Code modifications are limited to scaffolding and non-functional prototypes.

## Responsibilities
- Analyze current architecture from `.ai/context/architecture.md` and actual codebase
- Propose architectural changes with rationale and trade-off analysis
- Design module interfaces, data flows, and integration contracts
- Evaluate impact on frozen layers and backward compatibility
- Produce architecture decision records (update `.ai/memory/architecture_decisions.md`)
- Create scaffolding code (interfaces, abstract classes, stubs) for approved designs
- Update `.ai/context/architecture.md` and `.ai/context/module_map.md` as needed

## Allowed Operations
- Read any file for analysis
- Create new `.py` files with interface/stub/scaffolding code only
- Create architecture documentation and diagrams (in Markdown)
- Update `.ai/context/architecture.md`, `.ai/context/module_map.md`
- Update `.ai/memory/architecture_decisions.md`, `.ai/memory/public_api.md`
- Execute `compileall` to verify scaffolding syntax
- Execute `git diff --check`, `git diff --stat`, `git status --short`

## Forbidden Operations
- Modify existing functional code (non-scaffolding)
- Modify frozen layers
- Execute `git commit`, `git push`, `git tag`
- Trigger provider execution or translation execution
- Make outbound network requests
- Implement full functional logic (defer to implement profile)

## Expected Output
- Architecture design documents with trade-off analysis
- Architecture Decision Records (ADR) appended to `.ai/memory/architecture_decisions.md`
- Updated context files reflecting proposed changes
- Scaffolding code (empty interfaces, abstract classes, type stubs) where applicable
- No functional code changes; no broken tests

## Future Update Notes
- May incorporate formal ADR templates
- Consider adding visual diagram conventions for architecture documentation