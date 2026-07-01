from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.plugins import PipelinePluginManager


def main():

    manager = PipelinePluginManager(ROOT)
    registry = manager.build_registry()

    payload = {

        "previous_tail": "鄭泰義默默看著門口。",

        "chunk_text": """
초인종이 울린 순간 정태의는 멈칫했다.

손에 쥐고 있던 젓가락에서 콩자반이 떨어져 굴렀다.

방 안은 숨조차 들리지 않을 만큼 조용했다.
""",

        "source_text": """
초인종이 울린 순간 정태의는 멈칫했다.

손에 쥐고 있던 젓가락에서 콩자반이 떨어져 굴렀다.

방 안은 숨조차 들리지 않을 만큼 조용했다.
""",

        "translation_text": """
門鈴響起的瞬間，鄭泰義愣了一下。

他手中的筷子滑落，黑豆滾到了桌角。

房間裡安靜得連呼吸聲都聽不到。
""",

        "file_name": "plugin_flow_test.txt",

        "chunk_index": 1,

        "chunk_total": 1,

        "session_id": "PLUGIN_FLOW_TEST",

    }

    payload = registry.run_stage("context", payload)

    payload = registry.run_stage("narrative", payload)

    payload = registry.run_stage("prompt", payload)

    payload = registry.run_stage("quality", payload)

    checks = {

        "Context":
            "context" in payload,

        "Narrative":
            "narrative_analysis" in payload,

        "Prompt":
            "prompt_package" in payload,

        "Quality":
            "coverage" in payload,

        "Semantic":
            "semantic_after" in payload,

    }

    print("NTPE Foundation Plugin Flow Test")
    print("================================")

    for name, ok in checks.items():
        print(f"{name:<15} {'PASS' if ok else 'FAIL'}")

    if not all(checks.values()):
        raise SystemExit(2)

    print("PASS")


if __name__ == "__main__":
    main()