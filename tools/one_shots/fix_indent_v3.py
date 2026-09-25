with open('tests/contract/test_s5c_reference_integrity.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 511 (index 510): z.writestr at 24 spaces -> 12
if len(lines) > 510:
    line = lines[510]
    if line.lstrip().startswith('z.writestr("OEBPS/nav.xhtml"'):
        lines[510] = '            ' + lines[510].lstrip()

# Fix line 512 (index 511): empty line with 13 spaces -> 12 or 0
if len(lines) > 511:
    line = lines[511]
    if line.strip() == '' and len(line) - len(line.lstrip()) == 13:
        lines[511] = '            \n'

# Line 520 (index 519): z.writestr at 24 spaces -> 12
if len(lines) > 519:
    line = lines[519]
    if line.lstrip().startswith('z.writestr("OEBPS/chapter01.xhtml"'):
        lines[519] = '            ' + lines[519].lstrip()

# Line 521 (blank): at 16 spaces -> 0 or 8
if len(lines) > 520:
    line = lines[520]
    if line.strip() == '' and len(line) - len(line.lstrip()) == 16:
        lines[520] = '\n'

# Lines after with block (from import onwards) - should be at method level (8 spaces)
# These are at indices 522-524 (0-indexed 521-523)
for i in [521, 522, 522, 523]:  # indices 522, 523, 524 (1-indexed 523, 524, 524)
    if i < len(lines):
        line = lines[i]
        if line.strip() and not line.startswith('        '):
            lines[i] = '        ' + line.lstrip()

# Empty lines at module level (1 space) -> 0
for i in [525, 526]:  # indices 525, 526 (1-indexed 526, 527)
    if i < len(lines):
        line = lines[i]
        if line.strip() == '' and len(line) - len(line.lstrip()) > 0:
            lines[i] = '\n'

# Write back
with open('tests/contract/test_s5c_reference_integrity.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed!")