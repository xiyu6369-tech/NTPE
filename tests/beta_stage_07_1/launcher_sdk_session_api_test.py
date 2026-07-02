from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdk import NTPEClient, SDKSession, build_sdk_session_manifest, create_session


def show(name: str, ok: bool) -> bool:
    print(f"{name:<30} {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    checks = []
    events = []
    client = NTPEClient(translator=lambda segment, context: {"translation": f"譯文:{segment}", "context_seen": bool(context)})

    manifest = build_sdk_session_manifest()
    checks.append(show("Session Manifest", manifest.get("stage") == "NTPE 1.0 Beta Stage-07.1 SDK Session API"))
    checks.append(show("SDK Core Compatible", manifest.get("sdk_core_compatibility") == "stage-07.0 sdk core compatible"))
    checks.append(show("Backward Compatible", manifest.get("backward_compatible") is True))

    session = create_session(client=client, job_id="sdk-session-test", segments=["A", "B"], on_event=events.append)
    checks.append(show("SDK Session Created", session.get_status().status == "created" and session.progress()["total_segments"] == 2))

    session.start()
    result = session.result()
    checks.append(show("SDK Runtime Started", result["session"]["status"] == "completed"))
    checks.append(show("SDK Progress", result["session"]["progress_percent"] == 100.0 and result["session"]["result_count"] == 2))
    checks.append(show("SDK Result", result["ok"] is True and result["results"][0]["text"] == "譯文:A"))
    checks.append(show("SDK Callback", any(event["name"] == "completed" for event in events)))

    checkpoint = session.checkpoint()
    resumed = SDKSession.from_checkpoint(checkpoint, client=client, segments=["A", "B"])
    resumed.resume()
    checks.append(show("SDK Resume", resumed.get_status().status == "completed" and resumed.progress()["current_index"] == 2))

    session_manifest = session.manifest()
    checks.append(show("Session Client Reuse", session_manifest.get("metadata", {}).get("client_version") == client.version))

    checks.append(show("Public Imports", bool(SDKSession and create_session and build_sdk_session_manifest)))

    if all(checks):
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
