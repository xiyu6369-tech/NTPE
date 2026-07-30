# LCR Batch 2 — Character Memory V2 Offline Core

Status: implemented and tested offline; not production-integrated.

## Public API

`SCHEMA_VERSION`, `DEFAULT_PROMPT_TOKEN_BUDGET`, `MAX_EVIDENCE_EXCERPT_CHARS`, `AddDisposition`, `AddResult`, `ApprovalMetadata`, `ApprovalStatus`, `CharacterMemoryValidationError`, `ConflictRecord`, `Evidence`, `EvidenceType`, `ExpiryKind`, `ExpiryPolicy`, `FactType`, `MemoryRecord`, `MemoryStatus`, `MemoryStore`, `PromptMemoryItem`, `SelectionResult`, `add_or_merge_memory`, `approve_memory`, `create_evidence`, `create_memory`, `deserialize_memory_store`, `estimate_memory_tokens`, `expire_memory`, `reject_memory`, `rollback_memory`, `select_prompt_eligible_memories`, `serialize_memory_store`, `supersede_memory`, `validate_memory_store`, `validate_record`

## Governance

- Structured evidence, confidence, and approval are separate.
- AI inference remains pending and prompt-ineligible by default.
- Human-approved facts have highest priority and require explicit approval metadata.
- Deterministic normalization/dedup merges evidence but never silently merges conflicting values.
- Same-tier conflicts remain visible and prompt-ineligible until explicit resolution.
- Temporal/location facts cannot default to permanent expiry.
- Rollback restores prior versions without deleting evidence history.

## Prompt eligibility

Selection is offline-only and defaults to 256 estimated tokens. Rejected, expired, rolled-back, invalid, unresolved, incomplete, low-confidence, out-of-scope, and default AI-inference records are excluded. Over-budget records are omitted without rewriting facts.

## Boundaries

No Runtime, Provider, Prompt, QA, TIC production API, Resume, Output Assembly, CLI, or Web UI integration. No network request or translation generation. LCR Batch 3 is not started.

## Known limitations

No automatic extraction, unknown-name transliteration, entity merge, Scene Memory, Context injection, Chunk Cache, Dual-pass, or multilingual profiles. Token cost is a deterministic estimate, not a provider tokenizer.
