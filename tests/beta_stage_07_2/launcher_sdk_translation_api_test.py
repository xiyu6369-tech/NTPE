from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdk import (
    NTPEClient,
    SDKTranslationAPI,
    TranslationOptions,
    TranslationRequest,
    TranslationResponse,
    build_sdk_translation_manifest,
    translate,
    translate_async,
    translate_batch,
    translate_file,
)


def show(name: str, ok: bool) -> bool:
    print(f"{name:<30} {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    checks = []
    client = NTPEClient(translator=lambda segment, context: {"translation": f"譯文:{segment}", "context_seen": bool(context)})
    api = SDKTranslationAPI(client=client, metadata={"test": "stage-07.2"})

    manifest = build_sdk_translation_manifest()
    checks.append(show("Translation Manifest", manifest.get("stage") == "NTPE 1.0 Beta Stage-07.2 SDK Translation API"))
    checks.append(show("SDK Session Compatible", manifest.get("sdk_session_compatibility") == "stage-07.1 sdk session api compatible"))
    checks.append(show("Backward Compatible", manifest.get("backward_compatible") is True))

    options = TranslationOptions(job_id="sdk-translation-test", metadata={"case": "text"})
    text_response = api.translate_text("A", options)
    checks.append(show("SDK Translate Text", text_response.ok and text_response.text == "譯文:A" and text_response.job_id == "sdk-translation-test"))
    checks.append(show("SDK Response Object", isinstance(text_response, TranslationResponse) and text_response.to_dict()["ok"] is True))

    batch_response = api.translate_batch(["A", "B"], TranslationOptions(job_id="sdk-batch-test"))
    checks.append(show("SDK Batch Translation", batch_response.ok and batch_response.results == ["譯文:A", "譯文:B"]))

    with tempfile.TemporaryDirectory() as tmp:
        input_path = Path(tmp) / "input.txt"
        output_path = Path(tmp) / "output.txt"
        input_path.write_text("FILE", encoding="utf-8")
        file_response = api.translate_file(str(input_path), TranslationOptions(job_id="sdk-file-test"))
        api.write_file(file_response, str(output_path))
        checks.append(show("SDK Translate File", file_response.ok and file_response.text == "譯文:FILE"))
        checks.append(show("SDK Write File", output_path.read_text(encoding="utf-8") == "譯文:FILE"))

    async_future = api.translate_async(TranslationRequest.for_text("ASYNC", TranslationOptions(job_id="sdk-async-test")))
    async_response = async_future.result(timeout=5)
    checks.append(show("SDK Async Translation", async_response.ok and async_response.text == "譯文:ASYNC"))

    module_text = translate("M", client=client, options=TranslationOptions(job_id="module-text"))
    module_batch = translate_batch(["M1", "M2"], client=client, options=TranslationOptions(job_id="module-batch"))
    module_future = translate_async("MF", client=client, options=TranslationOptions(job_id="module-async"))
    checks.append(show("Module Translate", module_text.ok and module_text.text == "譯文:M"))
    checks.append(show("Module Batch", module_batch.ok and module_batch.results == ["譯文:M1", "譯文:M2"]))
    checks.append(show("Module Async", module_future.result(timeout=5).text == "譯文:MF"))

    with tempfile.TemporaryDirectory() as tmp:
        input_path = Path(tmp) / "module_file.txt"
        input_path.write_text("MODULE_FILE", encoding="utf-8")
        module_file = translate_file(str(input_path), client=client, options=TranslationOptions(job_id="module-file"))
        checks.append(show("Module File", module_file.ok and module_file.text == "譯文:MODULE_FILE"))

    request = TranslationRequest.from_dict({"text": "DICT", "options": {"job_id": "dict-job"}})
    dict_response = api.translate(request)
    checks.append(show("Dict Serialization", dict_response.ok and request.to_dict()["options"]["job_id"] == "dict-job"))

    api_manifest = api.manifest()
    checks.append(show("SDK Runtime Integration", api_manifest.get("metadata", {}).get("client_version") == client.version))

    checks.append(show("Public Imports", bool(SDKTranslationAPI and TranslationOptions and TranslationRequest and TranslationResponse)))

    if all(checks):
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
