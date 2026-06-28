# =====================================================
# NTPE v0.9.0 Production Pipeline
# Launcher
# 放置位置：D:\Python\NTPE\launcher_pipeline_production.py
# =====================================================

from pathlib import Path
from engine.pipeline.production_pipeline import ProductionPipeline

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    pipeline = ProductionPipeline(root=ROOT)
    result = pipeline.run()

    print("NTPE v0.9.0 Production Pipeline")
    print("===============================")
    print(f"status: {result['status']}")
    print(f"session_id: {result.get('session_id', '')}")
    print(f"files: {result.get('file_count', 0)}")
    print(f"chunks: {result.get('chunk_count', 0)}")
    print(f"translated: {result.get('translated_count', 0)}")
    print(f"final_outputs: {len(result.get('final_outputs', []))}")

    if result["status"] != "success":
        print(f"error: {result.get('error', '')}")
