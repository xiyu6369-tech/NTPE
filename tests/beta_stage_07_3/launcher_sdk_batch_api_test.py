from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdk import (
    BatchItem,
    BatchOptions,
    BatchRequest,
    BatchResponse,
    NTPEClient,
    SDKBatchAPI,
    SDKTranslationAPI,
    build_sdk_batch_manifest,
    sdk_batch_translate,
    sdk_batch_translate_async,
    sdk_translate_files,
)


def show(name: str, ok: bool) -> bool:
    print(f"{name:<30} {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    checks = []
    client = NTPEClient(translator=lambda segment, context: {"translation": f"譯文:{segment}", "context_seen": bool(context)})
    api = SDKBatchAPI(client=client, metadata={"test": "stage-07.3"})

    manifest = build_sdk_batch_manifest()
    checks.append(show("Batch Manifest", manifest.get("stage") == "NTPE 1.0 Beta Stage-07.3 SDK Batch API"))
    checks.append(show("SDK Translation Compatible", manifest.get("sdk_translation_compatibility") == "stage-07.2 sdk translation api compatible"))
    checks.append(show("Backward Compatible", manifest.get("backward_compatible") is True))

    response = api.translate_texts(["A", "B"], BatchOptions(job_id="sdk-batch-text"))
    checks.append(show("SDK Batch Text", response.ok and response.texts == ["譯文:A", "譯文:B"]))
    checks.append(show("Batch Response Object", isinstance(response, BatchResponse) and response.progress.percent == 100.0))
    checks.append(show("Batch Progress Query", api.progress().completed == 2 and api.progress().failed == 0))

    callback_events = []
    def callback(progress, result):
        callback_events.append((progress.completed, progress.failed, None if result is None else result.item_id))

    callback_response = api.translate_batch(BatchRequest.from_texts(["C", "D"], BatchOptions(job_id="sdk-batch-callback")), progress_callback=callback)
    checks.append(show("Batch Callback", callback_response.ok and len(callback_events) >= 4 and callback_events[-1][0] == 2))

    with tempfile.TemporaryDirectory() as tmp:
        input_a = Path(tmp) / "a.txt"
        input_b = Path(tmp) / "b.txt"
        output_dir = Path(tmp) / "out"
        input_a.write_text("FILE_A", encoding="utf-8")
        input_b.write_text("FILE_B", encoding="utf-8")
        file_response = api.translate_files([str(input_a), str(input_b)], BatchOptions(job_id="sdk-batch-files", write_outputs=True, output_dir=str(output_dir)))
        outputs = sorted(output_dir.glob("*_zh.txt"))
        checks.append(show("SDK Batch Files", file_response.ok and file_response.texts == ["譯文:FILE_A", "譯文:FILE_B"]))
        checks.append(show("Batch Output Writing", len(outputs) == 2 and outputs[0].read_text(encoding="utf-8").startswith("譯文:")))

    mixed_request = BatchRequest(
        items=[
            BatchItem(item_id="ok", text="OK"),
            BatchItem(item_id="missing", file_path="/path/does/not/exist.txt"),
            BatchItem(item_id="after", text="AFTER"),
        ],
        options=BatchOptions(job_id="sdk-batch-error", continue_on_error=True),
    )
    mixed_response = api.translate_batch(mixed_request)
    checks.append(show("Batch Error Isolation", not mixed_response.ok and mixed_response.progress.completed == 2 and mixed_response.progress.failed == 1))
    checks.append(show("Batch Result Summary", mixed_response.texts == ["譯文:OK", "譯文:AFTER"] and len(mixed_response.failed_results) == 1))

    stop_request = BatchRequest(
        items=[BatchItem(item_id="missing", file_path="/path/does/not/exist.txt"), BatchItem(item_id="skip", text="SKIP")],
        options=BatchOptions(job_id="sdk-batch-stop", continue_on_error=False),
    )
    stop_response = api.translate_batch(stop_request)
    checks.append(show("Batch Stop On Error", not stop_response.ok and len(stop_response.results) == 1 and stop_response.progress.failed == 1))

    future = api.translate_batch_async(BatchRequest.from_texts(["ASYNC"], BatchOptions(job_id="sdk-batch-async")))
    async_response = future.result(timeout=5)
    checks.append(show("Batch Async", async_response.ok and async_response.texts == ["譯文:ASYNC"]))

    module_response = sdk_batch_translate(["M1", "M2"], client=client, options=BatchOptions(job_id="module-batch"))
    checks.append(show("Module Batch API", module_response.ok and module_response.texts == ["譯文:M1", "譯文:M2"]))

    module_future = sdk_batch_translate_async(["MF"], client=client, options=BatchOptions(job_id="module-batch-async"))
    checks.append(show("Module Batch Async", module_future.result(timeout=5).texts == ["譯文:MF"]))

    with tempfile.TemporaryDirectory() as tmp:
        input_path = Path(tmp) / "module_file.txt"
        input_path.write_text("MODULE_FILE", encoding="utf-8")
        module_files = sdk_translate_files([str(input_path)], client=client, options=BatchOptions(job_id="module-files"))
        checks.append(show("Module Batch Files", module_files.ok and module_files.texts == ["譯文:MODULE_FILE"]))

    dict_request = {
        "items": [{"item_id": "dict", "text": "DICT"}],
        "options": {"job_id": "dict-batch", "metadata": {"case": "dict"}},
    }
    dict_response = api.translate_batch(dict_request)
    checks.append(show("Batch Dict Serialization", dict_response.ok and dict_response.job_id == "dict-batch"))

    api_manifest = api.manifest()
    checks.append(show("Runtime Reuse", api_manifest.get("metadata", {}).get("client_version") == client.version))
    checks.append(show("Translation API Reuse", isinstance(api.translation_api, SDKTranslationAPI)))

    if all(checks):
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
