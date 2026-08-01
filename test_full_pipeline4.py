"""Test complete glossary data pipeline end-to-end v4."""
import sys
sys.path.insert(0, 'd:/Python/NTPE')

from core.prompt_builder import PromptBuilder

# Test full PromptBuilder
builder = PromptBuilder('d:/Python/NTPE')

# Test with English text
chunk_text = "UNHRDO works with UNH on the PASSION project. UNHR and UNHRD also participate."

package = builder.build(
    chunk_text=chunk_text,
    file_name="test.txt",
    chunk_index=1,
    chunk_total=1,
    session_id="test_session"
)

print("=== English text test ===")
print(f"Glossary matches: {package['knowledge']['glossary_matches']}")

# Check the prompt contains glossary terms
prompt = package['prompt']
print(f"\nPrompt contains UNHRDO: {'UNHRDO' in prompt}")
print(f"Prompt contains UNH: {'UNH' in prompt}")
print(f"Prompt contains PASSION: {'PASSION' in prompt}")
print(f"Prompt contains UNHR: {'UNHR' in prompt}")
print(f"Prompt contains UNHRD: {'UNHRD' in prompt}")

# Also test Korean with spaces
chunk_text2 = "UNHRDO 는 UNH 와 협력하여 PASSION 프로젝트를 진행합니다."
package2 = builder.build(
    chunk_text=chunk_text2,
    file_name="test2.txt",
    chunk_index=1,
    chunk_total=1,
    session_id="test_session2"
)

print("\n=== Korean with spaces test ===")
print(f"Glossary matches: {package2['knowledge']['glossary_matches']}")