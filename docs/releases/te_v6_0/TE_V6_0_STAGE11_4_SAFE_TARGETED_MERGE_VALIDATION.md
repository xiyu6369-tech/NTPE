# TE v6.0 Stage 11.4 — Safe Targeted Merge Validation

Adds a fail-closed validation boundary for targeted retry merges. The validator confirms explicit translated ranges, preserves untouched prefix/suffix text, rejects empty or implausible replacements, and blocks high-overlap boundary duplication before the merged candidate enters the existing Unified Quality Gate.

No Provider, Prompt, score, decision, timeout, rate-limit, or resume behavior is changed.
