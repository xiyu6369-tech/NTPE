# TE v4.3 Stage-4.3.2 Runtime Hook Admission Adapter

Adds a metadata-only admission adapter for runtime shadow hook requests.

The adapter rejects unsafe callers, non-shadow modes, multi-chunk requests, and
recursive forbidden inputs. It never executes recovery or real translation.
