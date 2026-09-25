import re

with open("D:\\Python\\NTPE\\tests\\contract\\test_s5b_epub_structure.py", "r", encoding="utf-8") as f:
    content = f.read()

old_pattern = r'class TestS5BB23InvalidSpineFailure:.*?assert any\("missing manifest item" in e\.lower\(\) for e in errors\)'
new_code = '''class TestS5BB23InvalidSpineFailure:
    """B23 — Invalid spine causes failure."""

    def test_invalid_spine_validation(self, output_path: Path) -> None:
        """_validate_epub_archive catches invalid spine."""
        import zipfile
        
        bad_epub = output_path.parent / "bad.epub"
        with zipfile.ZipFile(bad_epub, 'w') as z:
            z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
            # Create container.xml with correct full-path attribute (hyphen)
            container_xml = '''<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'''
            z.writestr("META-INF/container.xml", container_xml)
            
            # Create OPF with proper namespace declarations
            opf_content = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">test</dc:identifier>
    <dc:title>Test</dc:title>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="nonexistent"/>
  </spine>
</package>'''
            z.writestr("content.opf", opf_content)
            z.writestr("nav.xhtml", "<html></html>")
            z.writestr("ch1.xhtml", "<html></html>")
        
        errors = _validate_epub_archive(bad_epub)
        assert any("missing manifest item" in e.lower() for e in errors)'''

# Find and replace
pattern = r'class TestS5BB23InvalidSpineFailure:.*?assert any\("missing manifest item" in e\.lower\(\) for e in errors\)'
content = re.sub(pattern, new_code, content, flags=re.DOTALL)

with open("D:\\Python\\NTPE\\tests\\contract\\test_s5b_epub_structure.py", "w", encoding="utf-8") as f:
    f.write(content)
    
print("Fixed!")