with open('tests/contract/test_s5c_reference_integrity.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('ch1 = ET.Element("html", xmlns="http://www.w3.org/1999/xhtml", xmlns_epub="http://www.idpf.org/2007/ops")')
if idx >= 0:
    start = max(0, idx - 200)
    end = min(len(content), idx + 500)
    print(repr(content[start:end]))
else:
    print('Not found')

# Also check for the from import line
idx2 = content.find('from core.epub_translation.runtime.epub_packager import _validate_epub_archive')
if idx2 >= 0:
    print('Found import at:', idx2)
    start = max(0, idx2 - 100)
    end = min(len(content), idx2 + 200)
    print(repr(content[start:end]))
else:
    print('Import not found')