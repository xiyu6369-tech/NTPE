# NTPE Architecture Consolidation Batch 1 Hygiene Report

Date: 2026-07-15 (Asia/Taipei)

## Deleted under explicit Batch 1 authority

- ignored `NTPE.zip`: 587,775,785 bytes;
- `.pytest_cache`: rebuildable local test cache;
- empty `.ntpe_test_sandbox`: rebuildable test staging;
- one untracked accidental command-output filename: reproducible Git output with no audit or user-data value.

The non-`.git` worktree fell from approximately 606.8 MiB to 18.521 MiB after
the initial cleanup. Test-created `.pytest_cache` is removed again before final
delivery.

## Deliberately retained

- `NTPE_ARCHITECTURE_AUDIT.zip`: prior architecture audit evidence;
- ignored Provider and regression evidence;
- `backup/`, input, resume, character-memory, and other user/private data;
- all tracked files, Stage 11 modules, Stage 12 Candidate, production paths,
  Provider authorization/redaction evidence, and release anchors.

No tracked artifact was moved or deleted. No broad cache or artifact directory
was removed merely because it was ignored.
