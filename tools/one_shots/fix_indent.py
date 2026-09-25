with open('tests/contract/test_s5c_reference_integrity.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 632 (index 631): z.writestr at 0 -> 12 spaces
if len(lines) > 631:
    line = lines[631]
    if line.lstrip().startswith('z.writestr("OEBPS/nav.xhtml"'):
        lines[631] = '            ' + lines[631].lstrip()

# Fix line 633 (index 632): empty line with 13 spaces -> 12
if len(lines) > 632:
    line = lines[632]
    if line.strip() == '' and len(line) - len(line.lstrip()) == 13:
        lines[632] = '            \n'

# Lines 634-640 (indices 633-639): should be 12 spaces (already correct)
# Line 641 (blank): at 1 space -> should be 8 (method level)
if len(lines) > 640:
    line = lines[640]
    if len(line) - len(line.lstrip()) == 1:
        lines[640] = '        ' + lines[640].lstrip()

# Lines 642-645 (indices 641-644): at module level (0), should be 8 spaces (method level)
for i in range(641, 645):
    if i < len(lines):
        line = lines[i]
        if line.strip():
            lines[i] = '        ' + lines[i].lstrip()
        else:
            lines[i] = '        \n'

# Write back
with open('tests/contract/test_s5c_reference_integrity.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed!")