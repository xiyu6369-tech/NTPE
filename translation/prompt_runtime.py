"""NTPE Foundation-06.4 Prompt Runtime.

Converts Translation Context Bundles into versioned, validated prompt packages.
This module is intentionally dictionary-compatible and non-destructive so older
06.0-06.3 translation contracts continue to work.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

VERSION = "Foundation-06.4"
PROMPT_PACKAGE_TYPE = "translation_prompt_package"
PROMPT_TEMPLATE_TYPE = "translation_prompt_template"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def create_prompt_template(
    template_id: str = "ntpe.default.translation",
    name: str = "NTPE Default Translation Prompt",
    system_prompt: str = "你是一個專業小說翻譯引擎。",
    instruction: str = "請將來源文字翻譯成自然流暢的台灣繁體中文，保留劇情、語氣、人名與段落資訊。",
    constraints: Optional[Iterable[str]] = None,
    output_format: str = "plain_text",
    version: str = VERSION,
) -> Dict[str, Any]:
    return {
        "type": PROMPT_TEMPLATE_TYPE,
        "template_id": template_id,
        "name": name,
        "version": version,
        "system_prompt": system_prompt,
        "instruction": instruction,
        "constraints": list(constraints or [
            "不得摘要、刪減或新增劇情。",
            "人名與術語必須依 glossary_context 固定。",
            "輸出只包含譯文，不加入說明、標題或前後綴。",
            "使用台灣繁體中文與中文標點。",
        ]),
        "output_format": output_format,
    }


def validate_prompt_template(template: Dict[str, Any]) -> bool:
    return isinstance(template, dict) and template.get("type") == PROMPT_TEMPLATE_TYPE and bool(template.get("template_id")) and bool(template.get("instruction"))


def normalize_prompt_template(template: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not template:
        return create_prompt_template()
    data = deepcopy(template)
    data.setdefault("type", PROMPT_TEMPLATE_TYPE)
    data.setdefault("template_id", data.get("id", "ntpe.default.translation"))
    data.setdefault("name", "NTPE Translation Prompt")
    data.setdefault("version", VERSION)
    data.setdefault("system_prompt", "你是一個專業小說翻譯引擎。")
    data.setdefault("instruction", "請翻譯來源文字。")
    data.setdefault("constraints", [])
    data.setdefault("output_format", "plain_text")
    return data


def _format_glossary(glossary: Dict[str, Any]) -> str:
    if not glossary:
        return "（無）"
    return "\n".join(f"- {k} => {v}" for k, v in glossary.items())


def _format_compact_segments(items: Iterable[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for item in items or []:
        sid = item.get("segment_id", item.get("id", "segment"))
        source = _text(item.get("source_text", item.get("text", ""))).strip()
        target = _text(item.get("target_text", item.get("output", ""))).strip()
        if target:
            lines.append(f"[{sid}] {target}")
        elif source:
            lines.append(f"[{sid}] {source}")
    return "\n".join(lines) if lines else "（無）"


def create_prompt_package(
    context_bundle: Dict[str, Any],
    template: Optional[Dict[str, Any]] = None,
    package_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ctx = deepcopy(context_bundle or {})
    tmpl = normalize_prompt_template(template)
    segment = ctx.get("segment", {})
    job = ctx.get("job", {})
    sid = segment.get("segment_id", segment.get("id", "segment"))
    jid = job.get("job_id", job.get("id", "job"))
    source_text = _text(segment.get("source_text", segment.get("text", "")))
    prompt_body = build_prompt_text(ctx, tmpl)
    return {
        "type": PROMPT_PACKAGE_TYPE,
        "version": VERSION,
        "package_id": package_id or f"prompt::{jid}::{sid}",
        "created_at": _now(),
        "template": tmpl,
        "job": deepcopy(job),
        "segment": deepcopy(segment),
        "context_id": ctx.get("context_id"),
        "source_language": job.get("source_language", "auto"),
        "target_language": job.get("target_language", job.get("target", "zh-TW")),
        "source_text": source_text,
        "prompt_text": prompt_body,
        "messages": [
            {"role": "system", "content": tmpl.get("system_prompt", "")},
            {"role": "user", "content": prompt_body},
        ],
        "metadata": deepcopy(metadata or {}),
        "runtime_metadata": {"runtime": "prompt_runtime", "foundation": VERSION},
    }


def build_prompt_text(context_bundle: Dict[str, Any], template: Dict[str, Any]) -> str:
    ctx = context_bundle or {}
    segment = ctx.get("segment", {})
    job = ctx.get("job", {})
    constraints = "\n".join(f"- {c}" for c in template.get("constraints", [])) or "- 保持原文資訊完整。"
    return "\n".join([
        "【任務】",
        _text(template.get("instruction")),
        "",
        "【語言】",
        f"來源語言：{job.get('source_language', 'auto')}",
        f"目標語言：{job.get('target_language', job.get('target', 'zh-TW'))}",
        "",
        "【硬性規則】",
        constraints,
        "",
        "【固定術語】",
        _format_glossary(ctx.get("glossary_context", {})),
        "",
        "【角色上下文】",
        _text(ctx.get("character_context", {})),
        "",
        "【敘事上下文】",
        _text(ctx.get("narrative_context", {})),
        "",
        "【場景上下文】",
        _text(ctx.get("scene_context", {})),
        "",
        "【前文參考】",
        _format_compact_segments(ctx.get("previous_context", [])),
        "",
        "【後文參考】",
        _format_compact_segments(ctx.get("next_context", [])),
        "",
        "【待翻譯內容】",
        _text(segment.get("source_text", segment.get("text", ""))),
    ])


def validate_prompt_package(package: Dict[str, Any]) -> bool:
    if not isinstance(package, dict):
        return False
    if package.get("type") != PROMPT_PACKAGE_TYPE:
        return False
    if not package.get("package_id"):
        return False
    if not validate_prompt_template(package.get("template", {})):
        return False
    if not isinstance(package.get("messages"), list) or len(package["messages"]) < 2:
        return False
    if not package.get("prompt_text"):
        return False
    return True


def normalize_prompt_package(package: Dict[str, Any]) -> Dict[str, Any]:
    data = deepcopy(package or {})
    data.setdefault("type", PROMPT_PACKAGE_TYPE)
    data.setdefault("version", VERSION)
    data.setdefault("package_id", data.get("id", "prompt::legacy"))
    data.setdefault("created_at", _now())
    data["template"] = normalize_prompt_template(data.get("template"))
    data.setdefault("messages", [
        {"role": "system", "content": data["template"].get("system_prompt", "")},
        {"role": "user", "content": data.get("prompt_text", data.get("content", ""))},
    ])
    data.setdefault("prompt_text", data.get("messages", [{}, {"content": ""}])[-1].get("content", ""))
    data.setdefault("runtime_metadata", {"runtime": "prompt_runtime", "foundation": VERSION})
    return data


class PromptPackageCache:
    def __init__(self) -> None:
        self._items: Dict[str, Dict[str, Any]] = {}

    def set(self, key: str, package: Dict[str, Any]) -> Dict[str, Any]:
        self._items[str(key)] = deepcopy(package)
        return deepcopy(package)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        item = self._items.get(str(key))
        return deepcopy(item) if item is not None else None

    def has(self, key: str) -> bool:
        return str(key) in self._items

    def manifest(self) -> Dict[str, Any]:
        return {"type": "prompt_package_cache", "count": len(self._items), "keys": sorted(self._items.keys())}


class PromptRuntimeBuilder:
    def __init__(self, template: Optional[Dict[str, Any]] = None, cache: Optional[PromptPackageCache] = None) -> None:
        self.template = normalize_prompt_template(template)
        self.cache = cache or PromptPackageCache()
        self.events: List[Dict[str, Any]] = []

    def _event(self, event: str, **data: Any) -> None:
        self.events.append({"event": event, "timestamp": _now(), **data})

    def build(self, context_bundle: Dict[str, Any], use_cache: bool = True, **kwargs: Any) -> Dict[str, Any]:
        ctx_id = context_bundle.get("context_id", "context")
        key = kwargs.get("cache_key") or f"prompt::{ctx_id}"
        if use_cache and self.cache.has(key):
            self._event("prompt_cache_hit", package_id=key)
            return self.cache.get(key) or {}
        package = create_prompt_package(context_bundle, template=self.template, metadata=kwargs.get("metadata"))
        self.cache.set(key, package)
        self._event("prompt_built", package_id=package["package_id"], context_id=ctx_id)
        return package

    def manifest(self) -> Dict[str, Any]:
        return create_prompt_runtime_manifest(events=self.events, cache=self.cache.manifest(), template=self.template)


def create_prompt_runtime_manifest(
    events: Optional[List[Dict[str, Any]]] = None,
    cache: Optional[Dict[str, Any]] = None,
    template: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "name": "NTPE Foundation-06.4 Prompt Runtime",
        "version": VERSION,
        "type": "prompt_runtime",
        "capabilities": [
            "prompt_template",
            "prompt_package",
            "context_to_prompt",
            "messages_builder",
            "prompt_cache",
            "prompt_manifest",
            "runtime_prompt_adapter",
        ],
        "events": deepcopy(events or []),
        "cache": deepcopy(cache or {}),
        "template": normalize_prompt_template(template),
        "compatible_with": ["Foundation-06.3", "Foundation-06.2", "Foundation-06.1", "Foundation-06.0", "Foundation-05.6"],
    }


class PromptRuntimeAdapter:
    def __init__(self, builder: Optional[PromptRuntimeBuilder] = None) -> None:
        self.builder = builder or PromptRuntimeBuilder()

    def build_prompt(self, context_bundle: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        return self.builder.build(context_bundle, **kwargs)

    def attach_prompt(self, payload: Dict[str, Any], context_bundle: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        data = deepcopy(payload or {})
        data["prompt_package"] = self.build_prompt(context_bundle, **kwargs)
        return data

    def validate(self, package: Dict[str, Any]) -> bool:
        return validate_prompt_package(package)

    def manifest(self) -> Dict[str, Any]:
        return self.builder.manifest()


def create_prompt_runtime_adapter(template: Optional[Dict[str, Any]] = None) -> PromptRuntimeAdapter:
    return PromptRuntimeAdapter(PromptRuntimeBuilder(template=template))
