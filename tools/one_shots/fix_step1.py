with open('tests/contract/test_s5c_reference_integrity.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 512 (index 511): empty line with 13 spaces -> 12
if len(lines) > 511:
    line = lines[511]
    if line.strip() == '' and len(line) - len(line.lstrip()) == 13:
        lines[511] = '            \n'

# Write back
with open('tests/contract/test_s5c_reference_integrity.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed first issue!")