NTPE Root Migration Map (RM-2)

Date: 2026-07-27T13:53:33+08:00

Scope: First-priority group: all launcher_*.py files (full) and initial key ntpe_*.py entries (selected core utilities and production entries). This deliverable is READ-ONLY: no files were moved, renamed or modified.

Deliverables produced:
- docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json  (contains per-file entries for launcher_*.py)
- docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.md   (this document)

Summary (launcher files):
- Launcher files discovered at repository root: 23 entries (launcher_*.py)
- Of these, the ones with evidence of runtime/artifact references (therefore requiring wrapper if moved):
  - launcher_pipeline.py (artifact+runtime references in config/manifests/docs) — requires wrapper
  - launcher_pipeline_production.py (artifact+runtime references in manifests/artifacts/config) — requires wrapper
  - launcher_translate.py (referenced in artifacts/docs/COMMAND_BUILDER) — requires wrapper
- All other launcher_*.py files are relatively self-contained launchers that are not imported by other modules (no import matches found across repository) and have no manifest/artifact references detected in this initial scan. They are candidates for MOVE with low risk, provided wrappers are created for any entrypoints used externally.

How the JSON fields are derived:
- file: filename in repository root
- category: high-level classification (launcher / production_entry / validator / provider_utility / utility)
- destination: proposed relocation (only a suggestion; directories not created in this read-only phase)
- imports: list of modules or qualified imports observed in the file header (parsed from the file top). For launcher files these were extracted by reading the file.
- runtime_reference: true if "python <file>" or similar command usage or runtime invocation was found in docs/manifests/artifacts.
- artifact_reference: true if the filename appears in artifacts/, manifests/, docs/ or config files.
- safe_to_move: heuristically true when there is no evidence of being imported by other modules and no artifact/runtime references. When false, moving requires refactor or wrapper.
- requires_wrapper: true when artifact_reference or runtime_reference are true (these indicate external callers expect the script to remain addressable at root). Also true when tests import the module by name.

Limitations and next steps (RM-2 continuation):
- This initial JSON currently contains complete entries for all launcher_*.py files. A follow-up automated pass should produce per-file entries for all root ntpe_*.py files (there are many) with the same evidence-gathering process (parse imports, search for imports-by-others, search for runtime/artifact references).
- The follow-up pass should:
  1. For each root ntpe_*.py file, collect its imports (top of file), and search the repo for:
     - exact import occurrences ("import <module>" / "from <module> import") — marks import_by_others
     - filename occurrences in artifacts/, manifests/, docs/ or config/ — marks artifact_reference
     - command-line usages like "python <file>" in docs or artifacts — marks runtime_reference
  2. Based on evidence, set safe_to_move and requires_wrapper.
  3. Output a full NTPE_ROOT_MIGRATION_MAP.json that covers both first and second groups.

Counts (current JSON content):
- Launcher entries: 23
- Production-entry launchers requiring wrapper: 3 (pipeline, pipeline_production, translate)
- Safe-to-move launcher candidates: 20

Validation / Git status expectations (after creating these files):
- Allowed changes in working tree:
  ?? docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.md
  ?? docs/governance/migration/NTPE_ROOT_MIGRATION_MAP.json
- No other file modifications made.

Notes and next action offer:
- If approve, run a full automated pass to generate a complete NTPE_ROOT_MIGRATION_MAP.json that includes all root ntpe_*.py files and the second-group stage patterns (ntpe_stage*, ntpe_te_*, ntpe_lcr*, ntpe_tic*, ntpe_ps*, ntpe_ter*).
- That automated pass will take longer (many files) but will produce the exhaustive map required to safely proceed to RM-3 migration.

Prepared by: AI assistant using Copilot CLI runtime in VS Code
