from pathlib import Path
import tempfile
import zipfile
import xml.etree.ElementTree as ET

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    source_epub = tmp_path / "source_with_image.epub"
    
    fixture_path = Path("tests/contract/fixtures/test_image.png")
    image_bytes = fixture_path.read_bytes()
    
    with zipfile.ZipFile(source_epub, 'w') as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        container = ET.Element("container", version="1.0", xmlns="urn:oasis:names:tc:opendocument:xmlns:container")
        rootfiles = ET.SubElement(container, "rootfiles")
        rootfile = ET.SubElement(rootfiles, "rootfile", media_type="application/oebps-package+xml")
        rootfile.set("full-path", "OEBPS/content.opf")
        z.writestr("META-INF/container.xml", ET.tostring(container, encoding="unicode"))
        opf = ET.Element("package", xmlns="http://www.idpf.org/2007/opf", unique_identifier="bookid", version="3.0")
        metadata = ET.SubElement(opf, "metadata", xmlns_dc="http://purl.org/dc/elements/1.1/")
        ET.SubElement(metadata, "dc:identifier", id="bookid").text = "test-book"
        ET.SubElement(metadata, "dc:title").text = "Test Book"
        ET.SubElement(metadata, "dc:language").text = "ko"
        manifest = ET.SubElement(opf, "manifest")
        ET.SubElement(manifest, "item", id="nav", href="nav.xhtml", media_type="application/xhtml+xml", properties="nav")
        ET.SubElement(manifest, "item", id="ch1", href="chapter1.xhtml", media_type="application/xhtml+xml")
        ET.SubElement(manifest, "item", id="ch2", href="chapter2.xhtml", media_type="application/xhtml+xml")
        ET.SubElement(manifest, "item", id="ch3", href="chapter3.xhtml", media_type="application/xhtml+xml")
        ET.SubElement(manifest, "item", id="css", href="style.css", media_type="text/css")
        ET.SubElement(manifest, "item", id="img1", href="images/test_image.png", media_type="image/png")
        spine = ET.SubElement(opf, "spine")
        ET.SubElement(spine, "itemref", idref="nav")
        ET.SubElement(spine, "itemref", idref="ch1")
        ET.SubElement(spine, "itemref", idref="ch2")
        ET.SubElement(spine, "itemref", idref="ch3")
        z.writestr("OEBPS/content.opf", ET.tostring(opf, encoding="unicode"))
        nav = ET.Element("html", xmlns="http://www.w3.org/1999/xhtml", xmlns_epub="http://www.idpf.org/2007/ops")
        head = ET.SubElement(nav, "head")
        ET.SubElement(head, "title").text = "Navigation"
        body = ET.SubElement(nav, "body")
        nav_elem = ET.SubElement(body, "nav", epub_type="toc")
        ol = ET.SubElement(nav_elem, "ol")
        for i in range(1, 4):
            li = ET.SubElement(ol, "li")
            ET.SubElement(li, "a", href=f"chapter{i}.xhtml").text = f"Chapter {i}"
        z.writestr("OEBPS/nav.xhtml", ET.tostring(nav, encoding="unicode"))
        for i in range(1, 4):
            ch = ET.Element("html", xmlns="http://www.w3.org/1999/xhtml", xmlns_epub="http://www.idpf.org/2007/ops")
            head = ET.SubElement(ch, "head")
            ET.SubElement(head, "title").text = f"Chapter {i}"
            body = ET.SubElement(ch, "body")
            ET.SubElement(body, "p").text = f"Chapter {i} content"
            z.writestr(f"OEBPS/chapter{i}.xhtml", ET.tostring(ch, encoding="unicode"))
        z.writestr("OEBPS/style.css", "body { font-family: serif; }")
        z.writestr("OEBPS/images/test_image.png", image_bytes)
    
    # Read and print the OPF
    with zipfile.ZipFile(source_epub, 'r') as z:
        opf_content = z.read("OEBPS/content.opf").decode("utf-8")
        print("OPF content:")
        print(opf_content)
        print()
        print("=== Parsing with validation function ===")
        import xml.etree.ElementTree as ET2
        opf_root = ET2.fromstring(opf_content)
        ns = {"opf": "http://www.idpf.org/2007/opf"}
        manifest = opf_root.find(".//opf:manifest", ns)
        if manifest is not None:
            print("Manifest found!")
            for item in manifest.findall("opf:item", ns):
                print(f"  Item: {item.attrib}")
        else:
            print("Manifest NOT found!")
            # Try without namespace
            manifest2 = opf_root.find(".//manifest")
            if manifest2 is not None:
                print("Found manifest without namespace")
                for item in manifest2.findall("item"):
                    print(f"  Item: {item.attrib}")
            else:
                print("Manifest not found even without namespace")
                # Print all elements
                for elem in opf_root.iter():
                    print(f"  {elem.tag}: {elem.attrib}")