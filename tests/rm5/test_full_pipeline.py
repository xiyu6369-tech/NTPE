"""Test complete glossary data pipeline end-to-end."""
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
print(f"Glossary matches: {package['glossary_matches']}")

# Check the prompt contains glossary terms
prompt = package['prompt']
print(f"\nPrompt contains UNHRDO: {'UNHRDO' in prompt}")
print(f"Prompt contains UNH: {'UNH' in prompt}")
print(f"Prompt contains PASSION: {'PASSION' in prompt}")
print(f"Prompt contains UNHR: {'UNHR' in prompt}")
print(f"Prompt contains UNHRD: {'UNHRD' in prompt}")

# Test with English text
chunk_text2 = "The UNHRDO organization works with UNH on the PASSION project."
package2 = builder.build(
    chunk_text=chunk_text2,
    file_name="test2.txt",
    chunk_index=1,
    chunk_total=1,
    session_id="test_session2"
)

print("\n=== English text test ===")
print(f"Glossary matches: {package2['glossary_matches']}")