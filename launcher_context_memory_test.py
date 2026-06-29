from pathlib import Path
import json

from core.context.memory_engine import ContextMemoryEngine

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    source_1 = """패션 1

초인종이 울린 순간 정태의는 멈칫했다.

손에 쥐고 있던 젓가락에서 콩자반이 떨어져 굴렀다.

정태의는 현관 쪽으로 신경질적인 시선을 주었다.
"""

    translation_1 = """《PASSION》第一卷

門鈴響起的瞬間，鄭泰義僵住了。

筷尖夾著的醬煮黑豆滑落下來，滾出盤緣。

鄭泰義帶著煩躁的目光望向玄關。
"""

    engine = ContextMemoryEngine(ROOT)

    states = engine.update_after_chunk(
        file_name="context_test.txt",
        chunk_index=1,
        source_text=source_1,
        translation_text=translation_1,
    )

    context = engine.build_context(previous_tail=translation_1[-300:])

    out = ROOT / "prompt_packages" / "context_memory_test_package.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "states": states,
                "context": context,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    checks = {
        "Story State": bool(states.get("story_state")),
        "Character State": "鄭泰義" in states.get("character_state", {}).get("characters", {}),
        "Scene State": bool(states.get("scene_state", {}).get("location") or states.get("scene_state", {}).get("objects")),
        "Dialogue State": "dialogue_state" in states,
        "Narrative State": bool(states.get("narrative_state")),
        "Context Builder": bool(context.get("previous_summary")),
        "Prompt Package": out.exists(),
    }

    print("NTPE v1.1 / TQF-06.2 Context Memory Engine")
    print("==========================================")

    for name, ok in checks.items():
        print(f"{name:<18} {'PASS' if ok else 'FAIL'}")

    print(f"package: {out}")

    if not all(checks.values()):
        raise SystemExit(2)

    print("PASS")