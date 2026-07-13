from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Mapping

from .config import ProviderEvidenceConfig
from .model import ProviderEvidenceBundle, ProviderRequestIdentity, ProviderTimingEvidence
from .timing import normalize_utc, request_elapsed_ms
from .token_usage import collect_token_usage, output_tokens

_SUCCESS = {"success", "accepted"}


@dataclass(frozen=True)
class ProviderAttemptHandle:
    identity: ProviderRequestIdentity
    started_ns: int
    started_at_utc: str


def _error_category(result: Mapping[str, object]) -> tuple[str, int | None, bool]:
    error = str(result.get("error", "")).lower()
    raw_http = result.get("http_status", result.get("status_code"))
    try: http_status = int(raw_http) if raw_http is not None else None
    except (TypeError, ValueError): http_status = None
    if "timeout" in error or "timed out" in error:
        return "timeout", http_status, True
    if http_status is not None and http_status >= 400:
        return f"http_{http_status}", http_status, http_status in {429, 500, 502, 503, 504}
    if error:
        return "provider_error", http_status, True
    return "", http_status, False


@dataclass
class ProviderEvidenceCollector:
    config: ProviderEvidenceConfig

    def __post_init__(self) -> None:
        self._records: list[ProviderTimingEvidence] = []
        self._excluded: list[dict[str, object]] = []

    def begin_attempt(
        self, identity: ProviderRequestIdentity, *, started_ns: int | None = None,
        started_at_utc: str | None = None,
    ) -> ProviderAttemptHandle:
        blockers = self.config.validate()
        if blockers:
            raise ValueError(",".join(blockers))
        return ProviderAttemptHandle(
            identity=identity,
            started_ns=time.perf_counter_ns() if started_ns is None else int(started_ns),
            started_at_utc=started_at_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )

    def finish_attempt(
        self, handle: ProviderAttemptHandle, result: Mapping[str, object], *,
        finished_ns: int | None = None, finished_at_utc: str | None = None,
    ) -> ProviderTimingEvidence | None:
        ended = time.perf_counter_ns() if finished_ns is None else int(finished_ns)
        payload = dict(result)
        payload["provider_elapsed_ms"] = round(max(0, ended - handle.started_ns) / 1_000_000, 3)
        payload["provider_started_at"] = handle.started_at_utc
        payload["provider_finished_at"] = finished_at_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self.collect_attempt(handle.identity, payload)

    def collect_attempt(self, identity: ProviderRequestIdentity, result: Mapping[str, object]) -> ProviderTimingEvidence | None:
        blockers = self.config.validate()
        if blockers:
            raise ValueError(",".join(blockers))
        if identity.pair_id != self.config.pair_id or identity.run_kind != self.config.run_kind:
            raise ValueError("provider-evidence-identity-contract-mismatch")
        if identity.chunk_index < 1 or identity.attempt < 1 or not identity.model:
            raise ValueError("provider-evidence-identity-invalid")
        if identity.resumed:
            self._excluded.append({
                "set_name": identity.set_name, "chunk_index": identity.chunk_index,
                "source_hash": identity.source_hash, "chunk_hash": identity.chunk_hash,
                "reason": "resume-chunk-excluded",
            })
            return None
        usage = collect_token_usage(result)
        category, http_status, external = _error_category(result)
        status = str(result.get("status", "failed")).strip().lower()
        elapsed = request_elapsed_ms(result)
        model = str(result.get("provider_model") or identity.model)
        record = ProviderTimingEvidence(
            pair_id=identity.pair_id, run_kind=identity.run_kind, set_name=identity.set_name,
            chunk_index=identity.chunk_index, source_hash=identity.source_hash, chunk_hash=identity.chunk_hash,
            model=model, attempt=identity.attempt, status=status, elapsed_ms=elapsed,
            started_at_utc=normalize_utc(result.get("provider_started_at")),
            finished_at_utc=normalize_utc(result.get("provider_finished_at")),
            error_category=category, http_status=http_status, external_provider_condition=external,
            fallback_used=bool(result.get("fallback_used", model != identity.model)), token_usage=usage,
            suspicious_short_output=bool(
                status in _SUCCESS and identity.minimum_output_tokens > 0 and output_tokens(usage) < identity.minimum_output_tokens
            ),
            real_provider_execution=self.config.real_provider_execution,
        )
        self._records.append(record)
        return record

    def bundle(self) -> ProviderEvidenceBundle:
        limitations: list[str] = []
        if not self._records: limitations.append("no-provider-request-evidence")
        if any(not row.timing_complete for row in self._records): limitations.append("provider-timing-evidence-incomplete")
        if any(row.suspicious_short_output for row in self._records): limitations.append("suspicious-short-output")
        if any(row.status not in _SUCCESS for row in self._records): limitations.append("provider-run-incomplete")
        if self._records and not all(row.real_provider_execution for row in self._records): limitations.append("not-executed-with-real-provider")
        identities = {(row.pair_id, row.run_kind) for row in self._records}
        if identities and identities != {(self.config.pair_id, self.config.run_kind)}: limitations.append("provider-evidence-contract-mismatch")
        complete = bool(self._records) and not any(value in limitations for value in (
            "provider-timing-evidence-incomplete", "provider-evidence-contract-mismatch",
        ))
        ready = complete and not any(value in limitations for value in (
            "suspicious-short-output", "provider-run-incomplete", "not-executed-with-real-provider",
        ))
        status = (
            "ready_for_benchmark" if ready
            else "evidence_complete_provider_limited" if complete and "not-executed-with-real-provider" not in limitations
            else "evidence_complete_mock_only" if complete
            else "evidence_incomplete"
        )
        return ProviderEvidenceBundle(
            pair_id=self.config.pair_id, run_kind=self.config.run_kind, records=tuple(self._records),
            excluded_resume_chunks=tuple(self._excluded), status=status, evidence_complete=complete,
            ready_for_benchmark=ready, limitations=tuple(limitations),
        )

    def total_latency_ms(self) -> float:
        return round(sum(row.elapsed_ms or 0.0 for row in self._records), 3)
