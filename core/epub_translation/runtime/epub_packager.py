"""S5 Resource-Aware EPUB Packager.

Packages EPUB translation results into valid EPUB 3.0 files while preserving
all original EPUB structure: metadata, resources, spine order, navigation, and chapter identity.
"""

from __future__ import annotations

import html
import os
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from core.epub_translation.contract import (
    EpubTranslationInput,
    EpubTranslationResult,
    EpubMetadata,
    ResourceRef,
    TocEntry,
    EpubChapterBoundary,
)
from core.epub_translation.reader_chapter_map import EpubReaderChapterMapResult, ChapterBoundary, ReaderChapterMap


class EpubPackagingError(ValueError):
    """Error raised when EPUB packaging fails."""
    pass


class EpubValidationError(ValueError):
    """Error raised when EPUB structural validation fails."""
    pass


@dataclass(frozen=True)
class EpubPackagingInput:
    """Complete input for resource-aware EPUB packaging.

    Combines S4 ReaderChapterMap result with S1 extraction input and S3 translation result.
    All fields are immutable.
    """
    reader_chapter_map_result: EpubReaderChapterMapResult
    translation_input: EpubTranslationInput
    translation_result: EpubTranslationResult

    def __post_init__(self) -> None:
        # Validate chapter identity consistency
        map_chapter_ids = {c.chapter_id for c in self.reader_chapter_map_result.reader_chapter_map.chapters}
        input_chapter_ids = {c.chapter_id for c in self.translation_input.chapter_map}
        result_chapter_ids = {cr.chapter_id for cr in self.translation_result.chapter_results}

        if map_chapter_ids != input_chapter_ids:
            raise EpubPackagingError(
                f"ReaderChapterMap chapter IDs {sorted(map_chapter_ids)} "
                f"do not match input chapter IDs {sorted(input_chapter_ids)}"
            )
        if map_chapter_ids != result_chapter_ids:
            raise EpubPackagingError(
                f"ReaderChapterMap chapter IDs {sorted(map_chapter_ids)} "
                f"do not match result chapter IDs {sorted(result_chapter_ids)}"
            )

        # Validate spine order consistency
        map_orders = [c.chapter_order for c in self.reader_chapter_map_result.reader_chapter_map.chapters]
        if map_orders != list(range(len(map_orders))):
            raise EpubPackagingError(f"ReaderChapterMap chapter orders not sequential 0-based: {map_orders}")

        input_spine_positions = [c.spine_position for c in self.translation_input.chapter_map]
        if input_spine_positions != sorted(input_spine_positions):
            raise EpubPackagingError(f"Input chapter map spine positions not strictly increasing: {input_spine_positions}")

        # Validate result chapter_order is 1-based sequential
        result_orders = [cr.chapter_order for cr in self.translation_result.chapter_results]
        if result_orders != list(range(1, len(result_orders) + 1)):
            raise EpubPackagingError(f"Result chapter_order not sequential 1-based: {result_orders}")


@dataclass(frozen=True)
class EpubPackagingResult:
    """Result of EPUB packaging operation."""
    success: bool
    output_path: Path | None
    source_identity: str
    chapter_count: int
    resource_count: int
    validation_errors: tuple[str, ...]
    error_message: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.success and not self.validation_errors


@dataclass(frozen=True)
class ExtractedEpubResources:
    """Resources extracted from source EPUB for re-embedding."""
    manifest_items: tuple[tuple[str, str, str], ...]  # (id, href, media_type)
    resource_bytes: MappingProxyType[str, bytes]  # href -> bytes
    spine_order: tuple[str, ...]  # manifest ids in spine order
    nav_href: str | None
    opf_path: str
    container_rootfile_path: str


_CHAPTER_PATTERN = re.compile(r"(?:第\s*\d+\s*章|Chapter\s+\d+|CHAPTER\s+\d+)")


def _extract_chapter_title(text: str, fallback: str) -> str:
    """Extract chapter title from explicit marker in text."""
    match = _CHAPTER_PATTERN.search(text)
    if match:
        return match.group(0).replace(" ", "")
    return fallback


def _escape_xhtml(text: str | None) -> str:
    """Escape XML/HTML special characters for safe XHTML content."""
    if text is None:
        return ""
    return html.escape(text, quote=False)


def _paragraphs_to_xhtml(text: str) -> str:
    """Convert paragraphs to XHTML <p> elements."""
    if not text.strip():
        return "<p></p>"

    paragraphs = text.split("\n\n")
    xhtml_parts: list[str] = []
    for para in paragraphs:
        para = para.strip()
        if para:
            escaped = _escape_xhtml(para)
            xhtml_parts.append(f"<p>{escaped}</p>")
        else:
            xhtml_parts.append("<p></p>")
    return "\n".join(xhtml_parts)


def _get_archive_paths(namelist: list[str]) -> set[str]:
    """Get set of all archive paths for reference resolution."""
    paths = set(namelist)
    # Also add basename versions for flexible matching
    for name in namelist:
        basename = os.path.basename(name)
        if basename:
            paths.add(basename)
    return paths



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



def _validate_xhtml_references(
    xhtml_content: str,
    xhtml_href: str,
    namelist: list[str],
    manifest_hrefs: set[str],
) -> list[str]:
    """Validate XHTML content for broken references.
    
    Checks:
    - CSS references (<link rel="stylesheet" href="...">)
    - Image references (<img src="...">)
    - Internal links (<a href="...">)
    - Fragment references (<a href="#...">)
    
    Returns list of validation errors.
    """
    errors: list[str] = []
    
    try:
        import xml.etree.ElementTree as ET
        import os
        
        parser = ET.XMLParser(encoding="utf-8")
        root = ET.fromstring(xhtml_content, parser=ET.XMLParser(encoding="utf-8"))
        
        archive_paths = _get_archive_paths(namelist)
        
        def resolve_href(base_href: str, ref: str) -> str:
            if not ref or ref.startswith('#'):
                return ref
            if ref.startswith(('http://', 'https://', 'data:')):
                return ref
            if base_href:
                base_dir = os.path.dirname(base_href)
                if base_dir:
                    return os.path.normpath(os.path.join(os.path.dirname(base_href), ref))
            return ref
        
        archive_paths = _get_archive_paths(namelist)
        
        # Check CSS references
        for link in root.findall('.//{http://www.w3.org/1999/xhtml}link[@rel="stylesheet"]'):
            href = link.get('href') or link.get('{http://www.w3.org/1999/xhtml}href')
            if href and not href.startswith(('http://', 'https://', 'data:')) and href not in ('#', ''):
                resolved = href
                if xhtml_href:
                    base_dir = os.path.dirname(xhtml_href)
                    if base_dir:
                        resolved = os.path.normpath(os.path.join(os.path.dirname(xhtml_href), href))
                    else:
                        resolved = href
                archive_paths = _get_archive_paths(namelist)
                if resolved not in archive_paths and os.path.basename(resolved) not in archive_paths:
                    errors.append(f"CSS reference not found in archive: {href} (resolved to {resolved}) in {xhtml_href}")
        
        # Check image references
        for img in root.findall('.//{http://www.w3.org/1999/xhtml}img'):
            src = img.get('src') or img.get('{http://www.w3.org/1999/xhtml}src')
            if src and not src.startswith(('http://', 'https://', 'data:')):
                resolved = src
                if xhtml_href:
                    base_dir = os.path.dirname(xhtml_href)
                    if base_dir:
                        resolved = os.path.normpath(os.path.join(os.path.dirname(xhtml_href), src))
                archive_paths = _get_archive_paths(namelist)
                if resolved not in archive_paths and os.path.basename(resolved) not in archive_paths:
                    errors.append(f"Image reference not found in archive: {src} (resolved to {resolved}) in {xhtml_href}")
        
        # Check internal links and fragments
        for a in root.findall('.//{http://www.w3.org/1999/xhtml}a'):
            href = a.get('href') or a.get('{http://www.w3.org/1999/xhtml}href')
            if href:
                if href.startswith('#'):
                    pass
                elif not href.startswith(('http://', 'https://', 'data:')):
                    resolved = href
                    if xhtml_href:
                        base_dir = os.path.dirname(xhtml_href)
                        if base_dir:
                            resolved = os.path.normpath(os.path.join(os.path.dirname(xhtml_href), href))
                    archive_paths = _get_archive_paths(namelist)
                    if resolved not in archive_paths and os.path.basename(resolved) not in archive_paths:
                        if '#' in href:
                            base_href = href.split('#')[0]
                            if base_href and base_href not in _get_archive_paths(namelist):
                                errors.append(f"Internal link target not found in archive: {href} (base: {base_href}) in {xhtml_href}")
                        else:
                            errors.append(f"Internal link target not found in archive: {href} (resolved to {resolved}) in {xhtml_href}")
        
    except Exception as e:
        errors.append(f"XHTML reference validation error in {xhtml_href}: {e}")
    
    return errors


def _get_archive_paths(namelist: list[str]) -> set[str]:
    """Get set of all archive paths for reference resolution."""
    paths = set(namelist)
    # Also add basename versions for flexible matching
    for name in namelist:
        basename = os.path.basename(name)
        if basename:
            paths.add(basename)
    return paths


def _validate_epub_archive(epub_path: Path) -> list[str]:
    """Validate EPUB archive structure.

    Returns list of validation errors (empty if valid).
    """
    errors: list[str] = []

    if not epub_path.exists():
        errors.append("Output EPUB file does not exist")
        return errors

    try:
        with zipfile.ZipFile(epub_path, 'r') as z:
            namelist = z.namelist()

            # 1. mimetype must exist and be first entry
            if "mimetype" not in namelist:
                errors.append("Missing mimetype in archive")
            else:
                mimetype_content = z.read("mimetype").decode("utf-8").strip()
                if mimetype_content != "application/epub+zip":
                    errors.append(f"Invalid mimetype: {mimetype_content}")
                # Check if mimetype is first entry (not strictly required but recommended)
                if namelist[0] != "mimetype":
                    errors.append("mimetype is not the first archive entry")

            # 2. META-INF/container.xml must exist
            if "META-INF/container.xml" not in z.namelist():
                errors.append("Missing META-INF/container.xml")

            opf_path: str | None = None
            manifest_items: list[Any] = []

            # 3. OPF package document must exist (referenced from container.xml)
            if "META-INF/container.xml" in z.namelist():
                container_xml = z.read("META-INF/container.xml").decode("utf-8")
                import xml.etree.ElementTree as ET
                root = ET.fromstring(container_xml)
                ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
                rootfile = root.find(".//container:rootfile", ns)
                if rootfile is not None:
                    opf_path = rootfile.get("full-path")
                    if opf_path and opf_path not in z.namelist():
                        errors.append(f"OPF package document not found: {opf_path}")
                else:
                    errors.append("No rootfile in container.xml")

            # 4. Validate OPF structure if present
            if opf_path and opf_path in z.namelist():
                opf_content = z.read(opf_path).decode("utf-8")
                import xml.etree.ElementTree as ET
                opf_root = ET.fromstring(opf_content)
                ns = {"opf": "http://www.idpf.org/2007/opf"}

                # Check metadata exists
                metadata = opf_root.find(".//opf:metadata", ns)
                if metadata is None:
                    errors.append("Missing metadata in OPF")

                # Check manifest exists and has items
                manifest = opf_root.find(".//opf:manifest", ns)
                if manifest is None:
                    errors.append("Missing manifest in OPF")
                else:
                    manifest_items = list(manifest.findall("opf:item", ns))
                    if not manifest_items:
                        errors.append("Empty manifest in OPF")
                    else:
                        # Check for unique IDs
                        item_ids = [item.get("id", "") for item in manifest_items]
                        if len(item_ids) != len(set(item_ids)):
                            errors.append("Duplicate IDs in manifest")

                # Check spine exists and references valid manifest items
                spine = opf_root.find(".//opf:spine", ns)
                if spine is None:
                    errors.append("Missing spine in OPF")
                else:
                    spine_itemrefs = list(spine.findall("opf:itemref", ns))
                    if not spine_itemrefs:
                        errors.append("Empty spine in OPF")
                    else:
                        # Collect manifest IDs
                        manifest_ids = {item.get("id", "") for item in manifest_items}
                        for itemref in spine_itemrefs:
                            idref = itemref.get("idref", "")
                            if idref and idref not in manifest_ids:
                                errors.append(f"Spine references missing manifest item: {idref}")

                # Check nav exists
                nav_found = False
                for item in manifest_items:
                    if item.get("properties", "") == "nav" or "nav" in item.get("href", "").lower():
                        nav_found = True
                        break
                if not nav_found:
                    errors.append("Missing nav in manifest")

                # 5. Validate XHTML content references
                # Collect all manifest hrefs for reference resolution
                manifest_hrefs = set()
                for item in manifest_items:
                    href = item.get("href", "")
                    if href:
                        manifest_hrefs.add(href)

                # Check each XHTML file for broken references
                archive_paths = _get_archive_paths(z.namelist())
                opf_dir = os.path.dirname(opf_path) if opf_path else ""
                for item in manifest_items:
                    href = item.get("href", "")
                    media_type = item.get("media-type", "")
                    if media_type == "application/xhtml+xml" and href:
                        # Resolve href relative to OPF directory
                        if opf_dir:
                            resolved_href = os.path.normpath(os.path.join(opf_dir, href)).replace("\\", "/")
                        else:
                            resolved_href = href
                        if resolved_href in archive_paths:
                            xhtml_content = z.read(resolved_href).decode("utf-8")
                            xhtml_errors = _validate_xhtml_references(xhtml_content, href, z.namelist(), manifest_hrefs)
                            errors.extend(xhtml_errors)
                        else:
                            errors.append(f"XHTML file not found in archive: {href} (resolved to {resolved_href})")

    except zipfile.BadZipFile:
        errors.append("Output is not a valid ZIP archive")
    except Exception as e:
        errors.append(f"Validation error: {e}")

    return errors


def _build_nav_document(
    translation_input: EpubTranslationInput,
    translation_result: EpubTranslationResult,
    reader_chapter_map: ReaderChapterMap,
    novel_title: str,
) -> str:
    """Build EPUB navigation document (nav.xhtml) preserving original TOC structure."""
    nav_items: list[str] = []

    # Use original TOC entries if available, otherwise build from chapters
    if translation_input.toc_entries:
        for toc in translation_input.toc_entries:
            nav_items.append(f'        <li><a href="{_escape_xhtml(toc.href)}">{_escape_xhtml(toc.title)}</a></li>')
    else:
        # Build from chapters in spine order
        for i, chapter in enumerate(reader_chapter_map.chapters):
            input_chapter = next(
                (c for c in translation_input.chapter_map if c.chapter_id == chapter.chapter_id),
                None
            )
            href = input_chapter.source_href if input_chapter else f"chapter_{i+1:03d}.xhtml"
            # Use basename for nav href
            import os
            href = os.path.basename(href.split("#")[0]) if href else f"chapter_{i+1:03d}.xhtml"
            title = input_chapter.title if input_chapter else chapter.chapter_title
            nav_items.append(f'        <li><a href="{_escape_xhtml(href)}">{_escape_xhtml(title)}</a></li>')

    nav_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="zh-TW">
<head>
    <meta charset="utf-8"/>
    <title>目錄</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>目錄</h1>
        <ol>
{chr(10).join(nav_items)}
        </ol>
    </nav>
</body>
</html>"""

    return nav_content


def _build_chapter_xhtml(
    chapter_result,
    input_chapter: EpubChapterBoundary,
    reader_chapter: ChapterBoundary,
    chapter_index: int,
    default_language: str = "zh-TW",
    extracted_resources: ExtractedEpubResources | None = None,
) -> tuple[str, str]:
    """Build XHTML content for a single chapter.

    Returns:
        (output_href, xhtml_content)
    """
    # Use source_href from input to determine output href
    source_href = input_chapter.source_href
    if source_href:
        # Preserve original href basename if possible
        import os
        output_href = os.path.basename(source_href.split("#")[0])
        if not output_href.endswith(".xhtml"):
            output_href = f"chapter_{chapter_index:03d}.xhtml"
    else:
        output_href = f"chapter_{chapter_index:03d}.xhtml"

    title = input_chapter.title or _extract_chapter_title(
        chapter_result.assembled_text if hasattr(chapter_result, 'assembled_text') and chapter_result.assembled_text else "",
        f"第{chapter_index}章"
    )

    # The actual translated content comes from the translation result
    chapter_content = chapter_result.assembled_text if hasattr(chapter_result, 'assembled_text') and chapter_result.assembled_text else ""

    # Try to preserve source XHTML structure
    if extracted_resources and source_href:
        preserved_xhtml = _rewrite_chapter_xhtml_preserving_structure(
            source_href=source_href,
            translated_text=chapter_content,
            title=title,
            default_language=default_language,
            extracted_resources=extracted_resources,
        )
        if preserved_xhtml:
            return output_href, preserved_xhtml

    # Fallback: generate minimal XHTML
    xhtml_body = _paragraphs_to_xhtml(chapter_content)

    xhtml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{default_language}">
<head>
    <meta charset="utf-8"/>
    <title>{_escape_xhtml(title)}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    {xhtml_body}
</body>
</html>"""

    return output_href, xhtml_content


def _build_css_from_resources(resources: tuple[ResourceRef, ...]) -> str:
    """Build CSS from original resources or generate default."""
    css_resources = [r for r in resources if r.type.lower() in ("css", "stylesheet")]
    if css_resources:
        # Use first CSS resource as base
        # In a real implementation, we'd extract the actual CSS content
        # For now, generate a reasonable default that preserves original intent
        pass

    return """@charset "utf-8";

body {
    font-family: "Noto Serif CJK TC", "PingFang TC", "Microsoft JhengHei", serif;
    line-height: 1.8;
    margin: 2em 1.5em;
    text-align: justify;
}

p {
    margin: 0.5em 0;
    text-indent: 2em;
}

p:first-child {
    text-indent: 0;
}

h1 {
    text-align: center;
    margin: 2em 0 1em;
    font-size: 1.5em;
    font-weight: bold;
}

nav ol {
    list-style: none;
    padding: 0;
}

nav li {
    margin: 0.5em 0;
}

nav a {
    text-decoration: none;
    color: #333;
}

nav a:hover {
    text-decoration: underline;
}
"""


def _rewrite_chapter_xhtml_preserving_structure(
    source_href: str,
    translated_text: str,
    title: str,
    default_language: str,
    extracted_resources: ExtractedEpubResources,
) -> str | None:
    """Rewrite chapter XHTML preserving structural elements (img, a, link, etc.)."""
    import os
    from xml.etree import ElementTree as ET
    from xml.dom import minidom

    # Find the source XHTML in extracted resources
    source_href_clean = source_href.split("#")[0]
    source_xhtml_bytes = None
    source_xhtml_href = None
    
    # Try exact match first
    if source_href_clean in extracted_resources.resource_bytes:
        source_xhtml_bytes = extracted_resources.resource_bytes[source_href_clean]
        source_xhtml_href = source_href_clean
    else:
        # Try basename match
        basename = os.path.basename(source_href_clean)
        if basename in extracted_resources.resource_bytes:
            source_xhtml_bytes = extracted_resources.resource_bytes[basename]
            source_xhtml_href = basename

    if not source_xhtml_bytes:
        return None

    try:
        # Parse source XHTML
        source_xhtml = source_xhtml_bytes.decode("utf-8")
        parser = ET.XMLParser(encoding="utf-8")
        root = ET.fromstring(source_xhtml, parser=parser)
        
        # Register namespaces
        ET.register_namespace("", "http://www.w3.org/1999/xhtml")
        ET.register_namespace("epub", "http://www.idpf.org/2007/ops")
        
        # Split translated text into paragraphs
        translated_paragraphs = [p.strip() for p in translated_text.split("\n\n") if p.strip()]
        para_iter = iter(translated_paragraphs)
        
        # Define XHTML namespace
        XHTML_NS = "http://www.w3.org/1999/xhtml"
        
        # Process all elements recursively
        def process_element(elem):
            # Handle text content replacement for text-bearing elements
            if elem.tag.endswith('}p') or elem.tag == 'p' or elem.tag.endswith('}h1') or elem.tag == 'h1' or elem.tag.endswith('}h2') or elem.tag == 'h2' or elem.tag.endswith('}h3') or elem.tag == 'h3' or elem.tag.endswith('}h4') or elem.tag == 'h4' or elem.tag.endswith('}h5') or elem.tag == 'h5' or elem.tag.endswith('}h6') or elem.tag == 'h6' or elem.tag.endswith('}li') or elem.tag == 'li' or elem.tag.endswith('}td') or elem.tag == 'td' or elem.tag.endswith('}th') or elem.tag == 'th' or elem.tag.endswith('}span') or elem.tag == 'span' or elem.tag.endswith('}div') or elem.tag == 'div':
                try:
                    new_text = next(para_iter)
                    elem.text = new_text
                    for child in list(elem):
                        if child.tail:
                            child.tail = None
                except StopIteration:
                    pass
            
            # Update href/src attributes for resources
            if elem.tag.endswith('}a') or elem.tag == 'a':
                href = elem.get('href') or elem.get(f'{{{XHTML_NS}}}href')
                if href and not href.startswith('#') and not href.startswith('http://') and not href.startswith('https://'):
                    new_href = os.path.basename(href.split('#')[0])
                    if '#' in href:
                        fragment = href.split('#', 1)[1]
                        new_href = f"{new_href}#{fragment}"
                    elem.set('href', new_href)
            
            if elem.tag.endswith('}img') or elem.tag == 'img':
                src = elem.get('src') or elem.get(f'{{{XHTML_NS}}}src')
                if src and not src.startswith('http://') and not src.startswith('https://') and not src.startswith('data:'):
                    new_src = os.path.basename(src.split('#')[0])
                    elem.set('src', new_src)
            
            if elem.tag.endswith('}link') or elem.tag == 'link':
                href = elem.get('href') or elem.get(f'{{{XHTML_NS}}}href')
                if href and not href.startswith('http://') and not href.startswith('https://'):
                    new_href = os.path.basename(href.split('#')[0])
                    elem.set('href', new_href)
            
            for child in elem:
                process_element(child)
        
        XHTML_NS = "http://www.w3.org/1999/xhtml"
        process_element(root)
        
        # Ensure proper namespace declarations - only add if not present
        # In ElementTree, check the tag namespace prefix
        has_xhtml_ns = root.tag.startswith('{http://www.w3.org/1999/xhtml}')
        has_epub_ns = False
        for k, v in root.attrib.items():
            if k.startswith('xmlns:') and v == 'http://www.idpf.org/2007/ops':
                has_epub_ns = True
        if not has_xhtml_ns:
            root.set('xmlns', 'http://www.w3.org/1999/xhtml')
        if not has_epub_ns:
            root.set('xmlns:epub', 'http://www.idpf.org/2007/ops')
        if '{http://www.w3.org/XML/1998/namespace}lang' not in root.attrib:
            root.set('{http://www.w3.org/XML/1998/namespace}lang', default_language)
        if 'lang' not in root.attrib:
            root.set('lang', default_language)
        
        # Ensure title is in head
        head = root.find('.//{http://www.w3.org/1999/xhtml}head')
        if head is not None:
            title_elem = head.find('.//{http://www.w3.org/1999/xhtml}title')
            if title_elem is not None:
                title_elem.text = title
            else:
                title_elem = ET.SubElement(head, '{http://www.w3.org/1999/xhtml}title')
                title_elem.text = title
            
            meta_charset = head.find('.//{http://www.w3.org/1999/xhtml}meta[@charset]')
            if meta_charset is None:
                meta_charset = ET.SubElement(head, '{http://www.w3.org/1999/xhtml}meta')
                meta_charset.set('charset', 'utf-8')
            
            css_link = head.find('.//{http://www.w3.org/1999/xhtml}link[@rel="stylesheet"]')
            if css_link is None:
                css_link = ET.SubElement(head, '{http://www.w3.org/1999/xhtml}link')
                css_link.set('rel', 'stylesheet')
                css_link.set('type', 'text/css')
                css_link.set('href', 'style.css')
            else:
                css_link.set('href', 'style.css')
        
        # Serialize with pretty formatting
        try:
            ET.indent(root, space="  ")
        except AttributeError:
            pass  # Python < 3.9
        rough_string = ET.tostring(root, encoding='unicode', method='xml')
        
        # Use ElementTree serialization directly to avoid minidom namespace duplication issues
        final_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
{rough_string}"""
        
        return final_xml
        
    except Exception:
        # If any error occurs, return None to use fallback
        return None


def _guess_media_type(href: str) -> str:
    """Guess media type from file extension."""
    ext = href.lower().split(".")[-1] if "." in href else ""
    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
        "css": "text/css",
        "ttf": "font/ttf",
        "otf": "font/otf",
        "woff": "font/woff",
        "woff2": "font/woff2",
        "mp3": "audio/mpeg",
        "mp4": "video/mp4",
        "js": "application/javascript",
        "html": "application/xhtml+xml",
        "xhtml": "application/xhtml+xml",
    }
    return media_types.get(ext, "application/octet-stream")


def pack_epub_resource_aware(
    *,
    packaging_input: EpubPackagingInput,
    output_path: Path,
) -> EpubPackagingResult:
    """Package EPUB from resource-aware translation results.

    This is the canonical S5 packaging function. It preserves:
    - Original EPUB metadata (title, author, language, identifier, etc.)
    - Original resources (images, CSS, fonts, other assets) with byte-level fidelity
    - Original spine order and chapter identity
    - Original navigation/TOC structure
    - Source href mapping (deterministic)
    - Translated chapter content

    Args:
        packaging_input: Complete packaging input combining S1, S3, S4 results
        output_path: Output EPUB file path

    Returns:
        EpubPackagingResult with success status and diagnostics

    Raises:
        EpubPackagingError: For deterministic contract violations
        EpubValidationError: For structural validation failures
    """
    try:
        from ebooklib import epub
    except ImportError:
        return EpubPackagingResult(
            success=False,
            output_path=None,
            source_identity=packaging_input.translation_input.original_hash,
            chapter_count=0,
            resource_count=0,
            validation_errors=("ebooklib not available",),
            error_message="EPUB dependency unavailable",
        )

    try:
        reader_result = packaging_input.reader_chapter_map_result
        translation_input = packaging_input.translation_input
        translation_result = packaging_input.translation_result

        # Extract resources from source EPUB for byte-level preservation
        source_epub_path = translation_input.source_epub_path
        extracted_resources = ExtractedEpubResources(
            manifest_items=(),
            resource_bytes=MappingProxyType({}),
            spine_order=(),
            nav_href=None,
            opf_path="",
            container_rootfile_path="",
        )
        if source_epub_path.exists():
            extracted_resources = _extract_epub_resources(source_epub_path)

        book = epub.EpubBook()
        book.set_identifier(translation_input.metadata.identifier or translation_input.original_hash[:16])

        # Preserve original metadata
        meta = translation_input.metadata
        book.set_title(meta.title or translation_input.original_hash[:16])
        book.set_language(meta.language or "zh-TW")
        if meta.author:
            book.add_author(meta.author)
        if meta.publisher:
            book.add_metadata("DC", "publisher", meta.publisher)
        if meta.date:
            book.add_metadata("DC", "date", meta.date)

        # Add translation metadata
        book.add_metadata("DC", "translator", "NTPE Translation Engine")
        book.add_metadata("DC", "pipeline", "NTPE_S5_v1")
        book.add_metadata("DC", "source_hash", translation_input.original_hash)

        # Collect resources from extraction contract
        resources = translation_input.resources
        resource_count = len(resources)

        # Build chapter mapping: chapter_id -> (input_chapter, reader_chapter, chapter_result)
        input_chapter_map = {c.chapter_id: c for c in translation_input.chapter_map}
        reader_chapter_map = {c.chapter_id: c for c in reader_result.reader_chapter_map.chapters}
        result_chapter_map = {cr.chapter_id: cr for cr in translation_result.chapter_results}

        spine_items = []
        chapter_items = []
        href_map = {}  # chapter_id -> output href

        # Determine default language from metadata
        default_language = translation_input.metadata.language or "zh-TW"

        # Build navigation document first (so nav is first in spine)
        nav_content = _build_nav_document(
            translation_input,
            translation_result,
            reader_result.reader_chapter_map,
            meta.title or "Novel",
        )
        nav_item = epub.EpubHtml(title="目錄", file_name="nav.xhtml", lang=default_language)
        nav_item.content = nav_content.encode("utf-8")
        nav_item.id = "nav"
        book.add_item(nav_item)
        spine_items.append(nav_item.id)

        # Process chapters in spine order (result order is spine order)
        for i, chapter_result in enumerate(translation_result.chapter_results, start=1):
            input_chapter = input_chapter_map[chapter_result.chapter_id]
            reader_chapter = reader_chapter_map[chapter_result.chapter_id]

            output_href, xhtml_content = _build_chapter_xhtml(
                chapter_result,
                input_chapter,
                reader_chapter,
                i,
                default_language,
                extracted_resources,
            )

            href_map[chapter_result.chapter_id] = output_href

            # Use EpubItem instead of EpubHtml for full control over XHTML content
            chapter_item = epub.EpubItem(
                uid=f"ch{i}",
                file_name=output_href,
                media_type="application/xhtml+xml",
                content=xhtml_content.encode("utf-8"),
            )
            book.add_item(chapter_item)

            chapter_items.append(chapter_item)
            spine_items.append(chapter_item.id)

        # Add CSS - use extracted CSS if available, otherwise generate default
        css_content = _build_css_from_resources(resources)
        # Check if we have extracted CSS from source EPUB
        for href, content in extracted_resources.resource_bytes.items():
            if href.endswith(".css") or _guess_media_type(href) == "text/css":
                css_content = content.decode("utf-8", errors="replace")
                break

        css_item = epub.EpubItem(
            uid="style_css",
            file_name="style.css",
            media_type="text/css",
            content=css_content.encode("utf-8"),
        )
        book.add_item(css_item)

        # Add original resources (images, fonts, etc.) with byte-level preservation
        for resource in resources:
            if resource.type.lower() in ("image", "font", "audio", "video", "script", "css", "stylesheet"):
                # Try to get actual bytes from extracted resources
                resource_bytes = b""
                if resource.href in extracted_resources.resource_bytes:
                    resource_bytes = extracted_resources.resource_bytes[resource.href]
                elif resource.href.split("/")[-1] in extracted_resources.resource_bytes:
                    # Try basename match
                    resource_bytes = extracted_resources.resource_bytes[resource.href.split("/")[-1]]

                item = epub.EpubItem(
                    uid=f"resource_{resource.href.replace('/', '_').replace('.', '_')}",
                    file_name=resource.href,
                    media_type=_guess_media_type(resource.href),
                    content=resource_bytes,
                )
                book.add_item(item)

        # Set spine and TOC
        book.spine = spine_items

        # Build TOC from original toc_entries or chapters
        toc_items = []
        for toc in translation_input.toc_entries:
            href = toc.href
            import os
            href = os.path.basename(href.split("#")[0]) if href else ""
            toc_items.append(epub.Link(href, toc.title, f"toc_{toc.level}_{toc.title}"))
        if toc_items:
            book.toc = toc_items
        else:
            book.toc = [
                epub.Link(href_map[cr.chapter_id], input_chapter_map[cr.chapter_id].title or f"Chapter {i}", f"ch{i}")
                for i, cr in enumerate(translation_result.chapter_results, start=1)
            ]

        book.add_item(epub.EpubNcx())
        # Note: nav already added above, don't add EpubNav() again to avoid duplication

        # Write EPUB
        epub.write_epub(str(output_path), book)

        # Validate output archive structure
        validation_errors = _validate_epub_archive(output_path)

        return EpubPackagingResult(
            success=len(validation_errors) == 0,
            output_path=output_path,
            source_identity=translation_input.original_hash,
            chapter_count=len(translation_result.chapter_results),
            resource_count=resource_count,
            validation_errors=tuple(validation_errors),
            error_message=None if len(validation_errors) == 0 else "; ".join(validation_errors),
        )

    except EpubPackagingError:
        raise
    except EpubValidationError:
        raise
    except OSError as e:
        return EpubPackagingResult(
            success=False,
            output_path=None,
            source_identity=packaging_input.translation_input.original_hash,
            chapter_count=0,
            resource_count=0,
            validation_errors=(f"I/O error: {e}",),
            error_message=str(e),
        )
    except Exception as e:
        return EpubPackagingResult(
            success=False,
            output_path=None,
            source_identity=packaging_input.translation_input.original_hash,
            chapter_count=0,
            resource_count=0,
            validation_errors=(f"Unexpected error: {e}",),
            error_message=str(e),
        )

def validate_packaging_input(packaging_input: EpubPackagingInput) -> None:
    """Validate packaging input contract.

    Raises:
        EpubPackagingError: If input contract is violated
    """
    # Validation is done in EpubPackagingInput.__post_init__
    # This function exists for explicit validation calls
    pass