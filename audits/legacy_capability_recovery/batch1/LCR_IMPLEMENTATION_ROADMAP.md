# LCR Implementation Roadmap

## LCR Batch 2 — Character Memory V2

- Direct quality value: Evidence-governed character/voice continuity
- Performance gate: token budget and local lookup benchmark
- Timeout gate: network requests=0 in design and offline tests
- Regression gate: current regressions plus false-persona cases
- Production boundary: design/isolated module only; no prompt/runtime hookup

## LCR Batch 3 — Context/Scene Memory Integration

- Direct quality value: merge approved character and scene evidence with Adaptive Context
- Performance gate: bounded context tokens
- Timeout gate: no provider request increase
- Regression gate: ko/ja/en context regressions
- Production boundary: disabled integration adapter only

## LCR Batch 4 — Chunk Cache V2

- Direct quality value: avoid retranslation of verified identical chunks
- Performance gate: cache lookup/write benchmark
- Timeout gate: retry only failed chunk
- Regression gate: resume/output ordering and stale-cache rejection
- Production boundary: reuse current ResumeJournal and collector

## LCR Batch 5 — Dual-pass Draft/Polish Prototype

- Direct quality value: observable draft and selective polish
- Performance gate: single vs selective vs dual benchmark
- Timeout gate: hard session budget
- Regression gate: semantic rollback corpus
- Production boundary: offline/mock prototype only

## LCR Batch 6 — Post-polish Semantic Verification

- Direct quality value: prevent polish omissions/additions
- Performance gate: local/offline gate cost
- Timeout gate: no automatic provider retry
- Regression gate: TIC semantic defects
- Production boundary: no production activation

## LCR Batch 7 — Multilingual Profiles

- Direct quality value: ko/ja/en-specific continuity and names
- Performance gate: profile token/latency budgets
- Timeout gate: no routing changes
- Regression gate: language-specific golden cases
- Production boundary: profile data only

## LCR Batch 8 — Controlled Provider Routing

- Direct quality value: evaluate availability without silent quality change
- Performance gate: routing benchmark
- Timeout gate: bounded attempts and timeout
- Regression gate: provider consistency/secret safety
- Production boundary: explicit authorization; disabled by default

## LCR Batch 9 — Offline Golden/TIC Validation

- Direct quality value: prove direct quality value
- Performance gate: offline evaluation budget
- Timeout gate: network requests=0
- Regression gate: active regression and human-reviewed goldens
- Production boundary: offline only

## LCR Batch 10 — Production Integration

- Direct quality value: only evidence-proven capabilities
- Performance gate: production latency gate
- Timeout gate: bounded provider budget
- Regression gate: full freeze ladder and rollback drill
- Production boundary: separate explicit authorization required

Batch 1 implements none of these. The first implementation batch is Character Memory V2 only.
