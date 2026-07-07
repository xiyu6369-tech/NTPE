import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.literary import normalize_literary_style

out = normalize_literary_style('挑起眉毛，然後就轉身走了。')
assert '眉毛' not in out
assert '轉身離去' in out
print('PASS')
