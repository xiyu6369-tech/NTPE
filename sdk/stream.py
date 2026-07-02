"""Stage-07.4 SDK Streaming API.

Provides additive streaming-style translation events over Stage-07.2 Translation
API. It exposes generator, callback, and collected response entry points without
changing Foundation v1.0, frozen CLI, SDK Core, Session, Translation, or Batch
contracts.
"""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, Optional

from .client import NTPEClient
from .stream_event import StreamEvent
from .stream_models import StreamOptions, StreamState
from .stream_response import StreamResponse
from .stream_session import StreamSession
from .translation import SDKTranslationAPI

SDK_STREAM_VERSION = "0.7.4"
SDK_STREAM_STAGE = "NTPE 1.0 Beta Stage-07.4 SDK Streaming API"
_STREAM_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ntpe-sdk-stream")
StreamCallback = Callable[[StreamEvent], None]


class SDKStreamingAPI:
    """Public SDK streaming facade for embedding event-driven NTPE workflows."""

    version = SDK_STREAM_VERSION
    stage = SDK_STREAM_STAGE

    def __init__(self, client: Optional[NTPEClient] = None, translation_api: Optional[SDKTranslationAPI] = None, metadata: Optional[Dict[str, Any]] = None):
        self.client = client or NTPEClient()
        self.translation_api = translation_api or SDKTranslationAPI(client=self.client)
        self.metadata = dict(metadata or {})
        self._last_session: Optional[StreamSession] = None

    def stream(self, text: str | Iterable[str] | Dict[str, Any], options: Optional[StreamOptions] = None, callback: Optional[StreamCallback] = None) -> Iterator[StreamEvent]:
        stream_options = self._coerce_options(options)
        segments = self._coerce_segments(text)
        session = StreamSession(job_id=stream_options.job_id)
        session.state.total_segments = len(segments)
        self._last_session = session
        collected_text: list[str] = []
        sequence = 0

        def make_event(event_type: str, *, segment_index: Optional[int] = None, text_value: str = "", progress: Optional[float] = None, data: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> StreamEvent:
            nonlocal sequence
            sequence += 1
            event = StreamEvent(
                type=event_type,
                sequence=sequence,
                job_id=stream_options.job_id,
                session_id=session.session_id,
                segment_index=segment_index,
                text=text_value,
                progress=session.state.progress if progress is None else progress,
                data=dict(data or {}),
                error=error,
            )
            session.append(event)
            if callback:
                callback(event)
            return event

        yield make_event("started", progress=0.0, data={"stage": self.stage, "total_segments": len(segments)})

        for index, segment in enumerate(segments):
            yield make_event("progress", segment_index=index, progress=session.state.progress, data={"status": "segment_started"})
            response = self.translation_api.translate_text(segment, stream_options.to_translation_options(segment_index=index))
            if not response.ok:
                error_message = "; ".join(response.errors) or "SDK stream translation failed"
                yield make_event("error", segment_index=index, progress=session.state.progress, data={"response": response.to_dict()}, error=error_message)
                if not stream_options.continue_on_error:
                    return
                continue
            collected_text.append(response.text)
            if stream_options.emit_segments:
                yield make_event("segment", segment_index=index, text_value=response.text, data={"response": response.to_dict()})
            if stream_options.emit_tokens:
                for token in self._tokenize(response.text):
                    yield make_event("token", segment_index=index, text_value=token, data={"token": token})
            yield make_event("progress", segment_index=index, progress=session.state.progress, data={"status": "segment_completed"})

        final_text = "\n".join(collected_text)
        yield make_event("completed", text_value=final_text, progress=100.0, data={"segments": len(collected_text)})

    def collect(self, text: str | Iterable[str] | Dict[str, Any], options: Optional[StreamOptions] = None, callback: Optional[StreamCallback] = None) -> StreamResponse:
        stream_options = self._coerce_options(options)
        events = list(self.stream(text, stream_options, callback=callback))
        session_id = events[0].session_id if events else None
        return StreamResponse.from_events(events, job_id=stream_options.job_id, session_id=session_id, data={"stage": self.stage})

    def stream_text(self, text: str, options: Optional[StreamOptions] = None, callback: Optional[StreamCallback] = None) -> Iterator[StreamEvent]:
        return self.stream(text, options=options, callback=callback)

    def stream_file(self, file_path: str, options: Optional[StreamOptions] = None, callback: Optional[StreamCallback] = None) -> Iterator[StreamEvent]:
        return self.stream(Path(file_path).read_text(encoding="utf-8"), options=options, callback=callback)

    def collect_file(self, file_path: str, options: Optional[StreamOptions] = None, callback: Optional[StreamCallback] = None) -> StreamResponse:
        return self.collect(Path(file_path).read_text(encoding="utf-8"), options=options, callback=callback)

    def stream_async(self, text: str | Iterable[str] | Dict[str, Any], options: Optional[StreamOptions] = None, callback: Optional[StreamCallback] = None) -> Future:
        return _STREAM_EXECUTOR.submit(self.collect, text, options, callback)

    def progress(self) -> StreamState:
        if self._last_session is None:
            return StreamState()
        return self._last_session.progress()

    def manifest(self) -> Dict[str, Any]:
        return build_sdk_stream_manifest({"client_version": getattr(self.client, "version", None), **self.metadata})

    def _coerce_options(self, options: Optional[StreamOptions]) -> StreamOptions:
        if options is None:
            return StreamOptions()
        if isinstance(options, StreamOptions):
            return options
        raise TypeError("options must be StreamOptions")

    def _coerce_segments(self, text: str | Iterable[str] | Dict[str, Any]) -> list[str]:
        if isinstance(text, str):
            return [text]
        if isinstance(text, dict):
            if "segments" in text:
                return [str(item) for item in text.get("segments", [])]
            if "text" in text:
                return [str(text.get("text", ""))]
            raise ValueError("stream dict request requires text or segments")
        return [str(item) for item in text]

    def _tokenize(self, text: str) -> list[str]:
        if not text:
            return []
        tokens = text.split()
        return tokens if len(tokens) > 1 else list(text)


def stream(text: str | Iterable[str] | Dict[str, Any], *, client: Optional[NTPEClient] = None, options: Optional[StreamOptions] = None, callback: Optional[StreamCallback] = None) -> Iterator[StreamEvent]:
    return SDKStreamingAPI(client=client).stream(text, options=options, callback=callback)


def collect_stream(text: str | Iterable[str] | Dict[str, Any], *, client: Optional[NTPEClient] = None, options: Optional[StreamOptions] = None, callback: Optional[StreamCallback] = None) -> StreamResponse:
    return SDKStreamingAPI(client=client).collect(text, options=options, callback=callback)


def stream_async(text: str | Iterable[str] | Dict[str, Any], *, client: Optional[NTPEClient] = None, options: Optional[StreamOptions] = None, callback: Optional[StreamCallback] = None) -> Future:
    return SDKStreamingAPI(client=client).stream_async(text, options=options, callback=callback)


def build_sdk_stream_manifest(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "NTPE SDK Streaming API",
        "stage": SDK_STREAM_STAGE,
        "version": SDK_STREAM_VERSION,
        "status": "beta",
        "components": [
            "SDKStreamingAPI",
            "StreamEvent",
            "StreamOptions",
            "StreamResponse",
            "StreamSession",
            "stream",
            "collect_stream",
            "stream_async",
        ],
        "capabilities": [
            "streaming_translation_events",
            "token_events",
            "segment_events",
            "progress_events",
            "event_callback",
            "async_stream_collection",
            "runtime_client_reuse",
            "error_event_handling",
        ],
        "foundation_compatibility": "foundation-v1.0 frozen compatible",
        "cli_compatibility": "stage-06.9 cli freeze compatible",
        "sdk_core_compatibility": "stage-07.0 sdk core compatible",
        "sdk_session_compatibility": "stage-07.1 sdk session api compatible",
        "sdk_translation_compatibility": "stage-07.2 sdk translation api compatible",
        "sdk_batch_compatibility": "stage-07.3 sdk batch api compatible",
        "backward_compatible": True,
        "metadata": dict(metadata or {}),
    }
