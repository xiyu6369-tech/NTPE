"""Stage-07.2 SDK Translation API.

This module adds text/file/batch/async SDK translation entry points while
reusing the Stage-07.0 NTPEClient and Stage-02 Translation Engine. It is fully
additive and keeps Foundation v1.0 and Stage-06 CLI freeze compatibility.
"""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .client import NTPEClient
from .options import TranslationOptions
from .request import TranslationRequest
from .response import TranslationResponse

SDK_TRANSLATION_VERSION = "0.7.2"
SDK_TRANSLATION_STAGE = "NTPE 1.0 Beta Stage-07.2 SDK Translation API"
_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ntpe-sdk-translation")


class SDKTranslationAPI:
    """Public SDK translation facade for embedding NTPE in Python apps."""

    version = SDK_TRANSLATION_VERSION
    stage = SDK_TRANSLATION_STAGE

    def __init__(self, client: Optional[NTPEClient] = None, metadata: Optional[Dict[str, Any]] = None):
        self.client = client or NTPEClient()
        self.metadata = dict(metadata or {})

    def translate(self, request: TranslationRequest | str | Dict[str, Any], options: Optional[TranslationOptions] = None) -> TranslationResponse:
        translation_request = self._coerce_request(request, options)
        try:
            segments = translation_request.resolve_segments()
            opts = translation_request.options
            sdk_results = self.client.translate_segments(
                segments,
                job_id=opts.job_id,
                source_language=opts.source_language,
                target_language=opts.target_language,
                model=opts.model,
                metadata={"sdk_translation_stage": self.stage, **dict(opts.metadata)},
            )
            if not all(item.ok for item in sdk_results):
                errors = []
                for item in sdk_results:
                    errors.extend(item.errors)
                return TranslationResponse(
                    ok=False,
                    job_id=opts.job_id,
                    data={"request": translation_request.to_dict(), "sdk_results": [item.to_dict() for item in sdk_results]},
                    errors=errors or ["SDK translation failed"],
                )
            session_id = sdk_results[-1].session_id if sdk_results else None
            return TranslationResponse.success(
                [item.text for item in sdk_results],
                job_id=opts.job_id,
                session_id=session_id,
                data={"request": translation_request.to_dict(), "sdk_results": [item.to_dict() for item in sdk_results]},
            )
        except Exception as exc:
            job_id = translation_request.options.job_id
            return TranslationResponse.failure(str(exc), job_id=job_id, data={"request": translation_request.to_dict()})

    def translate_text(self, text: str, options: Optional[TranslationOptions] = None) -> TranslationResponse:
        return self.translate(TranslationRequest.for_text(text, options or TranslationOptions()))

    def translate_file(self, file_path: str, options: Optional[TranslationOptions] = None) -> TranslationResponse:
        return self.translate(TranslationRequest.for_file(file_path, options or TranslationOptions()))

    def translate_batch(self, segments: Iterable[str], options: Optional[TranslationOptions] = None) -> TranslationResponse:
        return self.translate(TranslationRequest.for_batch(segments, options or TranslationOptions()))

    def translate_async(self, request: TranslationRequest | str | Dict[str, Any], options: Optional[TranslationOptions] = None) -> Future:
        return _EXECUTOR.submit(self.translate, request, options)

    def write_file(self, response: TranslationResponse, output_path: str) -> str:
        Path(output_path).write_text(response.text, encoding="utf-8")
        return output_path

    def manifest(self) -> Dict[str, Any]:
        return build_sdk_translation_manifest({"client_version": getattr(self.client, "version", None), **self.metadata})

    def _coerce_request(self, request: TranslationRequest | str | Dict[str, Any], options: Optional[TranslationOptions] = None) -> TranslationRequest:
        if isinstance(request, TranslationRequest):
            if options is not None:
                request.options = options
            return request
        if isinstance(request, str):
            return TranslationRequest.for_text(request, options or TranslationOptions())
        if isinstance(request, dict):
            parsed = TranslationRequest.from_dict(request)
            if options is not None:
                parsed.options = options
            return parsed
        raise TypeError("request must be TranslationRequest, str, or dict")


def translate(text: str, *, client: Optional[NTPEClient] = None, options: Optional[TranslationOptions] = None) -> TranslationResponse:
    return SDKTranslationAPI(client=client).translate_text(text, options=options)


def translate_file(file_path: str, *, client: Optional[NTPEClient] = None, options: Optional[TranslationOptions] = None) -> TranslationResponse:
    return SDKTranslationAPI(client=client).translate_file(file_path, options=options)


def translate_batch(segments: Iterable[str], *, client: Optional[NTPEClient] = None, options: Optional[TranslationOptions] = None) -> TranslationResponse:
    return SDKTranslationAPI(client=client).translate_batch(segments, options=options)


def translate_async(request: TranslationRequest | str | Dict[str, Any], *, client: Optional[NTPEClient] = None, options: Optional[TranslationOptions] = None) -> Future:
    return SDKTranslationAPI(client=client).translate_async(request, options=options)


def build_sdk_translation_manifest(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "NTPE SDK Translation API",
        "stage": SDK_TRANSLATION_STAGE,
        "version": SDK_TRANSLATION_VERSION,
        "status": "beta",
        "components": [
            "SDKTranslationAPI",
            "TranslationRequest",
            "TranslationResponse",
            "TranslationOptions",
            "translate",
            "translate_file",
            "translate_batch",
            "translate_async",
        ],
        "capabilities": [
            "sync_text_translation",
            "file_translation",
            "batch_translation",
            "async_translation",
            "runtime_client_reuse",
            "dict_serialization",
        ],
        "foundation_compatibility": "foundation-v1.0 frozen compatible",
        "cli_compatibility": "stage-06.9 cli freeze compatible",
        "sdk_core_compatibility": "stage-07.0 sdk core compatible",
        "sdk_session_compatibility": "stage-07.1 sdk session api compatible",
        "backward_compatible": True,
        "metadata": dict(metadata or {}),
    }
