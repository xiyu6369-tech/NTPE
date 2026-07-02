from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdk import (
    NTPEClient,
    SDKStreamingAPI,
    StreamEvent,
    StreamOptions,
    StreamResponse,
    collect_stream,
    stream,
    stream_async,
    build_sdk_stream_manifest,
)
from sdk.translation import SDKTranslationAPI


def show(name: str, ok: bool) -> bool:
    print(f"{name:<30} {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    checks = []
    client = NTPEClient(translator=lambda segment, context: {"translation": f"譯文 {segment}", "context_seen": bool(context)})
    api = SDKStreamingAPI(client=client, metadata={"test": "stage-07.4"})

    manifest = build_sdk_stream_manifest()
    checks.append(show("Stream Manifest", manifest.get("stage") == "NTPE 1.0 Beta Stage-07.4 SDK Streaming API"))
    checks.append(show("SDK Batch Compatible", manifest.get("sdk_batch_compatibility") == "stage-07.3 sdk batch api compatible"))
    checks.append(show("Backward Compatible", manifest.get("backward_compatible") is True))

    events = list(api.stream_text("A", StreamOptions(job_id="sdk-stream-text")))
    event_types = [event.type for event in events]
    checks.append(show("SDK Stream Created", event_types[0] == "started" and events[0].job_id == "sdk-stream-text"))
    checks.append(show("SDK Stream Translation", "segment" in event_types and events[-1].type == "completed" and events[-1].text == "譯文 A"))
    checks.append(show("SDK Stream Tokens", any(event.type == "token" for event in events)))
    checks.append(show("SDK Stream Progress", api.progress().status == "completed" and api.progress().progress == 100.0))

    callback_events = []
    response = api.collect(["B", "C"], StreamOptions(job_id="sdk-stream-callback"), callback=callback_events.append)
    checks.append(show("SDK Stream Callback", response.ok and len(callback_events) == response.event_count and callback_events[-1].type == "completed"))
    checks.append(show("Stream Response Object", isinstance(response, StreamResponse) and response.text == "譯文 B\n譯文 C"))

    dict_response = api.collect({"segments": ["D", "E"]}, StreamOptions(job_id="sdk-stream-dict", emit_tokens=False))
    checks.append(show("Stream Dict Request", dict_response.ok and dict_response.text == "譯文 D\n譯文 E" and not any(e.type == "token" for e in dict_response.events)))

    with tempfile.TemporaryDirectory() as tmp:
        input_path = Path(tmp) / "stream.txt"
        input_path.write_text("FILE", encoding="utf-8")
        file_response = api.collect_file(str(input_path), StreamOptions(job_id="sdk-stream-file"))
        checks.append(show("SDK Stream File", file_response.ok and file_response.text == "譯文 FILE"))

    future = api.stream_async("ASYNC", StreamOptions(job_id="sdk-stream-async"))
    async_response = future.result(timeout=5)
    checks.append(show("SDK Stream Async", async_response.ok and async_response.text == "譯文 ASYNC"))

    module_events = list(stream("M", client=client, options=StreamOptions(job_id="module-stream")))
    checks.append(show("Module Stream API", module_events[-1].type == "completed" and module_events[-1].text == "譯文 M"))

    module_response = collect_stream(["M1", "M2"], client=client, options=StreamOptions(job_id="module-collect"))
    checks.append(show("Module Stream Collect", module_response.ok and module_response.text == "譯文 M1\n譯文 M2"))

    module_future = stream_async("MF", client=client, options=StreamOptions(job_id="module-stream-async"))
    checks.append(show("Module Stream Async", module_future.result(timeout=5).text == "譯文 MF"))

    failing_client = NTPEClient(translator=lambda segment, context: (_ for _ in ()).throw(RuntimeError("boom")))
    failing_api = SDKStreamingAPI(client=failing_client)
    error_events = list(failing_api.stream_text("ERR", StreamOptions(job_id="sdk-stream-error")))
    checks.append(show("SDK Error Handling", any(event.type == "error" for event in error_events) and error_events[-1].type == "error"))

    serialized = events[0].to_dict()
    restored = StreamEvent.from_dict(serialized)
    checks.append(show("Stream Event Serialization", restored.type == events[0].type and restored.job_id == events[0].job_id))

    api_manifest = api.manifest()
    checks.append(show("Runtime Bridge", api_manifest.get("metadata", {}).get("client_version") == client.version))
    checks.append(show("Translation API Reuse", isinstance(api.translation_api, SDKTranslationAPI)))

    if all(checks):
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
