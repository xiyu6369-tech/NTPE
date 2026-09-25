# Fix indentation for the test_s5c_reference_integrity.py file
with open('D:\\Python\\NTPE\\tests\\contract\\test_s5c_reference_integrity.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix indentation for lines 598-640 (0-indexed: 597-639)
# The with block starts at line 598 (index 597) at 8 spaces
# Inside the with block should be at 12 spaces (8 + 4)

for i in range(597, 640):
    if i >= len(lines):
        break
    line = lines[i]
    if line.strip() == '':
        continue
    indent = len(line) - len(line.lstrip())
    stripped = line.lstrip()
    
    # Lines 599-631 (0-indexed: 598-630) should be at 12 spaces (inside with block)
    if 598 <= i <= 630:
        if indent == 12 and line.strip():
            lines[i] = '    ' + line
        elif indent == 13 and line.strip() == '':
            lines[i] = '                \n'
    
    # Line 632 (index 631): z.writestr("OEBPS/nav.xhtml"...) at 0 indent -> should be 16
    if i == 631 and indent == 0 and stripped:
        lines[i] = '                ' + stripped
    
    # Lines 633-639 (indices 632-638): empty line + ch1 block at 12, should be 16
    if 632 <= i <= 638:
        if indent == 13 and line.strip() == '':
            lines[i] = '                \n'
        elif indent == 12 and stripped:
            lines[i] = '    ' + line
    
    # Line 640: z.writestr at 12, should be 16
    if i == 639 and indent == 12 and stripped:
        lines[i] = '    ' + line

    # Lines 641-645: at module level (0), should be in method (8 spaces)
    if 640 <= i <= 644:
        if indent == 0 and stripped:
            lines[i] = '        ' + stripped

new_content = ''.join(lines)

with open('D:\\Python\\NTPE\\tests\\contract\\test_s5c_reference_integrity.py', 'w', encoding='utf-8') as f:
    f.write(''.join(lines))

print("Fixed!")