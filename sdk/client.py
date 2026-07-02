"""Public NTPE SDK client.

Stage-07.0 provides a thin, stable Python integration layer over the existing
Stage-02 translation engine and Stage-03 provider abstractions. It is additive:
no existing runtime, CLI, provider, or Foundation APIs are changed.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional

from core.translation_engine import TranslationOrchestrator, TranslationStrategy

try:
    from core.ai_provider.contracts import ProviderRequest
except Exception:  # pragma: no cover - SDK remains importable in minimal builds.
    ProviderRequest = None  # type: ignore

from .contracts import SDKRequest, SDKResult
from .manifest import VERSION, build_sdk_manifest


class NTPEClient:
    """Stable Python SDK facade for embedding NTPE in external apps."""

    version = VERSION

    def __init__(
        self,
        translator: Optional[Callable[[Any, Dict[str, Any]], Any]] = None,
        provider_manager: Any = None,
        strategy: Optional[TranslationStrategy] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.provider_manager = provider_manager
        self.metadata = dict(metadata or {})
        bridge = translator or (self._provider_translator if provider_manager is not None else None)
        self.orchestrator = TranslationOrchestrator(translator=bridge, strategy=strategy or TranslationStrategy())

    def translate_text(
        self,
        text: str,
        *,
        source_language: str = "ko",
        target_language: str = "zh-TW",
        job_id: str = "sdk-job",
        model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SDKResult:
        request = SDKRequest(
            text=text,
            source_language=source_language,
            target_language=target_language,
            job_id=job_id,
            model=model,
            metadata=dict(metadata or {}),
        )
        return self.translate(request)

    def translate(self, request: SDKRequest | Dict[str, Any]) -> SDKResult:
        sdk_request = self._coerce_request(request)
        payload = {
            "source_language": sdk_request.source_language,
            "target_language": sdk_request.target_language,
            "model": sdk_request.model,
            "sdk": {"version": self.version, "metadata": dict(sdk_request.metadata)},
        }
        try:
            result = self.orchestrator.translate_segments([sdk_request.text], job_id=sdk_request.job_id, payload=payload)
            item = result["results"][0] if result.get("results") else {}
            session = result.get("session", {})
            return SDKResult.success(
                str(item.get("translation", "")),
                job_id=sdk_request.job_id,
                session_id=session.get("session_id"),
                data={"request": sdk_request.to_dict(), "engine_result": result},
            )
        except Exception as exc:  # Public SDK should return structured failure, not leak internals.
            return SDKResult.failure(str(exc), job_id=sdk_request.job_id, data={"request": sdk_request.to_dict()})

    def translate_segments(
        self,
        segments: Iterable[str],
        *,
        job_id: str = "sdk-job",
        source_language: str = "ko",
        target_language: str = "zh-TW",
        model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[SDKResult]:
        results: List[SDKResult] = []
        for index, segment in enumerate(segments):
            item_metadata = dict(metadata or {})
            item_metadata.setdefault("segment_index", index)
            results.append(
                self.translate_text(
                    segment,
                    source_language=source_language,
                    target_language=target_language,
                    job_id=job_id,
                    model=model,
                    metadata=item_metadata,
                )
            )
        return results

    def prompt_package(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"sdk": {"version": self.version, "metadata": dict(metadata or {})}}
        return self.orchestrator.prompt_package(text, payload=payload)

    def manifest(self) -> Dict[str, Any]:
        manifest = build_sdk_manifest(self.metadata)
        manifest["translation_engine"] = self.orchestrator.manifest({"sdk_version": self.version})
        if self.provider_manager is not None and hasattr(self.provider_manager, "manifest"):
            manifest["provider_manager"] = self.provider_manager.manifest()
        return manifest

    def _provider_translator(self, segment: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        if ProviderRequest is None:
            raise RuntimeError("ProviderRequest is unavailable")
        payload = dict(context.get("payload", {}))
        prompt_package = context.get("prompt_package", {})
        prompt = prompt_package.get("prompt", str(segment)) if isinstance(prompt_package, dict) else str(segment)
        request = ProviderRequest(prompt=str(prompt), model=payload.get("model"), metadata={"sdk_context": context})
        response = self.provider_manager.complete(request)
        return {"translation": response.text, "provider_response": response}

    def _coerce_request(self, request: SDKRequest | Dict[str, Any]) -> SDKRequest:
        if isinstance(request, SDKRequest):
            return request
        if isinstance(request, dict):
            return SDKRequest(
                text=str(request.get("text", "")),
                source_language=str(request.get("source_language", "ko")),
                target_language=str(request.get("target_language", "zh-TW")),
                job_id=str(request.get("job_id", "sdk-job")),
                model=request.get("model"),
                metadata=dict(request.get("metadata", {}) or {}),
            )
        raise TypeError("request must be SDKRequest or dict")
