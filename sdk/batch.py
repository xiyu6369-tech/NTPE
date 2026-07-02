"""Stage-07.3 SDK Batch API.

Provides a stable multi-item SDK facade over Stage-07.2 Translation API. The
implementation is intentionally additive and isolates per-item failures so one
bad file does not break the whole batch when continue_on_error=True.
"""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional

from .batch_models import BatchItem, BatchOptions, BatchProgress, BatchResult
from .batch_request import BatchRequest
from .batch_response import BatchResponse
from .client import NTPEClient
from .translation import SDKTranslationAPI

SDK_BATCH_VERSION = "0.7.3"
SDK_BATCH_STAGE = "NTPE 1.0 Beta Stage-07.3 SDK Batch API"
_BATCH_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ntpe-sdk-batch")

ProgressCallback = Callable[[BatchProgress, BatchResult | None], None]


class SDKBatchAPI:
    """Public SDK batch facade for embedding NTPE batch workflows."""

    version = SDK_BATCH_VERSION
    stage = SDK_BATCH_STAGE

    def __init__(self, client: Optional[NTPEClient] = None, translation_api: Optional[SDKTranslationAPI] = None, metadata: Optional[Dict[str, Any]] = None):
        self.client = client or NTPEClient()
        self.translation_api = translation_api or SDKTranslationAPI(client=self.client)
        self.metadata = dict(metadata or {})
        self._last_progress = BatchProgress()

    def translate_batch(self, request: BatchRequest | Iterable[str] | Dict[str, Any], options: Optional[BatchOptions] = None, progress_callback: Optional[ProgressCallback] = None) -> BatchResponse:
        batch_request = self._coerce_request(request, options)
        batch_options = batch_request.options
        progress = BatchProgress(total=len(batch_request.items))
        self._last_progress = progress
        results: list[BatchResult] = []

        for index, item in enumerate(batch_request.items):
            progress.current_item_id = item.item_id
            self._emit(progress_callback, progress, None)
            try:
                text = item.resolve_text()
                translation_options = batch_options.merged_translation_options(item, index)
                translation_response = self.translation_api.translate_text(text, translation_options)
                if not translation_response.ok:
                    raise RuntimeError("; ".join(translation_response.errors) or "SDK batch item failed")
                output_path = self._write_output_if_requested(item, translation_response.text, batch_options)
                result = BatchResult.success(item.item_id, translation_response.text, output_path=output_path, data={"translation_response": translation_response.to_dict()})
                progress.completed += 1
            except Exception as exc:
                result = BatchResult.failure(item.item_id, str(exc), data={"item": item.to_dict()})
                progress.failed += 1
                if not batch_options.continue_on_error:
                    results.append(result)
                    self._emit(progress_callback, progress, result)
                    break
            results.append(result)
            self._emit(progress_callback, progress, result)

        progress.current_item_id = None
        self._last_progress = progress
        return BatchResponse.from_results(results, progress, job_id=batch_options.job_id, data={"request": batch_request.to_dict(), "stage": self.stage})

    def translate_texts(self, texts: Iterable[str], options: Optional[BatchOptions] = None, progress_callback: Optional[ProgressCallback] = None) -> BatchResponse:
        return self.translate_batch(BatchRequest.from_texts(texts, options or BatchOptions()), progress_callback=progress_callback)

    def translate_files(self, file_paths: Iterable[str], options: Optional[BatchOptions] = None, progress_callback: Optional[ProgressCallback] = None) -> BatchResponse:
        return self.translate_batch(BatchRequest.from_files(file_paths, options or BatchOptions()), progress_callback=progress_callback)

    def translate_batch_async(self, request: BatchRequest | Iterable[str] | Dict[str, Any], options: Optional[BatchOptions] = None, progress_callback: Optional[ProgressCallback] = None) -> Future:
        return _BATCH_EXECUTOR.submit(self.translate_batch, request, options, progress_callback)

    def progress(self) -> BatchProgress:
        return self._last_progress

    def manifest(self) -> Dict[str, Any]:
        return build_sdk_batch_manifest({"client_version": getattr(self.client, "version", None), **self.metadata})

    def _coerce_request(self, request: BatchRequest | Iterable[str] | Dict[str, Any], options: Optional[BatchOptions] = None) -> BatchRequest:
        if isinstance(request, BatchRequest):
            if options is not None:
                request.options = options
            return request
        if isinstance(request, dict):
            parsed = BatchRequest.from_dict(request)
            if options is not None:
                parsed.options = options
            return parsed
        return BatchRequest.from_texts(request, options or BatchOptions())

    def _write_output_if_requested(self, item: BatchItem, text: str, options: BatchOptions) -> Optional[str]:
        if not options.write_outputs and not item.output_path:
            return None
        output_path = Path(item.output_path) if item.output_path else Path(options.output_dir or ".") / f"{item.item_id}_zh.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        return str(output_path)

    def _emit(self, callback: Optional[ProgressCallback], progress: BatchProgress, result: BatchResult | None) -> None:
        if callback is not None:
            callback(progress, result)


def translate_batch(request: BatchRequest | Iterable[str] | Dict[str, Any], *, client: Optional[NTPEClient] = None, options: Optional[BatchOptions] = None, progress_callback: Optional[ProgressCallback] = None) -> BatchResponse:
    return SDKBatchAPI(client=client).translate_batch(request, options=options, progress_callback=progress_callback)


def translate_files(file_paths: Iterable[str], *, client: Optional[NTPEClient] = None, options: Optional[BatchOptions] = None, progress_callback: Optional[ProgressCallback] = None) -> BatchResponse:
    return SDKBatchAPI(client=client).translate_files(file_paths, options=options, progress_callback=progress_callback)


def translate_batch_async(request: BatchRequest | Iterable[str] | Dict[str, Any], *, client: Optional[NTPEClient] = None, options: Optional[BatchOptions] = None, progress_callback: Optional[ProgressCallback] = None) -> Future:
    return SDKBatchAPI(client=client).translate_batch_async(request, options=options, progress_callback=progress_callback)


def build_sdk_batch_manifest(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "NTPE SDK Batch API",
        "stage": SDK_BATCH_STAGE,
        "version": SDK_BATCH_VERSION,
        "status": "beta",
        "components": [
            "SDKBatchAPI",
            "BatchRequest",
            "BatchResponse",
            "BatchItem",
            "BatchOptions",
            "BatchProgress",
            "BatchResult",
            "translate_batch",
            "translate_files",
            "translate_batch_async",
        ],
        "capabilities": [
            "multi_text_batch_translation",
            "multi_file_batch_translation",
            "batch_progress_snapshot",
            "batch_progress_callback",
            "batch_error_isolation",
            "batch_output_writing",
            "async_batch_translation",
            "stage_07_2_translation_api_reuse",
        ],
        "foundation_compatibility": "foundation-v1.0 frozen compatible",
        "cli_compatibility": "stage-06.9 cli freeze compatible",
        "sdk_core_compatibility": "stage-07.0 sdk core compatible",
        "sdk_session_compatibility": "stage-07.1 sdk session api compatible",
        "sdk_translation_compatibility": "stage-07.2 sdk translation api compatible",
        "backward_compatible": True,
        "metadata": dict(metadata or {}),
    }
