import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.literary import LiteraryPromptBuilder

res = LiteraryPromptBuilder().build(
    chunk_text='정태의는 일레이를 불렀다.',
    locked_dictionary={'정태의': '鄭泰義', '일레이': '伊萊'},
    profile='literary',
)
assert res.prompt_profile.total_tokens < 450
assert '정태의=鄭泰義' in res.user_prompt
assert '일레이=伊萊' in res.user_prompt
print('PASS')
