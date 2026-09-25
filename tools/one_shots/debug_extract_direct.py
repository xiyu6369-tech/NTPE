from core.epub_translation.runtime.epub_packager import _extract_epub_resources
from pathlib import Path
import tempfile
import zipfile
import xml.etree.ElementTree as ET

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    source_epub = tmp_path / "source_simple.epub"
    
    with zipfile.ZipFile(source_epub, 'w') as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        container = ET.Element("container", version="1.0", xmlns="urn:oasis:names:tc:opendocument:xmlns:container")
        rootfiles = ET.SubElement(container, "rootfiles")
        rootfile = ET.SubElement(rootfiles, "rootfile", media_type="application/oebps-package+xml")
        rootfile.set("full-path", "OEBPS/content.opf")
        z.writestr("META-INF/container.xml", ET.tostring(container, encoding="unicode"))
        opf = ET.Element("package")
        opf.set("xmlns", "http://www.idpf.org/2007/opf")
        opf.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
        opf.set("unique-identifier", "bookid")
        opf.set("version", "3.0")
        metadata = ET.SubElement(opf, "metadata")
        ET.SubElement(metadata, "{http://purl.org/dc/elements/1.1/}identifier", id="bookid").text = "test-book"
        ET.SubElement(metadata, "{http://purl.org/dc/elements/1.1/}title").text = "Test Book"
        ET.SubElement(metadata, "{http://purl.org/dc/elements/1.1/}language").text = "ko"
        manifest = ET.SubElement(opf, "manifest")
        ET.SubElement(manifest, "item", id="nav", href="nav.xhtml", media_type="application/xhtml+xml", properties="nav")
        ET.SubElement(manifest, "item", id="ch1", href="chapter1.xhtml", media_type="application/xhtml+xml")
        ET.SubElement(manifest, "item", id="ch2", href="chapter2.xhtml", media_type="application/xhtml+xml")
        ET.SubElement(manifest, "item", id="ch3", href="chapter3.xhtml", media_type="application/xhtml+xml")
        ET.SubElement(manifest, "item", id="css", href="style.css", media_type="text/css")
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
    
    # Test extraction
    extracted = _extract_epub_resources(source_epub)
    print("Manifest items:", extracted.manifest_items)
    print("Resource bytes keys:", list(extracted.resource_bytes.keys()))
    for k, v in extracted.resource_bytes.items():
        print(f"  {k}: {len(v)} bytes")
    print("Spine order:", extracted.spine_order)
    print("Nav href:", extracted.nav_href)
    print("OPF path:", extracted.opf_path)
    print("Container rootfile path:", extracted.container_rootfile_path)