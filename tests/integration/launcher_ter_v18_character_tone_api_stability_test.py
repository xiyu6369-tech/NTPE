import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.literary import normalize_literary_style
print('NTPE TER-v1.8 Integration Test')
text = '伊萊開心地笑了，說：「當然。」說完便轉身離去，只留下那句令人費解的話。'
out = normalize_literary_style(text)
assert '開心地笑' not in out
assert '覺得有趣' in out
assert ('只答了一句「當然」' in out) or ('怎麼解讀' in out)
print('PASS')
