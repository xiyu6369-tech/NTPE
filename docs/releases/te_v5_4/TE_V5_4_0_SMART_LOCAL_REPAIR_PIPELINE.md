# TE v5.4.0 Smart Local Repair Pipeline

TE v5.4.0 reduces unnecessary provider calls after the existing deterministic
normalization and literary cleanup stages.

Naturalness-only and locally repairable orthography/formatting issues are saved
as `accepted_with_warnings` instead of retranslating the entire chunk. Potential
omission, Hangul residue, terminology loss, exact/semantic repetition, and
quality-lock violations remain provider-blocking.

The stage does not call a provider, delete text, invent content, or alter the
NVIDIA timeout, 40 RPM limiter, capacity backpressure, or resume behavior.
