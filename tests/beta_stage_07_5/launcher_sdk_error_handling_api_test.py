"""NTPE 1.0 Beta Stage-07.5 SDK Error Handling API test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdk import (  # noqa: E402
    SDK_BATCH_STAGE,
    SDK_STREAM_STAGE,
    SDK_TRANSLATION_STAGE,
    SDKError,
    SDKErrorCode,
    SDKErrorContext,
    SDKErrorRecord,
    SDKErrorResponse,
    SDKException,
    SDKTranslationError,
    SDKBatchError,
    SDKStreamingError,
    SDKRuntimeBridgeError,
    build_sdk_error_manifest,
    error_response,
    normalize_exception,
    normalize_response_errors,
)
from sdk.response import TranslationResponse  # noqa: E402
from sdk.batch_response import BatchResponse  # noqa: E402
from sdk.stream_response import StreamResponse  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<28} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta Stage-07.5 SDK Error Handling API Test")
    print("=" * 64)

    check("Error Code Coerce", SDKErrorCode.coerce("sdk.translation") is SDKErrorCode.TRANSLATION)

    context = SDKErrorContext(job_id="job-075", session_id="session-075", component="sdk.translation", operation="translate", retryable=True)
    record = SDKErrorRecord(code=SDKErrorCode.TRANSLATION, message="translation failed", context=context, cause="RuntimeError")
    record_dict = record.to_dict()
    check("Error Record Serialize", record_dict["code"] == "sdk.translation" and record_dict["context"]["job_id"] == "job-075")
    check("Error Record Restore", SDKErrorRecord.from_dict(record_dict).code is SDKErrorCode.TRANSLATION)

    response = SDKErrorResponse.from_error(record)
    check("Error Response", not response.ok and response.code is SDKErrorCode.TRANSLATION and response.error_messages == ["translation failed"])

    exc = SDKTranslationError("bad translation", job_id="job-075", session_id="session-075", operation="translate", retryable=True)
    check("Typed Exception", exc.code is SDKErrorCode.TRANSLATION and exc.to_response().job_id == "job-075")

    legacy = SDKError("legacy error", operation="legacy")
    check("Legacy SDKError", isinstance(legacy, SDKException) and legacy.to_dict()["message"] == "legacy error")

    normalized = normalize_exception(ValueError("invalid input"), code=SDKErrorCode.VALIDATION, job_id="job-normalized", component="sdk.validation", operation="validate")
    check("Normalize Exception", normalized.code is SDKErrorCode.VALIDATION and normalized.context.job_id == "job-normalized")

    translated = TranslationResponse.failure("translation api failed", job_id="job-t")
    batch = BatchResponse(ok=False, job_id="job-b", errors=["batch api failed"])
    stream = StreamResponse(ok=False, job_id="job-s", session_id="session-s", errors=["stream api failed"])
    check("Normalize Translation", normalize_response_errors(translated, fallback_code=SDKErrorCode.TRANSLATION)[0].code is SDKErrorCode.TRANSLATION)
    check("Normalize Batch", normalize_response_errors(batch, fallback_code=SDKErrorCode.BATCH)[0].context.job_id == "job-b")
    check("Normalize Streaming", normalize_response_errors(stream, fallback_code=SDKErrorCode.STREAMING)[0].context.session_id == "session-s")

    helper = error_response("runtime bridge failed", code=SDKErrorCode.RUNTIME, job_id="job-runtime", component="sdk.runtime_bridge")
    check("Error Response Helper", helper.code is SDKErrorCode.RUNTIME and helper.job_id == "job-runtime")

    check("Specialized Errors", all(cls("x").code for cls in [SDKBatchError, SDKStreamingError, SDKRuntimeBridgeError]))

    manifest = build_sdk_error_manifest({"translation_stage": SDK_TRANSLATION_STAGE, "batch_stage": SDK_BATCH_STAGE, "stream_stage": SDK_STREAM_STAGE})
    check("Error Manifest", manifest["backward_compatible"] is True and "SDKErrorCode" in manifest["components"])
    check("Stage Links", "Stage-07.2" in manifest["metadata"]["translation_stage"] and "Stage-07.4" in manifest["metadata"]["stream_stage"])

    print("PASS")


if __name__ == "__main__":
    main()
