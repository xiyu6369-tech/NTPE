with open('tests/contract/test_s5c_reference_integrity.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Line 632 - z.writestr at 0 indent -> 12 spaces
content = content.replace(
    'z.writestr("OEBPS/nav.xhtml", ET.tostring(nav, encoding="unicode"))',
    '            z.writestr("OEBPS/nav.xhtml", ET.tostring(nav, encoding="unicode"))'
)

# Fix 2: Line 633 - empty line with 13 spaces -> 12
content = content.replace(
    '            \n            ch1 = ET.Element',
    '            \n            ch1 = ET.Element'
)

# Fix 3: Lines 642-645 (from core.epub_translation... to assert) - move from module level to method level (8 spaces)
content = content.replace(
    'from core.epub_translation.runtime.epub_packager import _validate_epub_archive\nerrors = _validate_epub_archive(broken_epub)\n# Should detect the broken reference\nassert len(errors) > 0',
    '        from core.epub_translation.runtime.epub_packager import _validate_epub_archive\n        errors = _validate_epub_archive(broken_epub)\n        # Should detect the broken reference\n        assert len(errors) > 0'
)

with open('tests/contract/test_s5c_reference_integrity.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed!")