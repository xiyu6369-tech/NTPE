from core.epub_translation.runtime.epub_packager import _extract_epub_resources
from pathlib import Path
import tempfile
import zipfile
import xml.etree.ElementTree as ET

with tempfile.TemporaryDirectory() as tmp:
    source_epub = Path(tmp) / "source_with_image.epub"
    
    fixture_path = Path("tests/contract/fixtures/test_image.png")
    image_bytes = fixture_path.read_bytes()
    
    with zipfile.ZipFile(source_epub, 'w') as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        container = ET.Element("container", version="1.0", xmlns="urn:oasis:names:tc:opendocument:xmlns:container")
        rootfiles = ET.SubElement(container, "rootfiles")
        ET.SubElement(rootfiles, "rootfile", full_path="OEBPS/content.opf", media_type="application/oebps-package+xml")
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
    
    # Debug step by step
    with zipfile.ZipFile(source_epub, 'r') as z:
        namelist = z.namelist()
        print("Namelist:", namelist)
        
        if "META-INF/container.xml" in namelist:
            container_xml = z.read("META-INF/container.xml").decode("utf-8")
            print("Container XML:", container_xml)
            root = ET.fromstring(container_xml)
            ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//container:rootfile", ns)
            if rootfile is not None:
                opf_path = rootfile.get("full-path")
                print("OPF path from container:", opf_path)
                print("OPF path in namelist:", opf_path in z.namelist())
                
                if opf_path in z.namelist():
                    opf_content = z.read(opf_path).decode("utf-8")
                    print("OPF content:", opf_content[:500])
                    opf_root = ET.fromstring(opf_content)
                    ns_opf = {"opf": "http://www.idpf.org/2007/opf"}
                    manifest = opf_root.find(".//opf:manifest", ns_opf)
                    if manifest is not None:
                        print("Manifest found!")
                        for item in manifest.findall("opf:item", ns_opf):
                            item_id = item.get("id", "")
                            href = item.get("href", "")
                            media_type = item.get("media-type", "")
                            print(f"  Item: id={item_id}, href={href}, media_type={media_type}")
                            # Check resource path
                            opf_dir = str(Path(opf_path).parent)
                            resource_path = f"{opf_dir}/{href}" if opf_dir != "." else href
                            print(f"  Resource path: {resource_path}")
                            print(f"  In namelist: {resource_path in z.namelist()}")
                    else:
                        print("Manifest not found!")