# -*- coding: utf-8 -*-
# Read the file
with open("D:\\Python\\NTPE\\core\\epub_translation\\runtime\\epub_packager.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the position after the first _get_archive_paths function
idx = content.find("def _get_archive_paths(namelist: list[str]) -> set[str]:")
if idx >= 0:
    # Find the end of the first _get_archive_paths function (next function definition)
    next_func = content.find("\ndef ", content.find("def _get_archive_paths(namelist: list[str]) -> set[str]:") + 1)
    if next_func > 0:
        new_func = '''

def _extract_epub_resources(epub_path: Path) -> ExtractedEpubResources:
    """Extract resources from source EPUB for re-embedding.

    Returns ExtractedEpubResources with all binary resources and manifest info.
    """
    manifest_items = []  # (id, href, media_type)
    resource_bytes = {}
    spine_order = []
    nav_href = None
    opf_path = None
    container_rootfile_path = None

    with zipfile.ZipFile(epub_path, "r") as z:
        # Read container.xml to find OPF path
        if "META-INF/container.xml" in z.namelist():
            container_xml = z.read("META-INF/container.xml").decode("utf-8")
            import xml.etree.ElementTree as ET
            root = ET.fromstring(container_xml)
            ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//container:rootfile", ns)
            if rootfile is not None:
                container_rootfile_path = rootfile.get("full-path")
                opf_path = container_rootfile_path

        # Read OPF to get manifest and spine
        if opf_path and opf_path in z.namelist():
            opf_content = z.read(opf_path).decode("utf-8")
            import xml.etree.ElementTree as ET
            opf_root = ET.fromstring(opf_content)
            ns = {"opf": "http://www.idpf.org/2007/opf"}

            # Parse manifest
            manifest = opf_root.find(".//opf:manifest", ns)
            if manifest is not None:
                for item in manifest.findall("opf:item", ns):
                    item_id = item.get("id", "")
                    href = item.get("href", "")
                    media_type = item.get("media-type", "")
                    if item_id and href:
                        manifest_items.append((item_id, href, media_type))
                        # Read resource bytes
                        opf_dir = str(Path(opf_path).parent)
                        resource_path = f"{opf_dir}/{href}" if opf_dir != "." else href
                        if resource_path in z.namelist():
                            resource_bytes[href] = z.read(resource_path)
                        elif href in z.namelist():
                            resource_bytes[href] = z.read(href)

            # Parse spine
            spine = opf_root.find(".//opf:spine", ns)
            if spine is not None:
                for itemref in spine.findall("opf:itemref", ns):
                    idref = itemref.get("idref", "")
                    if idref:
                        spine_order.append(idref)

            # Find nav href
            for item_id, href, media_type in manifest_items:
                if media_type == "application/xhtml+xml" and "nav" in href.lower():
                    nav_href = href
                    break

    return ExtractedEpubResources(
        manifest_items=tuple(manifest_items),
        resource_bytes=MappingProxyType(resource_bytes),
        spine_order=tuple(spine_order),
        nav_href=nav_href,
        opf_path=opf_path or "",
        container_rootfile_path=container_rootfile_path or "",
    )


'''

        new_content = content[:next_func] + new_func + content[next_func:]
        with open("D:\\Python\\NTPE\\core\\epub_translation\\runtime\\epub_packager.py", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Added _extract_epub_resources function")
    else:
        print("Could not find insertion point")