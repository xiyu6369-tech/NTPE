"""Test complete glossary data pipeline end-to-end v2."""
import sys
sys.path.insert(0, 'd:/Python/NTPE')

from core.prompt_builder import PromptBuilder

# Test full PromptBuilder
builder = PromptBuilder('d:/Python/NTPE')

# Test with a chunk containing glossary terms
chunk_text = "UNHRDO는 UNH와 협력하여 PASSION 프로젝트를 진행합니다. UNHR과 UNHRD도 참여합니다."

package = builder.build(
    chunk_text=chunk_text,
    file_name="test.txt",
    chunk_index=1,
    chunk_total=1,
    session_id="test_session"
)

print("=== PromptBuilder.build() ===")
print(f"Package keys: {list(package.keys())}")
for k, v in package.items():
    if isinstance(v, list) and v and isinstance(v[0], dict) and 'source' in v[0]:
        print(f"  {k}: {v}")

# Check the prompt contains glossary terms
prompt = package['prompt']
print(f"\nPrompt contains UNHRDO: {'UNHRDO' in prompt}")
print(f"Prompt contains UNH: {'UNH' in prompt}")
print(f"Prompt contains PASSION: {'PASSION' in prompt}")
print(f"Prompt contains UNHR: {'UNHR' in prompt}")
print(f"Prompt contains UNHRD: {'UNHRD' in prompt}")