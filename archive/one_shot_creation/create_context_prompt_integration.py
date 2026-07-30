from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "core" / "prompt_builder" / "prompt_builder.py"

text = TARGET.read_text(encoding="utf-8")

# 1. 加入 import
if "from core.context.memory_engine import ContextMemoryEngine" not in text:
    text = text.replace(
        "from .utils import save_json\n",
        "from .utils import save_json\n\n"
        "try:\n"
        "    from core.context.memory_engine import ContextMemoryEngine\n"
        "except Exception:\n"
        "    ContextMemoryEngine = None\n"
    )

# 2. 在 __init__ 加入 self.context_memory
if "self.context_memory = ContextMemoryEngine(self.root) if ContextMemoryEngine else None" not in text:
    text = text.replace(
        "self.package_builder = PackageBuilder()\n",
        "self.package_builder = PackageBuilder()\n"
        "        self.context_memory = ContextMemoryEngine(self.root) if ContextMemoryEngine else None\n"
    )

# 3. context 預設值改成讀取 Context Memory
old = '''if context is None:
            context = {
                "previous_summary": "",
                "previous_chunk_tail": "",
                "recent_characters": [],
                "recent_terms": [],
            }'''

new = '''if context is None:
            if self.context_memory:
                context = self.context_memory.build_context()
            else:
                context = {
                    "previous_summary": "",
                    "previous_chunk_tail": "",
                    "recent_characters": [],
                    "recent_terms": [],
                }'''

if old in text:
    text = text.replace(old, new)

TARGET.write_text(text, encoding="utf-8")
print("Prompt Builder integrated with Context Memory.")