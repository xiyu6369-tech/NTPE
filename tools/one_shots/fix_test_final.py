with open('D:\\Python\\NTPE\\tests\\contract\\test_s5c_reference_integrity.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Fix specific lines
# Line 632 (index 631): z.writestr at 0 -> 12 spaces
# Line 633 (empty): 13 spaces -> 12 or 0
# Lines 642-645: at 0 -> 8 spaces

new_lines = []
for i, line in enumerate(content.split('\n')):
    line_num = i + 1
    
    if line_num == 632:  # z.writestr("OEBPS/nav.xhtml"...
        new_lines.append('            ' + line.lstrip())
    elif line_num == 633:  # empty line with 13 spaces
        new_lines.append('            \n')
    elif 635 <= line_num <= 640:  # lines 635-640 (1-indexed)
        # These are at 12, should stay 12 (inside with block)
        new_lines.append(line)
    elif line_num in [642, 643, 643, 644, 644]:  # lines 642-645
        # These are at module level, should be at method level (8 spaces)
        if line.strip():
            new_lines.append('        ' + line.lstrip())
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open('tests/contract/test_s5c_reference_integrity.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print("Fixed!")