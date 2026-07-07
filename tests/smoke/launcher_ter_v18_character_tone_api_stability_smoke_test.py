import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.literary import normalize_literary_style
print('NTPE TER-v1.8 Smoke Test')
out = normalize_literary_style('伊萊開心地笑了，說：「當然。」')
assert '開心地笑' not in out
print('PASS')
