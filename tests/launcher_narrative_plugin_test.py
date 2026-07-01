from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.plugins import (
    PluginContext,
    PluginRegistry,
    NarrativePlugin,
)
from core.runtime import RuntimeManager


if __name__ == "__main__":
    runtime = RuntimeManager(ROOT)
    context = PluginContext(root=ROOT, runtime=runtime)

    registry = PluginRegistry(context)
    registry.register(NarrativePlugin())

    payload = {
        "chunk_text": """
초인종이 울린 순간 정태의는 멈칫했다.

손에 쥐고 있던 젓가락에서 콩자반이 떨어져 굴렀다.

방 안은 숨조차 들리지 않을 만큼 조용했다.
"""
    }

    result = registry.run_stage("narrative", payload)

    checks = {
        "Plugin Registered": "narrative" in registry.list_plugins(),
        "Stage Registered": "narrative" in registry.list_stages(),
        "Narrative Analysis": "narrative_analysis" in result,
        "Narrative Rules": "narrative_prompt_rules" in result,
        "Rules Generated": len(result["narrative_prompt_rules"]) > 0,
    }

    print("NTPE v1.2 Foundation Narrative Plugin Test")
    print("==========================================")

    for name, ok in checks.items():
        print(f"{name:<22} {'PASS' if ok else 'FAIL'}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")