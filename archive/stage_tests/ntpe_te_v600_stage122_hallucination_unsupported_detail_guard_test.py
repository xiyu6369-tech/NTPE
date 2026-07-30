from __future__ import annotations

from pathlib import Path

from core.translation_naturalness import (
    UNSUPPORTED_DETAIL_GUARD_VERSION,
    analyze_unsupported_details,
)


def _assert(name: str, condition: bool) -> None:
    print(f"{name:<48} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("TE v6.0 Stage 12.2 Hallucination / Unsupported Detail Guard")
    print("=" * 70)

    transport = analyze_unsupported_details("그 섬은 멀리 떨어져 있었다.", "那座島沒有直通交通工具，只能搭乘小型飛機前往。")
    _assert("Unsupported transport becomes blocking issue", any(i["code"] == "ADDED_DETAIL" for i in transport.issues))

    supported_transport = analyze_unsupported_details("소형 비행기로 그 섬에 갔다.", "搭乘小型飛機前往那座島。")
    _assert("Supported transport is not flagged", not supported_transport.issues)

    island = analyze_unsupported_details("그 섬은 아주 작았다.", "拉古恩島很小。")
    _assert("Unsupported named island is detected", any(i["code"] == "HALLUCINATION" for i in island.issues))

    generic_island = analyze_unsupported_details("그 섬은 아주 작았다.", "這座島很小。")
    _assert("Generic island wording is allowed", not generic_island.issues)

    duration = analyze_unsupported_details("그는 계속 화를 냈다.", "他足足哀號了四天。")
    _assert("Unsupported explicit duration is detected", any(i["code"] == "ADDED_DETAIL" for i in duration.issues))

    supported_duration = analyze_unsupported_details("그는 나흘 동안 화를 냈다.", "他生了四天的氣。")
    _assert("Supported duration is not flagged", not supported_duration.issues)

    metadata = island.to_metadata()
    _assert("Metadata is fail-closed and offline", metadata["fail_closed"] and not metadata["provider_called"])
    _assert("Stage version is correct", metadata["version"] == UNSUPPORTED_DETAIL_GUARD_VERSION)

    runtime = Path("lts/txt_translation_runtime.py").read_text(encoding="utf-8")
    _assert("Runtime invokes unsupported detail guard", "analyze_unsupported_details(chunk, evaluated_text)" in runtime)
    _assert("Runtime stores guard metadata", '"unsupported_detail_guard"' in runtime)

    print("ALL PASS")


if __name__ == "__main__":
    main()
