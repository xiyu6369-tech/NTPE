from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class ControlledResultReplacementGuard:
    """Makes a decision for controlled mappings without mutating runtime state."""

    version = "TE-v4.4"
    stage = "4.4.4"
    name = "controlled_result_replacement_guard"
    forbidden_inputs = {"source_text", "translated_text", "text", "chunks", "api_key", "provider_client"}

    def evaluate(
        self,
        original_summary: Optional[Mapping[str, Any]] = None,
        candidate_result: Optional[Mapping[str, Any]] = None,
        config: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        original = dict(original_summary or {}) if isinstance(original_summary, Mapping) else {}
        candidate = dict(candidate_result or {}) if isinstance(candidate_result, Mapping) else {}
        candidate_summary = candidate.get("candidate_summary") if isinstance(candidate.get("candidate_summary"), Mapping) else {}
        cfg = dict(config or {}) if isinstance(config, Mapping) else {}
        max_hangul = self._int(cfg.get("max_hangul_residue", 0))
        max_duplicates = self._int(cfg.get("max_duplicate_count", 0))
        failed = []
        original_id = str(original.get("original_result_id") or "")
        checks = (
            (bool(original), "missing_original_summary"),
            (bool(original_id), "missing_original_result_id"),
            (candidate.get("status") == "controlled_execution_completed", "candidate_not_completed"),
            (candidate.get("success") is True, "candidate_not_successful"),
            (candidate_summary.get("candidate_valid") is True, "candidate_invalid"),
            (candidate_summary.get("outcome") == "success", "candidate_outcome_not_success"),
            (candidate_summary.get("quality_pass") is True, "quality_not_passed"),
            (self._int(candidate_summary.get("translated_chars")) > 0, "empty_candidate"),
            (self._int(candidate_summary.get("hangul_residue_count")) <= max_hangul, "hangul_residue_exceeded"),
            (self._int(candidate_summary.get("duplicate_count")) <= max_duplicates, "duplicate_count_exceeded"),
            (candidate.get("original_result_preserved") is True, "original_result_not_preserved"),
            (candidate.get("replacement_pending_guard") is True, "replacement_not_pending_guard"),
            (candidate.get("real_provider_request_executed") is False, "real_provider_request_executed"),
            (candidate.get("provider_fallback_executed") is False, "provider_fallback_executed"),
            (candidate.get("real_translation_executed") is False, "real_translation_executed"),
            (candidate.get("rollback_available") is True, "rollback_unavailable"),
            (str(candidate.get("original_result_id") or "") == original_id, "original_result_id_mismatch"),
            (not self._has_forbidden(original) and not self._has_forbidden(candidate), "forbidden_input_present"),
        )
        for condition, code in checks:
            if not condition:
                failed.append(code)
        allowed = not failed
        return {
            "replacement_allowed": allowed,
            "status": "replacement_approved" if allowed else "replacement_rejected",
            "stage": self.stage,
            "reason": "all_replacement_checks_passed" if allowed else failed[0],
            "failed_checks": failed,
            "original_result_id": original_id,
            "recovery_candidate_id": str(candidate.get("recovery_candidate_id") or ""),
            "original_result_preserved": True,
            "controlled_replacement_only": True,
            "replacement_scope": "single_chunk",
            "execution_allowed": False,
            "real_provider_request_allowed": False,
            "provider_fallback_allowed": False,
            "real_translation_allowed": False,
            "rollback_available": True,
            "quality_summary": {
                "translated_chars": self._int(candidate_summary.get("translated_chars")),
                "quality_pass": candidate_summary.get("quality_pass") is True,
                "hangul_residue_count": self._int(candidate_summary.get("hangul_residue_count")),
                "duplicate_count": self._int(candidate_summary.get("duplicate_count")),
            },
            "metadata": {"guard": self.name, "version": self.version, "stage": self.stage, "runtime_state_modified": False},
        }

    def should_replace(self, result: Optional[Mapping[str, Any]]) -> bool:
        return isinstance(result, Mapping) and result.get("replacement_allowed") is True and result.get("status") == "replacement_approved"

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "replacement_allowed", "status", "stage", "reason", "failed_checks", "original_result_id",
            "recovery_candidate_id", "original_result_preserved", "controlled_replacement_only",
            "replacement_scope", "execution_allowed", "real_provider_request_allowed",
            "provider_fallback_allowed", "real_translation_allowed", "rollback_available",
            "quality_summary", "metadata",
        }
        if not required.issubset(result) or result.get("stage") != self.stage:
            return False
        if result.get("original_result_preserved") is not True or result.get("controlled_replacement_only") is not True:
            return False
        if result.get("replacement_scope") != "single_chunk" or result.get("rollback_available") is not True:
            return False
        if any(result.get(key) is not False for key in (
            "execution_allowed", "real_provider_request_allowed", "provider_fallback_allowed", "real_translation_allowed"
        )):
            return False
        if self._has_forbidden(result):
            return False
        failed = result.get("failed_checks")
        if not isinstance(failed, list):
            return False
        if result.get("replacement_allowed") is True:
            return result.get("status") == "replacement_approved" and not failed and self.should_replace(result)
        return result.get("status") == "replacement_rejected" and bool(failed) and not self.should_replace(result)

    def _has_forbidden(self, value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(str(key) in self.forbidden_inputs or self._has_forbidden(nested) for key, nested in value.items())
        if isinstance(value, (list, tuple)):
            return any(self._has_forbidden(item) for item in value)
        return False

    @staticmethod
    def _int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0


__all__ = ["ControlledResultReplacementGuard"]
