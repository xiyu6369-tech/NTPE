with open('tests/contract/test_s5c_reference_integrity.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 632 (index 631): z.writestr at 12 spaces -> keep 12 (correct)
# Fix line 633 (index 632): empty line with 13 spaces -> 0
if len(lines) > 632:
    line = lines[632]
    if line.strip() == '' and len(line) - len(line.lstrip()) == 13:
        lines[632] = '\n'

# Line 641 (index 640): blank line after with block, at 16 spaces -> should be 0 or 8
if len(lines) > 640:
    line = lines[640]
    if line.strip() == '' and len(line) - len(line.lstrip()) == 16:
        lines[640] = '\n'

# Lines 642-644 (indices 641-643): from/errors/assert at 8 spaces (correct for method level)
# But they should be at 8 spaces (method level), which they are
# Line 645 (index 644): empty line with 1 space -> should be 0
if len(lines) > 644:
    line = lines[644]
    if line.strip() == '' and len(line) - len(line.lstrip()) == 1:
        lines[644] = '\n'
    elif line.strip() == '' and len(line) - len(line.lstrip()) != 0:
        lines[644] = '\n'

# Line 646 (index 645): empty line with 1 space
if len(lines) > 645:
    line = lines[645]
    if line.strip() == '' and len(line) - len(line.lstrip()) == 1:
        lines[645] = '\n'

# Write back
with open('tests/contract/test_s5c_reference_integrity.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed!")