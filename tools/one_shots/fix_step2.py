with open('tests/contract/test_s5c_reference_integrity.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 521 (index 520): empty line at 9 spaces -> 0 (after with block)
if len(lines) > 520:
    line = lines[520]
    if line.strip() == '' and len(line) - len(line.lstrip()) == 9:
        lines[520] = '\n'

# Fix line 526 (index 525): empty line with 1 space -> 0
if len(lines) > 525:
    line = lines[525]
    if line.strip() == '' and len(line) - len(line.lstrip()) == 1:
        lines[525] = '\n'

# Fix line 527 (index 526): empty line with 1 space -> 0
if len(lines) > 526:
    line = lines[526]
    if line.strip() == '' and len(line) - len(line.lstrip()) == 1:
        lines[526] = '\n'

# Write back
with open('tests/contract/test_s5c_reference_integrity.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed!")