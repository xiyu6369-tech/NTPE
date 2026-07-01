from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.plugins import PluginContext, PluginRegistry, QualityPlugin
from core.runtime import RuntimeManager


if __name__ == "__main__":
    runtime = RuntimeManager(ROOT)
    context = PluginContext(root=ROOT, runtime=runtime)

    registry = PluginRegistry(context)
    registry.register(QualityPlugin())

    payload = {
        "chunk_text": """
초인종이 울린 순간 정태의는 멈칫했다.

손에 쥐고 있던 젓가락에서 콩자반이 떨어져 굴렀다.
""",
        "translation_text": """
門鈴響起的瞬間，鄭泰義僵住了。

筷尖夾著的醬煮黑豆滑落下來，滾出盤緣。
""",
    }

    result = registry.run_stage("quality", payload)

    checks = {
        "Quality Plugin": "quality" in registry.list_plugins(),
        "Semantic Before": "semantic_before" in result,
        "Semantic After": "semantic_after" in result,
        "Coverage": "coverage" in result,
        "Translation Text": bool(result.get("translation_text")),
        "Semantic Repaired Flag": "semantic_repaired" in result,
    }

    print("NTPE v1.2 Foundation Quality Plugin Test")
    print("========================================")

    for name, ok in checks.items():
        print(f"{name:<24} {'PASS' if ok else 'FAIL'}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")