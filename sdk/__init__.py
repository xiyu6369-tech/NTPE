"""NTPE Python SDK public surface."""
from .client import NTPEClient
from .contracts import SDKRequest, SDKResult
from .manifest import VERSION, STAGE, attach_sdk_manifest, build_sdk_manifest
from .session import SDK_SESSION_STAGE, SDK_SESSION_VERSION, SDKSession, SDKSessionStatus, build_sdk_session_manifest, create_session
from .exceptions import SDKError, SDKSessionError

from .error_codes import SDK_ERROR_STAGE, SDK_ERROR_VERSION, SDKErrorCode
from .error_models import SDKErrorContext, SDKErrorRecord
from .error_response import SDKErrorResponse
from .errors import (
    SDKException,
    SDKValidationError,
    SDKConfigurationError,
    SDKTranslationError,
    SDKBatchError,
    SDKStreamingError,
    SDKRuntimeBridgeError,
    build_sdk_error_manifest,
    error_response,
    normalize_exception,
    normalize_response_errors,
)
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

from .config_models import ProviderConfig, RuntimeConfig, TranslationConfig, BatchConfig, StreamingConfig
from .config import SDK_CONFIG_STAGE, SDK_CONFIG_VERSION, SDKConfig, build_sdk_config_manifest, default_config
from .config_builder import SDKConfigBuilder, config_builder
from .config_validator import SDKConfigValidationResult, SDKConfigValidator, validate_config
from .config_loader import SDKConfigLoader, load_config, save_config

from .plugin_models import PluginDescriptor, PluginResult
from .plugin_manifest import SDK_PLUGIN_STAGE, SDK_PLUGIN_VERSION, PluginManifest, build_sdk_plugin_manifest
from .plugin_context import SDKPluginContext
from .plugin import SDKPlugin
from .plugin_registry import SDKPluginRegistry
from .plugin_loader import SDKPluginLoader
from .plugin_manager import SDKPluginManager

from .version import SDK_VERSION as PACKAGE_VERSION, SDK_STAGE as PACKAGE_STAGE, SDK_STAGE_NAME, SDK_API_LEVEL, get_version, version_info
from .metadata import SDKPackageMetadata, package_metadata, package_classifiers

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
    "normalize_response_errors",
    "normalize_exception",
    "error_response",
    "build_sdk_error_manifest",
    "SDKRuntimeBridgeError",
    "SDKStreamingError",
    "SDKBatchError",
    "SDKTranslationError",
    "SDKConfigurationError",
    "SDKValidationError",
    "SDKException",
    "SDKErrorResponse",
    "SDKErrorRecord",
    "SDKErrorContext",
    "SDKErrorCode",
    "SDK_ERROR_VERSION",
    "SDK_ERROR_STAGE",
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
    "ProviderConfig",
    "RuntimeConfig",
    "TranslationConfig",
    "BatchConfig",
    "StreamingConfig",
    "SDK_CONFIG_STAGE",
    "SDK_CONFIG_VERSION",
    "SDKConfig",
    "build_sdk_config_manifest",
    "default_config",
    "SDKConfigBuilder",
    "config_builder",
    "SDKConfigValidationResult",
    "SDKConfigValidator",
    "validate_config",
    "SDKConfigLoader",
    "load_config",
    "save_config",
    "PluginDescriptor",
    "PluginResult",
    "SDK_PLUGIN_STAGE",
    "SDK_PLUGIN_VERSION",
    "PluginManifest",
    "build_sdk_plugin_manifest",
    "SDKPluginContext",
    "SDKPlugin",
    "SDKPluginRegistry",
    "SDKPluginLoader",
    "SDKPluginManager",
    "PACKAGE_VERSION",
    "PACKAGE_STAGE",
    "SDK_STAGE_NAME",
    "SDK_API_LEVEL",
    "get_version",
    "version_info",
    "SDKPackageMetadata",
    "package_metadata",
    "package_classifiers",
]
