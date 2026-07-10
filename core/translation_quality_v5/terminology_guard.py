from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


class TerminologyConsistencyGuard:
    version = "TE-v5.0"
    stage = "5.0.3"

    def evaluate(
        self,
        source_text: Optional[str],
        translated_text: Optional[str],
        *,
        locked_terms: Optional[Mapping[str, str]] = None,
        forbidden_variants: Optional[Mapping[str, Iterable[str]]] = None,
    ) -> Dict[str, Any]:
        source = str(source_text or "")
        translated = str(translated_text or "")
        terms = dict(locked_terms or {})
        variants = {
            key: list(values)
            for key, values in dict(forbidden_variants or {}).items()
        }

        missing: List[Dict[str, str]] = []
        wrong_variants: List[Dict[str, str]] = []
        replacements: List[Dict[str, str]] = []

        for source_term, target_term in terms.items():
            if source_term and source_term in source and target_term not in translated:
                missing.append({"source": source_term, "target": target_term})

            for wrong in variants.get(source_term, []):
                if wrong and wrong in translated:
                    wrong_variants.append({
                        "source": source_term,
                        "wrong": wrong,
                        "target": target_term,
                    })
                    replacements.append({"from": wrong, "to": target_term})

        repaired = translated
        for item in sorted(replacements, key=lambda x: len(x["from"]), reverse=True):
            repaired = repaired.replace(item["from"], item["to"])

        # Avoid expanding a given-name-only occurrence into a full name.
        full_name_overexpansion = []
        for source_term, target_term in terms.items():
            if " " in source_term.strip():
                continue
            if source_term and source_term in source:
                for other_source, other_target in terms.items():
                    if other_source != source_term and source_term in other_source:
                        if other_target != target_term and other_target in translated:
                            full_name_overexpansion.append({
                                "source": source_term,
                                "unexpected": other_target,
                                "expected": target_term,
                            })

        accepted = not missing and not wrong_variants and not full_name_overexpansion
        return {
            "accepted": accepted,
            "status": "consistent" if accepted else "inconsistent",
            "stage": self.stage,
            "missing_locked_terms": missing,
            "wrong_variants": wrong_variants,
            "full_name_overexpansion": full_name_overexpansion,
            "repair_replacements": replacements,
            "repaired_text": repaired,
            "source_text_retained": False,
            "translated_text_retained": False,
        }

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "accepted", "status", "stage", "missing_locked_terms",
            "wrong_variants", "full_name_overexpansion",
            "repair_replacements", "repaired_text",
            "source_text_retained", "translated_text_retained"
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if result.get("accepted") is True and (
            result.get("missing_locked_terms")
            or result.get("wrong_variants")
            or result.get("full_name_overexpansion")
        ):
            return False
        return True
