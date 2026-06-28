# =====================================================
# NTPE Pipeline Engine v1.0 Core
# Launcher
# 放置位置：D:\Python\NTPE\launcher_pipeline.py
# =====================================================

from pathlib import Path
from engine.pipeline.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    pipeline = Pipeline(root=ROOT)
    result = pipeline.run_demo()

    print("NTPE Pipeline Engine v1.0 Core")
    print("==============================")
    print(f"status: {result['status']}")
    print(f"session_id: {result.get('session_id', '')}")
    print(f"stages: {len(result.get('stages', []))}")

    for stage in result.get("stages", []):
        print(f"- {stage['stage']}: {stage['status']}")

    if result["status"] != "success":
        print(f"error: {result.get('error', '')}")
