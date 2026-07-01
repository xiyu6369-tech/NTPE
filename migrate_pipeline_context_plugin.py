from pathlib import Path

ROOT = Path(__file__).resolve().parent
P = ROOT / "engine" / "pipeline" / "pipeline_v1.py"

text = P.read_text(encoding="utf-8")

# 1. 加入 helper method
if "def _build_plugin_payload(" not in text:
    marker = "    def _translate_with_retry("
    helper = '''    def _build_plugin_payload(
        self,
        *,
        chunk,
        file_path: Path,
        chunk_total: int,
        session_id: str,
        previous_tail: str = "",
        translation_text: str = "",
    ) -> dict:
        return {
            "previous_tail": previous_tail,
            "chunk_text": chunk.text,
            "source_text": chunk.text,
            "translation_text": translation_text,
            "file_name": file_path.name,
            "chunk_index": chunk.index,
            "chunk_total": chunk_total,
            "session_id": session_id,
        }

'''
    text = text.replace(marker, helper + marker)

# 2. 在 prompt_builder.build 前建立 plugin context
old = '''                    package = prompt_builder.build(
                        chunk_text=chunk.text,
                        file_name=file_path.name,
                        chunk_index=chunk.index,
                        chunk_total=len(chunks),
                        session_id=f"PIPELINE_V1_{file_path.stem}",
                    )'''

new = '''                    plugin_payload = self._build_plugin_payload(
                        chunk=chunk,
                        file_path=file_path,
                        chunk_total=len(chunks),
                        session_id=f"PIPELINE_V1_{file_path.stem}",
                    )

                    try:
                        plugin_payload = self.plugin_adapter.build_context(plugin_payload)
                        plugin_context = plugin_payload.get("context")
                    except Exception as e:
                        append_log(self.log_path, f"PLUGIN CONTEXT FALLBACK {file_path.name} chunk {chunk.index}: {e}")
                        plugin_context = None

                    package = prompt_builder.build(
                        chunk_text=chunk.text,
                        file_name=file_path.name,
                        chunk_index=chunk.index,
                        chunk_total=len(chunks),
                        session_id=f"PIPELINE_V1_{file_path.stem}",
                        context=plugin_context,
                    )'''

if old in text:
    text = text.replace(old, new)
else:
    print("WARN: prompt_builder.build block not found or already migrated.")

P.write_text(text, encoding="utf-8")
print("Foundation-04.2 Context Migration applied.")