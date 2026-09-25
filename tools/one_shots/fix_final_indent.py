with open('tests/contract/test_s5c_reference_integrity.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: After z.writestr("OEBPS/chapter01.xhtml"...) there should be proper blank line and method-level code
# Find the pattern and fix
content = content.replace(
    'z.writestr("OEBPS/chapter01.xhtml", ET.tostring(ch1, encoding="unicode"))\n        \n        # Verify validation catches this\n        from core.epub_translation.runtime.epub_packager import _validate_epub_archive\nerrors = _validate_epub_archive(broken_epub)\n# Should detect the broken reference\nassert len(errors) > 0',
    'z.writestr("OEBPS/chapter01.xhtml", ET.tostring(ch1, encoding="unicode"))\n        \n        # Verify validation catches this\n        from core.epub_translation.runtime.epub_packager import _validate_epub_archive\n        errors = _validate_epub_archive(broken_epub)\n        # Should detect the broken reference\n        assert len(errors) > 0'
)

with open('tests/contract/test_s5c_reference_integrity.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed!")