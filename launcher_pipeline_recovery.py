# =====================================================
# NTPE v0.9.1.1 Transactional Recovery Pipeline
# Launcher
# 放置位置：D:\Python\NTPE\launcher_pipeline_recovery.py
# =====================================================

from pathlib import Path
from engine.pipeline.recovery_pipeline import RecoveryPipeline

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    pipeline = RecoveryPipeline(root=ROOT)
    result = pipeline.run()

    print("")
    print("NTPE v0.9.1.1 Transactional Recovery")
    print("====================================")
    print(f"status: {result['status']}")
    print(f"session_id: {result.get('session_id', '')}")
    print(f"files: {result.get('file_count', 0)}")
    print(f"chunks_total: {result.get('chunk_count', 0)}")
    print(f"done: {result.get('done_count', 0)}")
    print(f"skipped: {result.get('skipped_count', 0)}")
    print(f"failed: {result.get('failed_count', 0)}")
    print(f"failed_dir: {result.get('failed_dir', '')}")
    print(f"final_outputs: {len(result.get('final_outputs', []))}")

    if result["status"] not in ["success", "partial_success"]:
        print(f"error: {result.get('error', '')}")
