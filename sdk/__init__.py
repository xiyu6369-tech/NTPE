"""NTPE Python SDK public surface."""
from .client import NTPEClient
from .contracts import SDKRequest, SDKResult
from .manifest import VERSION, STAGE, attach_sdk_manifest, build_sdk_manifest
from .session import SDK_SESSION_STAGE, SDK_SESSION_VERSION, SDKSession, SDKSessionStatus, build_sdk_session_manifest, create_session
from .exceptions import SDKError, SDKSessionError
from .options import TranslationOptions
from .request import TranslationRequest
from .response import TranslationResponse
from .translation import (
    SDK_TRANSLATION_STAGE,
    SDK_TRANSLATION_VERSION,
    SDKTranslationAPI,
    build_sdk_translation_manifest,
    translate,
    translate_async,
    translate_batch,
    translate_file,
)

from .batch_models import BatchItem, BatchOptions, BatchProgress, BatchResult
from .batch_request import BatchRequest
from .batch_response import BatchResponse
from .batch import (
    SDK_BATCH_STAGE,
    SDK_BATCH_VERSION,
    SDKBatchAPI,
    build_sdk_batch_manifest,
    translate_batch as sdk_batch_translate,
    translate_batch_async as sdk_batch_translate_async,
    translate_files as sdk_translate_files,
)

from .stream_event import StreamEvent
from .stream_models import StreamOptions, StreamState
from .stream_response import StreamResponse
from .stream_session import StreamSession
from .stream import (
    SDK_STREAM_STAGE,
    SDK_STREAM_VERSION,
    SDKStreamingAPI,
    build_sdk_stream_manifest,
    stream,
    collect_stream,
    stream_async,
)

__all__ = [
    "NTPEClient",
    "SDKRequest",
    "SDKResult",
    "VERSION",
    "STAGE",
    "attach_sdk_manifest",
    "build_sdk_manifest",
    "SDK_SESSION_STAGE",
    "SDK_SESSION_VERSION",
    "SDKSession",
    "SDKSessionStatus",
    "build_sdk_session_manifest",
    "create_session",
    "SDKError",
    "SDKSessionError",
    "TranslationOptions",
    "TranslationRequest",
    "TranslationResponse",
    "SDK_TRANSLATION_STAGE",
    "SDK_TRANSLATION_VERSION",
    "SDKTranslationAPI",
    "build_sdk_translation_manifest",
    "translate",
    "translate_async",
    "translate_batch",
    "translate_file",
    "BatchItem",
    "BatchOptions",
    "BatchProgress",
    "BatchResult",
    "BatchRequest",
    "BatchResponse",
    "SDK_BATCH_STAGE",
    "SDK_BATCH_VERSION",
    "SDKBatchAPI",
    "build_sdk_batch_manifest",
    "sdk_batch_translate",
    "sdk_batch_translate_async",
    "sdk_translate_files",
    "StreamEvent",
    "StreamOptions",
    "StreamState",
    "StreamResponse",
    "StreamSession",
    "SDK_STREAM_STAGE",
    "SDK_STREAM_VERSION",
    "SDKStreamingAPI",
    "build_sdk_stream_manifest",
    "stream",
    "collect_stream",
    "stream_async",
]
