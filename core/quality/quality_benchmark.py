from __future__ import annotations

import json
import re
from pathlib import Path
from datetime import datetime


class QualityBenchmark:
    """
    NTPE TQF Quality Benchmark v1.0

    用途：
    - 為翻譯品質建立可量化基準。
    - 先不改翻譯流程，只評估 Prompt Package + 譯文。
    - 專門抓目前已知問題：標題誤判、語義錯誤、摘要化、幻覺、文風壓扁。
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.report_dir = self.root / "quality_reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.rules_path = self.root / "rules" / "semantic_quality_rules.json"
        self.rules = self._load_rules()

    def evaluate_files(self, package_path: str | Path, translation_path: str | Path) -> dict:
        package_path = Path(package_path)
        translation_path = Path(translation_path)

        if not package_path.exists():
            return self._error(f"Prompt Package 不存在：{package_path}")
        if not translation_path.exists():
            return self._error(f"譯文檔不存在：{translation_path}")

        package = self._load_json(package_path)
        translation = translation_path.read_text(encoding="utf-8-sig")
        source = package.get("source", {}).get("chunk_text", "")

        result = self.evaluate_text(source=source, translation=translation, package=package)
        result["package_path"] = str(package_path)
        result["translation_path"] = str(translation_path)

        report_json, report_txt = self._save_reports(result)
        result["report_json"] = str(report_json)
        result["report_txt"] = str(report_txt)
        return result

    def evaluate_text(self, source: str, translation: str, package: dict | None = None) -> dict:
        issues: list[dict] = []

        structure_score = self._check_structure(source, translation, issues)
        semantic_score = self._check_semantic(source, translation, issues)
        coverage_score = self._check_coverage(source, translation, issues)
        hallucination_score = self._check_hallucination(source, translation, issues)
        style_score = self._check_style(source, translation, issues)

        scores = {
            "structure": structure_score,
            "semantic": semantic_score,
            "coverage": coverage_score,
            "hallucination": hallucination_score,
            "style": style_score,
        }

        overall = round(
            structure_score * 0.20
            + semantic_score * 0.25
            + coverage_score * 0.25
            + hallucination_score * 0.20
            + style_score * 0.10,
            1,
        )
        scores["overall"] = overall

        return {
            "status": "success",
            "generated_at": self._now(),
            "scores": scores,
            "issues": issues,
            "metrics": self._metrics(source, translation),
            "recommendation": self._recommendation(scores, issues),
        }

    def _check_structure(self, source: str, translation: str, issues: list[dict]) -> int:
        score = 100
        source_lines = [line.strip() for line in source.splitlines() if line.strip()]
        trans_start = translation.strip()[:120]

        if source_lines:
            first = source_lines[0]
            for rule in self.rules.get("title_rules", []):
                if re.search(rule["source_regex"], first):
                    required = rule.get("required_any", [])
                    forbidden = rule.get("forbidden_any", [])

                    if required and not any(x in translation for x in required):
                        score -= 45
                        self._issue(
                            issues,
                            rule.get("severity", "error"),
                            "structure_title_missing",
                            f"來源第一行像標題：{first}，但譯文沒有保留指定標題格式。",
                        )

                    for bad in forbidden:
                        if bad in trans_start:
                            score -= 45
                            self._issue(
                                issues,
                                rule.get("severity", "error"),
                                "structure_title_as_body",
                                f"標題可能被當成正文翻譯：譯文開頭包含「{bad}」。",
                            )

        return max(score, 0)

    def _check_semantic(self, source: str, translation: str, issues: list[dict]) -> int:
        score = 100

        for rule in self.rules.get("semantic_locks", []):
            src = rule.get("source", "")
            if src and src in source:
                required = rule.get("required_any", [])
                forbidden = rule.get("forbidden_any", [])
                severity = rule.get("severity", "warning")

                for bad in forbidden:
                    if bad in translation:
                        score -= 30 if severity == "error" else 15
                        self._issue(
                            issues,
                            severity,
                            "semantic_forbidden_translation",
                            f"{src} 出現時，譯文不應出現「{bad}」。{rule.get('note', '')}",
                        )

                if required and not any(x in translation for x in required):
                    score -= 25 if severity == "error" else 12
                    self._issue(
                        issues,
                        severity,
                        "semantic_required_missing",
                        f"{src} 出現時，譯文應包含建議語義：{required}。{rule.get('note', '')}",
                    )

        return max(score, 0)

    def _check_coverage(self, source: str, translation: str, issues: list[dict]) -> int:
        source_len = len(source.strip())
        trans_len = len(translation.strip())
        if source_len == 0:
            return 100

        ratio = trans_len / max(source_len, 1)
        score = 100

        if ratio < 0.55:
            score -= 45
            self._issue(
                issues,
                "error",
                "coverage_too_short",
                f"譯文長度比例過低，可能摘要或漏翻：ratio={ratio:.2f}",
            )
        elif ratio < 0.75:
            score -= 25
            self._issue(
                issues,
                "warning",
                "coverage_short",
                f"譯文偏短，需人工檢查是否漏翻：ratio={ratio:.2f}",
            )

        source_para = len([p for p in re.split(r"\n\s*\n", source.strip()) if p.strip()])
        trans_para = len([p for p in re.split(r"\n\s*\n", translation.strip()) if p.strip()])

        if source_para >= 3 and trans_para <= max(1, source_para // 2):
            score -= 25
            self._issue(
                issues,
                "warning",
                "coverage_paragraph_compression",
                f"段落數壓縮明顯：source_paragraphs={source_para}, translation_paragraphs={trans_para}",
            )

        return max(score, 0)

    def _check_hallucination(self, source: str, translation: str, issues: list[dict]) -> int:
        score = 100

        for rule in self.rules.get("hallucination_guards", []):
            required_source = rule.get("source_contains", [])
            if all(x in source for x in required_source):
                for bad in rule.get("translation_forbidden_any", []):
                    if bad in translation:
                        severity = rule.get("severity", "error")
                        score -= 40 if severity == "error" else 20
                        self._issue(
                            issues,
                            severity,
                            "hallucination_forbidden_content",
                            rule.get("message", f"譯文不應出現：{bad}"),
                        )

        # Korean residue basic check
        korean_count = len(re.findall(r"[가-힣]", translation))
        if korean_count >= 20:
            score -= 25
            self._issue(
                issues,
                "warning",
                "korean_residue",
                f"譯文仍有較多韓文字元：{korean_count}",
            )

        return max(score, 0)

    def _check_style(self, source: str, translation: str, issues: list[dict]) -> int:
        score = 100
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", translation.strip()) if p.strip()]

        if paragraphs:
            long_paragraphs = [p for p in paragraphs if len(p) > 900]
            if long_paragraphs:
                score -= 20
                self._issue(
                    issues,
                    "warning",
                    "style_long_paragraph",
                    f"譯文有 {len(long_paragraphs)} 個過長段落，可能壓扁小說節奏。",
                )

        if "……" in source and "……" not in translation:
            score -= 10
            self._issue(
                issues,
                "info",
                "style_ellipsis_lost",
                "原文有停頓符號，但譯文沒有保留類似節奏。",
            )

        if '"' in translation:
            score -= 5
            self._issue(
                issues,
                "info",
                "style_quote_format",
                "譯文出現英文雙引號，建議統一為中文引號「」。",
            )

        return max(score, 0)

    def _metrics(self, source: str, translation: str) -> dict:
        return {
            "source_chars": len(source),
            "translation_chars": len(translation),
            "length_ratio": round(len(translation.strip()) / max(len(source.strip()), 1), 3),
            "source_paragraphs": len([p for p in re.split(r"\n\s*\n", source.strip()) if p.strip()]),
            "translation_paragraphs": len([p for p in re.split(r"\n\s*\n", translation.strip()) if p.strip()]),
            "korean_residue_count": len(re.findall(r"[가-힣]", translation)),
        }

    def _recommendation(self, scores: dict, issues: list[dict]) -> str:
        if scores["overall"] < 70:
            return "RETRANSLATE_REQUIRED"
        if any(i["severity"] == "error" for i in issues):
            return "RETRANSLATE_RECOMMENDED"
        if scores["overall"] < 85:
            return "HUMAN_REVIEW_RECOMMENDED"
        return "PASS"

    def _save_reports(self, result: dict) -> tuple[Path, Path]:
        stamp = self._now().replace(":", "").replace("-", "").replace("T", "_")
        report_json = self.report_dir / f"quality_benchmark_{stamp}.json"
        report_txt = self.report_dir / f"quality_benchmark_{stamp}.txt"

        report_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        report_txt.write_text(self._render_text_report(result), encoding="utf-8")
        return report_json, report_txt

    def _render_text_report(self, result: dict) -> str:
        lines = []
        lines.append("====================================")
        lines.append("NTPE TQF Quality Benchmark v1.0")
        lines.append("====================================")
        lines.append("")
        lines.append(f"Generated: {result['generated_at']}")
        lines.append(f"Recommendation: {result['recommendation']}")
        lines.append("")
        lines.append("[Scores]")
        for key, value in result["scores"].items():
            lines.append(f"- {key}: {value}")
        lines.append("")
        lines.append("[Metrics]")
        for key, value in result["metrics"].items():
            lines.append(f"- {key}: {value}")
        lines.append("")
        lines.append("[Issues]")
        if not result["issues"]:
            lines.append("- None")
        else:
            for issue in result["issues"]:
                lines.append(f"- [{issue['severity']}] {issue['type']}: {issue['message']}")
        lines.append("")
        return "\n".join(lines)

    def _load_rules(self) -> dict:
        if not self.rules_path.exists():
            return {"semantic_locks": [], "hallucination_guards": [], "title_rules": []}
        return self._load_json(self.rules_path)

    def _load_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def _issue(self, issues: list[dict], severity: str, issue_type: str, message: str) -> None:
        issues.append({
            "severity": severity,
            "type": issue_type,
            "message": message,
        })

    def _error(self, message: str) -> dict:
        return {
            "status": "failed",
            "scores": {"overall": 0, "structure": 0, "semantic": 0, "coverage": 0, "hallucination": 0, "style": 0},
            "issues": [{"severity": "error", "type": "runtime", "message": message}],
            "metrics": {},
            "recommendation": "ERROR",
            "report_json": "",
            "report_txt": "",
        }

    def _now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")
