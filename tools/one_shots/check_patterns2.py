with open('tests/contract/test_s5c_reference_integrity.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check patterns
print('Pattern 1:', 'z.writestr("OEBPS/nav.xhtml", ET.tostring(nav, encoding="unicode"))' in content)
print('Pattern 2:', '            \n            ch1 = ET.Element' in content)
print('Pattern 3:', 'from core.epub_translation.runtime.epub_packager import _validate_epub_archive\nerrors = _validate_epub_archive(broken_epub)\n# Should detect the broken reference\nassert len(errors) > 0' in content)