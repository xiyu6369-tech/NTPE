# PS-04 Narrative & Character Understanding Engine

PS-04 introduces NTPE's first narrative-aware literary prompt layer.

## Purpose

The goal is to improve translation quality before the API call by giving the model structured context:

- literary translation policy
- narrative perspective and scene hints
- psychological and lexical hints
- character context
- subject / pronoun hints
- locked glossary and forbidden aliases

## Core Principle

NTPE should not force a regional Chinese wording style.  It should translate Korean novels into natural Traditional Chinese that fits the work's era, culture, character identity, and narrative tone.

## Validation

PS-04 is validated with:

- Smoke Set
- Golden Set
- Regression Set
- prompt package integration tests
- manual comparison of Golden Set translation quality
