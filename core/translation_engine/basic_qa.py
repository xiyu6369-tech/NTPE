from __future__ import annotations

import re


class BasicTranslationQA:
    """
    v2.0 Core 內建輕量 QA。
    正式 QA Engine 之後會獨立為 v1.0 模組。
    """

    def check(self, package: dict, translation: str) -> dict:
        source = package.get("source", {}).get("chunk_text", "")
        issues = []

        korean_count = len(re.findall(r"[가-힣]", translation))
        if korean_count >= 20:
            issues.append({
                "type": "korean_residue",
                "severity": "warning",
                "message": f"譯文仍包含較多韓文字元：{korean_count}",
            })

        source_len = len(source.strip())
        trans_len = len(translation.strip())

        if source_len > 200 and trans_len < source_len * 0.25:
            issues.append({
                "type": "possible_missing_translation",
                "severity": "warning",
                "message": f"譯文長度偏短：source={source_len}, translation={trans_len}",
            })

        locked = package.get("knowledge", {}).get("locked_dictionary", {})
        for src, target in locked.items():
            if src in source and target and target not in translation:
                issues.append({
                    "type": "locked_name_missing",
                    "severity": "warning",
                    "message": f"原文出現 {src}，但譯文未出現鎖定譯名 {target}",
                })

        return {
            "passed": not any(i["severity"] == "error" for i in issues),
            "issues": issues,
            "korean_residue_count": korean_count,
            "source_length": source_len,
            "translation_length": trans_len,
        }
