with open('tests/contract/test_s5c_reference_integrity.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check patterns
pattern1 = 'z.writestr("OEBPS/nav.xhtml", ET.tostring(nav, encoding="unicode"))'
pattern2 = '            \n            ch1 = ET.Element'
pattern3 = 'from core.epub_translation.runtime.epub_packager import _validate_epub_archive\nerrors = _validate_epub_archive(broken_epub)\n# Should detect the broken reference\nassert len(errors) > 0'

print('Pattern 1 found:', pattern1 in content)
print('Pattern 2 found:', pattern2 in content)
print('Pattern 3 found:', pattern3 in content)