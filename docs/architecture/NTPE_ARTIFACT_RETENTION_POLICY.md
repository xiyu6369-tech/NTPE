# NTPE Artifact Retention Policy

Status: Architecture Consolidation Batch 1  
Effective date: 2026-07-15

This policy classifies artifacts without moving or deleting tracked artifacts.
Retention depends on reference, integrity, human review, Provider/security
evidence, reproducibility, and rollback value—not merely age or a Frozen label.

## Active

Keep in the active repository when required by current compatibility or release
validation:

- current release anchors and latest freeze artifacts;
- production-required fixtures and schemas;
- approved human reviews and reviewer provenance;
- Golden Corpus records and their integrity chain.

## Audit

Retain as immutable audit evidence, preferably with SHA-256 and a manifest:

- Provider execution records;
- timeout and failure evidence;
- authorization, redaction, and security-boundary evidence;
- release manifests and human review decisions.

Raw Provider payloads and responses must not be copied into routine Audit
Packages. References and hashes are preferred.

## Rebuildable

These may be regenerated when their inputs and deterministic tool version are
preserved:

- execution-package templates;
- generated prompt profiles;
- deterministic reports;
- packaging inventories and parity reports;
- local cache and package staging.

Rebuildable does not automatically mean delete eligible. A report that anchors
a release, human review, or Provider failure remains Audit or Active.

## Archive

Move outside the active worktree only through a separately reviewed migration:

- historical Stage artifacts;
- older freeze artifacts;
- evidence whose assertions are fully covered by a later freeze;
- historical regression output that is useful for comparison but not daily use.

An archive must have an inventory, SHA-256 values, source Stage, storage
location, retention period, and restoration instructions.

## Delete-eligible

Deletion is allowed only when every condition is true:

1. the path is untracked;
2. no import, configuration, manifest, test, document, or artifact references it;
3. it is completely rebuildable;
4. it contains no human review or approval;
5. it has no Provider, timeout, authorization, redaction, or security audit value;
6. it is not a release anchor, resume state, user input, or private data.

Tracked files are proposal-only in Batch 1. No tracked artifact may be moved or
deleted in this batch.

## Batch 1 decisions

- The ignored full-worktree `NTPE.zip` is delete eligible by explicit Batch 1
  authorization and must not be recreated.
- `.pytest_cache`, temporary package staging, and empty test sandboxes are
  delete eligible.
- Existing Provider evidence, Stage 11 anchors, Stage 12 execution evidence,
  input, character memory, resume data, and ignored historical regression
  output are retained.
