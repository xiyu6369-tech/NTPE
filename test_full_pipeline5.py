"""Test complete glossary data pipeline end-to-end v5."""
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

# Check the prompt structure
prompt_dict = package['prompt']
print(f"\nPrompt type: {type(prompt_dict)}")
print(f"Prompt keys: {list(prompt_dict.keys())}")
print(f"system_prompt: {prompt_dict.get('system_prompt', '')[:200]}...")
print(f"user_prompt contains UNHRDO: {'UNHRDO' in prompt_dict.get('user_prompt', '')}")
print(f"user_prompt contains UNH: {'UNH' in prompt_dict.get('user_prompt', '')}")
print(f"user_prompt contains PASSION: {'PASSION' in prompt_dict.get('user_prompt', '')}")
print(f"user_prompt contains UNHR: {'UNHR' in prompt_dict.get('user_prompt', '')}")
print(f"user_prompt contains UNHRD: {'UNHRD' in prompt_dict.get('user_prompt', '')}")

# Check for the glossary section in user_prompt
user_prompt = prompt_dict.get('user_prompt', '')
if '【本段術語】' in user_prompt:
    idx = user_prompt.index('【本段術語】')
    print(f"\n【本段術語】 section found at index {idx}")
    print(user_prompt[idx:idx+500])
else:
    print("\n【本段術語】 section NOT found in user_prompt")