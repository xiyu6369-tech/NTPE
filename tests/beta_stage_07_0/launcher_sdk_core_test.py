from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.ai_provider.contracts import MockProvider
from core.ai_provider.manager import ProviderManager
from core.ai_provider.registry import ProviderRegistry
from sdk import NTPEClient, SDKRequest, SDKResult, attach_sdk_manifest, build_sdk_manifest


def show(name: str, ok: bool) -> bool:
    print(f"{name:<30} {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    checks = []

    manifest = build_sdk_manifest()
    checks.append(show("Manifest Stage", manifest.get("stage") == "NTPE 1.0 Beta Stage-07.0 SDK Core"))
    checks.append(show("Foundation Compatible", manifest.get("foundation_compatibility") == "foundation-v1.0 frozen compatible"))
    checks.append(show("CLI Compatible", manifest.get("cli_compatibility") == "stage-06.9 cli freeze compatible"))
    checks.append(show("Backward Compatible", manifest.get("backward_compatible") is True))

    request = SDKRequest(text="안녕하세요", job_id="sdk-test", metadata={"case": "core"})
    encoded = json.dumps(request.to_dict(), ensure_ascii=False)
    decoded = json.loads(encoded)
    checks.append(show("Request Serializable", decoded["text"] == "안녕하세요" and decoded["target_language"] == "zh-TW"))

    result = SDKResult.success("你好", job_id="sdk-test", session_id="session-1")
    result_payload = result.to_dict()
    checks.append(show("Result Serializable", result_payload["ok"] is True and result_payload["text"] == "你好"))

    client = NTPEClient(translator=lambda segment, context: {"translation": f"譯文:{segment}", "context_seen": bool(context)})
    translated = client.translate(request)
    checks.append(show("Client Translate", translated.ok and translated.text == "譯文:안녕하세요"))
    checks.append(show("Session Attached", bool(translated.session_id)))

    text_result = client.translate_text("테스트", job_id="sdk-text")
    checks.append(show("Translate Text", text_result.ok and text_result.text == "譯文:테스트"))

    segment_results = client.translate_segments(["A", "B"], job_id="sdk-segments")
    checks.append(show("Translate Segments", len(segment_results) == 2 and all(item.ok for item in segment_results)))

    prompt_package = client.prompt_package("문장", metadata={"mode": "prompt"})
    checks.append(show("Prompt Package", prompt_package.get("type") == "translation_prompt_package" and prompt_package.get("source") == "문장"))

    registry = ProviderRegistry()
    registry.register(MockProvider(name="mock-sdk", response_text="provider translation"), default=True)
    provider_client = NTPEClient(provider_manager=ProviderManager(registry=registry))
    provider_result = provider_client.translate_text("provider prompt", job_id="sdk-provider", model="mock-model")
    checks.append(show("Provider Bridge", provider_result.ok and provider_result.text == "provider translation"))

    payload = attach_sdk_manifest({})
    checks.append(show("Attach Manifest", payload.get("manifests", {}).get("sdk", {}).get("version") == "0.7.0"))

    client_manifest = client.manifest()
    checks.append(show("Client Manifest", client_manifest.get("version") == "0.7.0" and "translation_engine" in client_manifest))

    public_imports = all([NTPEClient, SDKRequest, SDKResult])
    checks.append(show("Public Imports", public_imports))

    if all(checks):
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
