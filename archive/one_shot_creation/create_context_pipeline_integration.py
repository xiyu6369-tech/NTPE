from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "engine" / "pipeline" / "pipeline_v1.py"

text = TARGET.read_text(encoding="utf-8")

if "from core.context.memory_engine import ContextMemoryEngine" not in text:
    text = text.replace(
        "from core.quality.coverage_checker import CoverageChecker\n",
        "from core.quality.coverage_checker import CoverageChecker\n"
        "from core.context.memory_engine import ContextMemoryEngine\n"
    )

if "context_memory = ContextMemoryEngine(root=self.root)" not in text:
    text = text.replace(
        "coverage_checker = CoverageChecker(root=self.root)\n",
        "coverage_checker = CoverageChecker(root=self.root)\n"
        "            context_memory = ContextMemoryEngine(root=self.root)\n"
    )

marker = "save_json(state_path, chunk_state)\n"

insert = """save_json(state_path, chunk_state)

                    context_memory.update_after_chunk(
                        file_name=file_path.name,
                        chunk_index=chunk.index,
                        source_text=chunk.text,
                        translation_text=translation_text,
                    )
"""

if marker in text and "context_memory.update_after_chunk(" not in text:
    text = text.replace(marker, insert)

TARGET.write_text(text, encoding="utf-8")
print("Pipeline integrated with Context Memory.")