# NTPE 1.2 Professional — Stage-16.6 Adaptive Translation Strategy

Stage-16.6 adds the Adaptive Translation Strategy layer for selecting translation behavior from content type, context signals, narrative state, character signals, quality risks, memory signals, and provider capabilities.

## Added

- `AdaptiveTranslationStrategyEngine`
- Strategy context, policy, profile, selector, result, metrics, events, and exceptions
- Content classification for novel, dialogue, technical, mixed, and general content
- Explainable strategy selection with confidence and fallback strategy
- Stage launcher test

## Compatibility

This stage is additive only and does not modify Foundation v1.0, NTPE 1.1 LTS, Stage-14 Provider Framework, or Stage-15 Translation Quality Engine public contracts.
