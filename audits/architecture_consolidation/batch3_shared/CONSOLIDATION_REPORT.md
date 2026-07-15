# Batch 3 Shared Utilities Pilot

Batch 3 creates a standard-library-only `core.shared.evidence` package and migrates only the two Batch 1 packaging tools. No production, runtime, provider, prompt, Stage 11, Stage 12.1 candidate, frozen schema, or historical artifact is migrated or rewritten.

## Pilot scope

- Canonical UTF-8 JSON with deterministic compact bytes and atomic replacement.
- Streaming SHA-256 for files plus bytes/text hashing and strict lowercase digest validation.
- Deterministic `/` project-relative paths with resolved containment and symlink escape protection.
- Tooling migration: `tools/package_source.py` and `tools/package_audit.py` only.

## Compatibility

CLI arguments, defaults, report fields, Git tracked-only behavior, Git HEAD fail-closed behavior, explicit untracked opt-in, audit allowlists, secret detection, traversal defense, Unicode ZIP names, and ZIP integrity checks remain in place. Report JSON formatting becomes canonical and compact; its schema and semantics are unchanged.

## Deliberately not migrated

All production and historical domain helpers remain untouched because Batch 3 is a low-risk tooling pilot. Batch 4 is not started.

## Boundary declaration

```text
production_code_modified = false
runtime_modified = false
provider_modified = false
prompt_modified = false
candidate_modified = false
stage11_modified = false
frozen_schema_modified = false

shared_utility_created = true
migrated_tooling_files = 2
historical_modules_migrated = 0

provider_executed = false
new_translation_generated = false

package_inventory_changed = false
package_security_regressed = false

tracked_files_deleted = 0
batch4_started = false
```
