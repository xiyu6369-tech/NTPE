from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.plugins import PipelinePluginAdapter


if __name__ == "__main__":
    adapter = PipelinePluginAdapter(ROOT)

    payload = {
        "previous_tail": "鄭泰義默默看著門口。",
        "chunk_text": """
초인종이 울린 순간 정태의는 멈칫했다.

손에 쥐고 있던 젓가락에서 콩자반이 떨어져 굴렀다.
""",
        "source_text": """
초인종이 울린 순간 정태의는 멈칫했다.

손에 쥐고 있던 젓가락에서 콩자반이 떨어져 굴렀다.
""",
        "translation_text": """
門鈴響起的瞬間，鄭泰義愣了一下。

筷尖夾著的醬煮黑豆滑落下來，滾出盤緣。
""",
        "file_name": "adapter_test.txt",
        "chunk_index": 1,
        "chunk_total": 1,
        "session_id": "PIPELINE_PLUGIN_ADAPTER_TEST",
    }

    pre = adapter.run_pre_translation(payload)
    post = adapter.run_post_translation(pre)

    checks = {
        "Context": "context" in pre,
        "Narrative": "narrative_analysis" in pre,
        "Prompt Package": "prompt_package" in pre,
        "Quality": "coverage" in post,
        "Semantic": "semantic_after" in post,
    }

    print("NTPE Foundation Pipeline Plugin Adapter Test")
    print("============================================")

    for name, ok in checks.items():
        print(f"{name:<18} {'PASS' if ok else 'FAIL'}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")