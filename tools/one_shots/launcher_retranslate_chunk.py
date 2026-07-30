# =====================================================
# NTPE v0.9.1.2 Retranslate Chunk Tool
# 指定重翻某一本 normalized TXT 的某個 chunk
#
# 預設：
# python launcher_retranslate_chunk.py
#
# 指定：
# python launcher_retranslate_chunk.py passion1_normalized.txt 1
# =====================================================

from pathlib import Path
import sys

from engine.pipeline.retranslate_chunk import RetranslateChunkTool

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    file_name = sys.argv[1] if len(sys.argv) >= 2 else "passion1_normalized.txt"
    chunk_index = int(sys.argv[2]) if len(sys.argv) >= 3 else 1

    tool = RetranslateChunkTool(root=ROOT)
    result = tool.run(file_name=file_name, chunk_index=chunk_index)

    print("")
    print("NTPE v0.9.1.2 Retranslate Chunk Tool")
    print("====================================")
    print(f"status: {result['status']}")
    print(f"file: {file_name}")
    print(f"chunk: {chunk_index}")
    print(f"output: {result.get('output_path', '')}")

    if result["status"] != "success":
        print(f"error: {result.get('error', '')}")
