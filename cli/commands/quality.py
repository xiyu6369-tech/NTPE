from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from ..command import CLICommand, CommandRegistry
from ..context import CLIContext
from ..result import CLIResult
from .manifest import attach_quality_manifest


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_mapping(path_value: Optional[str]) -> Dict[str, str]:
    if not path_value:
        return {}
    path = Path(path_value)
    if not path.exists():
        return {}
    text = _read_text(path).strip()
    if not text:
        return {}
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    mapping: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            source, target = line.split("=", 1)
        elif "->" in line:
            source, target = line.split("->", 1)
        else:
            continue
        mapping[source.strip()] = target.strip()
    return mapping


def _make_quality_context(args: object) -> Any:
    from translation.quality.contract import QualityContext

    target_path = Path(getattr(args, "target", "")).resolve()
    translated_text = _read_text(target_path) if target_path.exists() else str(getattr(args, "target", ""))

    source_text = ""
    source_value = getattr(args, "source", None)
    if source_value:
        source_path = Path(source_value)
        source_text = _read_text(source_path) if source_path.exists() else str(source_value)

    glossary = _load_mapping(getattr(args, "glossary", None))
    character_names = _load_mapping(getattr(args, "characters", None))
    return QualityContext(
        source_text=source_text,
        translated_text=translated_text,
        glossary=glossary,
        character_names=character_names,
        style=getattr(args, "style", "zh-TW"),
        metadata={"cli": "quality", "target": str(target_path)},
    )


def _run_quality(args: object) -> Any:
    from translation.quality.pipeline import QualityPipeline

    context = _make_quality_context(args)
    return QualityPipeline().run(context)


def _result_payload(result: Any) -> Dict[str, Any]:
    payload = result.to_dict() if hasattr(result, "to_dict") else dict(result)
    attach_quality_manifest(payload)
    return payload


def command_quality(context: CLIContext, args: object) -> CLIResult:
    action = getattr(args, "quality_action", "check") or "check"
    try:
        if action == "rules":
            from translation.quality.rules import QualityRuleSet

            rules = QualityRuleSet(locale=getattr(args, "style", "zh-TW")).list_rules()
            data = {"rules": rules, "count": len(rules)}
            attach_quality_manifest(data)
            return CLIResult.success("Quality rules", **data)

        result = _run_quality(args)
        payload = _result_payload(result)

        if action == "check":
            message = "Quality check passed" if result.passed else "Quality check failed"
            return CLIResult.success(message, **payload) if result.passed else CLIResult.failure(message, exit_code=2, errors=[issue.message for issue in result.issues], **payload)

        if action == "score":
            data = {"score": result.score, "passed": result.passed, "issue_count": len(result.issues)}
            attach_quality_manifest(data)
            return CLIResult.success("Quality score", **data)

        if action == "repair":
            output_value = getattr(args, "output", None)
            if output_value:
                output_path = Path(output_value)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(result.text, encoding="utf-8")
                payload["output"] = str(output_path)
            return CLIResult.success("Quality repair completed", **payload)

        if action == "report":
            from translation.quality.report import QualityReport

            report = QualityReport(result).summary()
            attach_quality_manifest(report)
            output_value = getattr(args, "output", None)
            if output_value:
                _write_json(Path(output_value), report)
                report["output"] = str(Path(output_value))
            return CLIResult.success("Quality report", **report)

        return CLIResult.failure(f"Unknown quality action: {action}", exit_code=2)
    except Exception as exc:
        return CLIResult.failure(f"Quality command failed: {exc}", exit_code=2)


def register_quality_command(registry: CommandRegistry) -> CommandRegistry:
    registry.register(CLICommand("quality", "run translation quality checks", command_quality))
    return registry
