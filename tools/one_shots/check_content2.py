with open('tests/contract/test_s5c_reference_integrity.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check specific patterns
patterns = [
    'z.writestr("OEBPS/nav.xhtml", ET.tostring(nav, encoding="unicode"))',
    '            \n            ch1 = ET.Element',
    'from core.epub_translation.runtime.epub_packager import _validate_epub_archive\nerrors = _validate_epub_archive(broken_epub)\n# Should detect the broken reference\nassert len(errors) > 0'
]

for pattern in patterns:
    if pattern in content:
        print('FOUND: ' + pattern[:50] + '...')
    else:
        print('NOT FOUND: ' + pattern[:50] + '...')