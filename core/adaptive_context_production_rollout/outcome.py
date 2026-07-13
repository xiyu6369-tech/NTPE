from __future__ import annotations

from dataclasses import dataclass


OUTCOME_VERSION = "7.0.0-stage08.4.1"


@dataclass(frozen=True)
class ProductionOutcome:
    """Redacted, immutable QA/quality outcome for ACE-activated chunks only."""

    observed_chunks: int = 0
    activated_chunks: int = 0
    qa_accepted: int = 0
    qa_retry_required: int = 0
    qa_failed: int = 0
    quality_scores: tuple[int, ...] = ()
    baseline_quality_scores: tuple[int, ...] = ()
    new_issue_codes: tuple[str, ...] = ()
    omission_issues: tuple[str, ...] = ()
    unsupported_detail_issues: tuple[str, ...] = ()
    anchor_mismatch_count: int = 0
    replacement_count: int = 0
    provider_timeout: int = 0
    provider_503: int = 0
    evidence_complete: bool = False
    sampled_not_activated_chunks: int = 0
    resume_chunks: int = 0
    provider_incomplete_chunks: int = 0
    baseline_covered_chunks: int = 0
    evidence_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "quality_scores", "baseline_quality_scores", "new_issue_codes", "omission_issues",
            "unsupported_detail_issues", "evidence_reasons",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))

    @property
    def qa_failure_rate(self) -> float | None:
        total = self.qa_accepted + self.qa_retry_required + self.qa_failed
        return self.qa_failed / total if total else None

    def to_dict(self) -> dict[str, object]:
        return {
            "version": OUTCOME_VERSION,
            "observed_chunks": self.observed_chunks,
            "activated_chunks": self.activated_chunks,
            "sampled_not_activated_chunks": self.sampled_not_activated_chunks,
            "resume_chunks": self.resume_chunks,
            "provider_incomplete_chunks": self.provider_incomplete_chunks,
            "baseline_covered_chunks": self.baseline_covered_chunks,
            "qa_accepted": self.qa_accepted,
            "qa_retry_required": self.qa_retry_required,
            "qa_failed": self.qa_failed,
            "quality_scores": list(self.quality_scores),
            "baseline_quality_scores": list(self.baseline_quality_scores),
            "new_issue_codes": list(self.new_issue_codes),
            "omission_issues": list(self.omission_issues),
            "unsupported_detail_issues": list(self.unsupported_detail_issues),
            "anchor_mismatch_count": self.anchor_mismatch_count,
            "replacement_count": self.replacement_count,
            "provider_timeout": self.provider_timeout,
            "provider_503": self.provider_503,
            "evidence_complete": self.evidence_complete,
            "evidence_reasons": list(self.evidence_reasons),
            "content_redacted": True,
        }
