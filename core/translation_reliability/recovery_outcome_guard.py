
from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Optional


class RecoveryOutcomeGuard:
    """Validate isolated recovery outputs before they can be accepted.

    This guard is side-effect free. It does not call providers, HTTP clients,
    Translation Runtime, launcher code, or API keys.
    """

    version = "TE-v4.1"
    stage = "4.1.3"
    name = "recovery_outcome_guard"

    def evaluate(
        self,
        source_text: Optional[str],
        translated_text: Optional[str],
        recovery_result: Optional[Mapping[str, Any]] = None,
        config: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        source = str(source_text or "")
        translated = str(translated_text or "")
        recovery = dict(recovery_result or {})
        cfg = self._normalize_config(config)

        issues = []

        if not source:
            issues.append("missing_source")
        if not translated:
            issues.append("empty_output")

        source_chars = len(source)
        translated_chars = len(translated)
        length_ratio = (
            round(translated_chars / source_chars, 4)
            if source_chars > 0
            else 0.0
        )

        if source_chars > 0 and translated_chars > 0:
            if length_ratio < cfg["min_length_ratio"]:
                issues.append("too_short")
            if length_ratio > cfg["max_length_ratio"]:
                issues.append("too_long")

        hangul_residue_count = len(re.findall(r"[가-힣]", translated))
        if hangul_residue_count > cfg["max_hangul_residue"]:
            issues.append("hangul_residue")

        duplicate_line_count = self._duplicate_line_count(translated)
        if duplicate_line_count > cfg["max_duplicate_lines"]:
            issues.append("duplicate_output")

        if recovery.get("success") is not True:
            issues.append("recovery_not_successful")

        final_outcome = str(recovery.get("final_outcome") or "")
        if recovery and final_outcome not in {"success", ""}:
            issues.append("recovery_final_outcome_not_success")

        accepted = not issues

        return {
            "accepted": accepted,
            "status": "accepted" if accepted else "rejected",
            "stage": self.stage,
            "issues": issues,
            "metrics": {
                "source_chars": source_chars,
                "translated_chars": translated_chars,
                "length_ratio": length_ratio,
                "hangul_residue_count": hangul_residue_count,
                "duplicate_line_count": duplicate_line_count,
            },
            "recovery_summary": {
                "success": recovery.get("success") is True,
                "status": str(recovery.get("status") or "unknown"),
                "final_outcome": final_outcome or "unknown",
                "attempts_used": int(recovery.get("attempts_used", 0) or 0),
                "split_count": int(recovery.get("split_count", 0) or 0),
                "rebuild_count": int(recovery.get("rebuild_count", 0) or 0),
            },
            "source_text_retained": False,
            "translated_text_retained": False,
            "integration_status": {
                "mode": "validation_only",
                "provider_called": False,
                "http_called": False,
                "api_key_accessed": False,
                "runtime_modified": False,
                "launcher_modified": False,
                "real_translation_executed": False,
            },
            "metadata": {
                "guard": self.name,
                "version": self.version,
                "stage": self.stage,
            },
        }

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False

        required = {
            "accepted",
            "status",
            "stage",
            "issues",
            "metrics",
            "recovery_summary",
            "source_text_retained",
            "translated_text_retained",
            "integration_status",
            "metadata",
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if result.get("status") not in {"accepted", "rejected"}:
            return False
        if result.get("accepted") is True and result.get("issues"):
            return False
        if result.get("accepted") is False and not result.get("issues"):
            return False
        if result.get("source_text_retained") is not False:
            return False
        if result.get("translated_text_retained") is not False:
            return False

        integration = result.get("integration_status")
        if not isinstance(integration, Mapping):
            return False
        for key in (
            "provider_called",
            "http_called",
            "api_key_accessed",
            "runtime_modified",
            "launcher_modified",
            "real_translation_executed",
        ):
            if integration.get(key) is not False:
                return False

        metrics = result.get("metrics")
        if not isinstance(metrics, Mapping):
            return False
        if float(metrics.get("length_ratio", -1)) < 0:
            return False
        if int(metrics.get("hangul_residue_count", -1)) < 0:
            return False
        if int(metrics.get("duplicate_line_count", -1)) < 0:
            return False

        return True

    @staticmethod
    def _normalize_config(config: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        src = dict(config or {})
        min_ratio = float(src.get("min_length_ratio", 0.35) or 0.35)
        max_ratio = float(src.get("max_length_ratio", 2.5) or 2.5)
        if max_ratio < min_ratio:
            max_ratio = min_ratio

        return {
            "min_length_ratio": max(0.0, min_ratio),
            "max_length_ratio": max(0.0, max_ratio),
            "max_hangul_residue": max(
                0, int(src.get("max_hangul_residue", 0) or 0)
            ),
            "max_duplicate_lines": max(
                0, int(src.get("max_duplicate_lines", 0) or 0)
            ),
        }

    @staticmethod
    def _duplicate_line_count(text: str) -> int:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        seen = set()
        duplicates = 0
        for line in lines:
            if line in seen:
                duplicates += 1
            else:
                seen.add(line)
        return duplicates


__all__ = ["RecoveryOutcomeGuard"]
