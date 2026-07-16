# LCR Batch 1 — Legacy Capability Recovery Audit

Status: COMPLETE (audit/design only).

Legacy capabilities inventoried: 27.

## Findings

- Legacy dynamic character extraction adds unverified AI traits to an append-only memory and can pollute later prompts.
- The fixed previous-translation tail has continuity value but should merge into Adaptive Context, not become a parallel context engine.
- Temp chunk files reduce reruns but accept stale output by existence alone; Chunk Cache V2 requires content and policy hashes.
- Legacy three-step draft/review/polish is one opaque request, not a true dual pass.
- Academic degraded fallback and automatic unknown-name transliteration violate the current literary/evidence quality contract.
- Current Resume/Recovery, chunking, assembly, glossary, semantic verification, quality retry, encoding and batch flow remain authoritative.

## Security

Credential exposure was detected in the supplied legacy source. The review copy is redacted; the value was not tested or stored. Rotate/revoke the credential.

## Boundary

Provider executed: false; network requests: 0; new translation generated: false. Production, Runtime, Provider, Prompt, QA Engine and TIC are unchanged. LCR Batch 2 was not started.
