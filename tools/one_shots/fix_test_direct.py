# Read the file
with open("D:\\Python\\NTPE\\tests\\contract\\test_s5b_epub_structure.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the test function and replace it
new_lines = []
i = 0
in_test = False
test_indent = None
while i < len(lines):
    line = lines[i]
    if "def test_invalid_spine_validation" in line:
        in_test = True
        test_indent = len(line) - len(line.lstrip())
        # Skip until we find the end of the function
        # Write the new implementation
        new_lines.append(line)  # def line
        i += 1
        # Skip old implementation lines until we hit the next test class or function at same indent
        while i < len(lines):
            if lines[i].strip() and not lines[i].startswith(" " * (test_indent + 4)) and not lines[i].startswith("\t" * (test_indent // 4 + 1)):
                # This line is at or less indent than the def, so we're done
                break
            i += 1
        # Now insert new implementation
        new_impl = [
            '        """_validate_epub_archive catches invalid spine."""\n',
            '        import zipfile\n',
            '        \n',
            '        bad_epub = output_path.parent / "bad.epub"\n',
            '        with zipfile.ZipFile(bad_epub, \'w\') as z:\n',
            '            z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)\n',
            '            # Create container.xml with correct full-path attribute (hyphen)\n',
            '            container_xml = \'<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>\'\n',
            '            z.writestr("META-INF/container.xml", container_xml)\n',
            '            \n',
            '            # Create OPF with proper namespace declarations\n',
            '            opf_content = \'<?xml version="1.0" encoding="UTF-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">\n  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n    <dc:identifier id="bookid">test</dc:identifier>\n    <dc:title>Test</dc:title>\n    <dc:language>en</dc:language>\n  </metadata>\n  <manifest>\n    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>\n    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>\n  </manifest>\n  <spine>\n    <itemref idref="nonexistent"/>\n  </spine>\n</package>\'\n',
            '            z.writestr("content.opf", opf_content)\n',
            '            z.writestr("nav.xhtml", "<html></html>")\n',
            '            z.writestr("ch1.xhtml", "<html></html>")\n',
            '        \n',
            '        errors = _validate_epub_archive(bad_epub)\n',
            '        assert any("missing manifest item" in e.lower() for e in errors)\n',
        ]
        new_lines.extend(new_impl)
        in_test = False
        test_indent = None
        continue
    new_lines.append(line)
    i += 1

with open("D:\\Python\\NTPE\\tests\\contract\\test_s5b_epub_structure.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Fixed!")