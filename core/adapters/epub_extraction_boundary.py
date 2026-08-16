from __future__ import annotations

import hashlib
import posixpath
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from types import MappingProxyType

try:
    from lxml import etree, html
except ImportError:
    etree = None
    html = None


@dataclass(frozen=True)
class EpubMetadata:
    title: str | None
    author: str | None
    language: str | None
    identifier: str | None
    publisher: str | None
    date: str | None
    raw: MappingProxyType[str, Any]


@dataclass(frozen=True)
class ChapterBoundary:
    index: int
    spine_position: int
    title: str | None
    start_offset: int
    end_offset: int
    source_href: str | None
    toc_level: int = 0
    is_linear: bool = True
    word_count: int = 0
    landmark_type: str | None = None
    status: str = "linear"


@dataclass(frozen=True)
class ResourceRef:
    type: str
    href: str
    chapter_index: int | None
    metadata: MappingProxyType[str, Any]


@dataclass(frozen=True)
class ExtractionManifest:
    extractor_version: str
    extracted_at: str
    chapter_count: int
    total_characters: int
    total_words: int
    warnings: tuple[str, ...]
    resources: tuple[ResourceRef, ...]
    spine_item_count: int
    nav_toc_entries: int
    encoding_used: str
    parsing_duration_ms: int
    fixed_layout: MappingProxyType[str, Any] | None = None


@dataclass(frozen=True)
class EpubExtractionResult:
    source_path: Path
    original_hash: str
    extracted_text: str
    extracted_hash: str
    metadata: EpubMetadata
    chapter_map: tuple[ChapterBoundary, ...]
    extraction_manifest: ExtractionManifest
    status: str
    warnings: tuple[str, ...]


class EpubExtractionError(Exception):
    def __init__(self, message: str, blocked: bool = False, warnings: tuple[str, ...] = ()):
        self.blocked = blocked
        self.warnings = warnings
        super().__init__(message)


@dataclass(frozen=True)
class ExtractedTextIntakeRequest:
    source_path: Path
    source_format: str
    extracted_text: str
    original_file_hash: str
    extracted_text_hash: str
    epub_metadata: dict[str, Any]
    chapter_map: tuple[ChapterBoundary, ...]
    extraction_manifest: ExtractionManifest
    extractor_version: str


# Module-level constants
_MAX_ARCHIVE_SIZE = 500 * 1024 * 1024
_MAX_ENTRY_COUNT = 10000
_MAX_COMPRESSION_RATIO = 100
_EXECUTABLE_EXTENSIONS = {".exe", ".dll", ".so", ".sh", ".bat", ".ps1"}
_NESTED_ARCHIVE_EXTENSIONS = {".zip", ".epub", ".jar", ".war", ".ear"}
_NESTED_ARCHIVE_SIGNATURES = [b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"]
_EXTRACTOR_VERSION = "epub-extraction-v1.0.0"


class EpubExtractionBoundary:
    def __init__(self):
        self.extractor_version = _EXTRACTOR_VERSION

    def extract(self, epub_path: Path) -> EpubExtractionResult:
        start_time = datetime.now(timezone.utc)
        warnings: list[str] = []

        if not epub_path.exists():
            raise EpubExtractionError(f"EPUB file not found: {epub_path}", blocked=True)

        original_bytes = epub_path.read_bytes()
        original_hash = hashlib.sha256(original_bytes).hexdigest()

        with zipfile.ZipFile(epub_path, "r") as zf:
            self._validate_zip_security(zf, warnings)

            container_xml = self._read_container_xml(zf)
            opf_path = self._parse_container_xml(container_xml)

            try:
                opf_content = zf.read(opf_path).decode("utf-8")
            except KeyError:
                raise EpubExtractionError(f"OPF file not found: {opf_path}", blocked=True)

            opf_root = etree.fromstring(opf_content.encode("utf-8"))

            manifest_items = self._parse_manifest(opf_root)
            spine_items = self._parse_spine(opf_root)

            if not spine_items:
                raise EpubExtractionError("Empty spine - no spine items", blocked=True)

            metadata = self._parse_metadata(opf_root, warnings)

            nav_toc, nav_landmarks, nav_warnings = self._parse_nav(zf, manifest_items, opf_path)
            warnings.extend(nav_warnings)

            ncx_toc, ncx_warnings = self._parse_ncx(zf, manifest_items, opf_path)
            warnings.extend(ncx_warnings)

            toc_map = self._build_toc_map(nav_toc, ncx_toc, spine_items, manifest_items)

            fixed_layout_info = self._detect_fixed_layout(opf_root, zf, manifest_items, spine_items)
            if fixed_layout_info:
                warnings.append("Fixed-layout EPUB detected; viewport metadata recorded in manifest")

            linear_items, supplementary_items = self._partition_spine_items(spine_items)

            # Check for all supplementary spine items
            if not linear_items and supplementary_items:
                warnings.append("all spine items linear=no")

            extracted_parts: list[str] = []
            chapter_map: list[ChapterBoundary] = []
            resources: list[ResourceRef] = []
            current_offset = 0
            chapter_index = 0

            opf_dir = posixpath.dirname(opf_path) if opf_path else ""

            all_spine_items = linear_items + supplementary_items

            for item in all_spine_items:
                chapter_index += 1
                is_linear = item in linear_items
                status = "linear" if is_linear else "supplementary"

                # Resolve href from manifest
                item_id = item["idref"]
                manifest_item = manifest_items.get(item_id, {})
                href = manifest_item.get("href", "")
                full_href = posixpath.normpath(posixpath.join(opf_dir, href)) if opf_dir else href

                chapter_text, chapter_resources, chapter_warnings, extracted_title = self._extract_chapter(
                    zf, item, manifest_items, chapter_index, toc_map, opf_dir
                )
                warnings.extend(chapter_warnings)
                resources.extend(chapter_resources)

                # Use extracted title if available, otherwise fall back to TOC/generated
                title = extracted_title or self._resolve_chapter_title_fallback(
                    item, toc_map, chapter_index
                )

                marker = f"=== CHAPTER {chapter_index}: {title or 'Untitled'} ===\n"
                full_chapter_text = marker + chapter_text + "\n"

                start_offset = current_offset
                end_offset = current_offset + len(full_chapter_text)

                word_count = len(chapter_text.split())

                chapter_boundary = ChapterBoundary(
                    index=chapter_index,
                    spine_position=item["spine_position"],
                    title=title,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    source_href=full_href,
                    toc_level=toc_map.get(href, {}).get("level", 0),
                    is_linear=is_linear,
                    word_count=word_count,
                    landmark_type=toc_map.get(href, {}).get("landmark"),
                    status=status,
                )
                chapter_map.append(chapter_boundary)
                extracted_parts.append(full_chapter_text)
                current_offset = end_offset

            extracted_text = "".join(extracted_parts)
            extracted_text = extracted_text.replace("\r\n", "\n").replace("\r", "\n")
            extracted_hash = hashlib.sha256(extracted_text.encode("utf-8")).hexdigest()

            resources = self._deduplicate_and_sort_resources(resources)
            manifest = self._build_manifest(
                chapter_count=len(chapter_map),
                total_characters=len(extracted_text),
                total_words=sum(cb.word_count for cb in chapter_map),
                warnings=tuple(warnings),
                resources=tuple(resources),
                spine_item_count=len(linear_items),
                nav_toc_entries=len(nav_toc) + len(ncx_toc),
                encoding_used="utf-8",
                parsing_duration_ms=int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000),
                fixed_layout=fixed_layout_info,
            )

            status = self._determine_status(warnings)

            return EpubExtractionResult(
                source_path=epub_path,
                original_hash=original_hash,
                extracted_text=extracted_text,
                extracted_hash=extracted_hash,
                metadata=metadata,
                chapter_map=tuple(chapter_map),
                extraction_manifest=manifest,
                status=status,
                warnings=tuple(warnings),
            )

    def validate_epub(self, epub_path: Path) -> tuple[bool, str | None]:
        if not epub_path.exists():
            return False, f"EPUB file not found: {epub_path}"
        if epub_path.suffix.lower() != ".epub":
            return False, f"File is not an EPUB: {epub_path}"
        try:
            with zipfile.ZipFile(epub_path, "r") as zf:
                self._validate_zip_security(zf, [])
                if "META-INF/container.xml" not in zf.namelist():
                    return False, "Missing META-INF/container.xml"
            return True, None
        except zipfile.BadZipFile:
            return False, "Invalid ZIP file"
        except EpubExtractionError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {e}"

    def _validate_zip_security(self, zf: zipfile.ZipFile, warnings: list[str]) -> None:
        if len(zf.namelist()) > _MAX_ENTRY_COUNT:
            raise EpubExtractionError(f"Entry count exceeds maximum ({_MAX_ENTRY_COUNT})", blocked=True)

        total_uncompressed = sum(info.file_size for info in zf.infolist())
        if total_uncompressed > _MAX_ARCHIVE_SIZE:
            raise EpubExtractionError(f"Uncompressed size exceeds maximum ({_MAX_ARCHIVE_SIZE} bytes)", blocked=True)

        canonical_paths: set[str] = set()

        for info in zf.infolist():
            name = info.filename

            if name.endswith("/"):
                continue

            parts = name.split("/")
            if ".." in parts:
                raise EpubExtractionError(f"Path traversal detected: {name}", blocked=True)

            if name.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", name) or name.startswith("\\\\"):
                raise EpubExtractionError(f"Absolute/UNC/drive-letter path detected: {name}", blocked=True)

            if getattr(info, "is_symlink", lambda: False)():
                raise EpubExtractionError(f"Symlink entry detected: {name}", blocked=True)

            normalized = posixpath.normpath(name).lower()
            if normalized in canonical_paths:
                raise EpubExtractionError(f"Duplicate canonical path: {normalized}", blocked=True)
            canonical_paths.add(normalized)

            ext = posixpath.splitext(name)[1].lower()
            if ext in _EXECUTABLE_EXTENSIONS:
                raise EpubExtractionError(f"Executable archive member: {name}", blocked=True)

            if ext in _NESTED_ARCHIVE_EXTENSIONS:
                try:
                    with zf.open(info) as f:
                        header = f.read(4)
                        if any(header.startswith(sig) for sig in _NESTED_ARCHIVE_SIGNATURES):
                            raise EpubExtractionError(f"Nested archive detected: {name}", blocked=True)
                except EpubExtractionError:
                    raise
                except Exception:
                    pass

            if info.compress_size > 0 and info.file_size > 0:
                ratio = info.file_size / info.compress_size
                if ratio > _MAX_COMPRESSION_RATIO:
                    raise EpubExtractionError(f"Zip bomb detected (ratio {ratio:.1f}:1): {name}", blocked=True)

        if "META-INF/encryption.xml" in zf.namelist():
            raise EpubExtractionError("Encrypted container (encryption.xml present)", blocked=True)

        if "META-INF/signatures.xml" in zf.namelist():
            warnings.append("Signatures.xml present; ignored")

    def _read_container_xml(self, zf: zipfile.ZipFile) -> bytes:
        try:
            return zf.read("META-INF/container.xml")
        except KeyError:
            raise EpubExtractionError("Missing META-INF/container.xml", blocked=True)

    def _parse_container_xml(self, container_xml: bytes) -> str:
        root = etree.fromstring(container_xml)
        ns = {"ocf": "urn:oasis:names:tc:opendocument:xmlns:container"}
        rootfiles = root.xpath("//ocf:rootfile", namespaces=ns)
        if not rootfiles:
            raise EpubExtractionError("No rootfile in container.xml", blocked=True)
        return rootfiles[0].get("full-path", "")

    def _parse_manifest(self, opf_root: etree._Element) -> dict[str, dict[str, Any]]:
        ns = {"opf": "http://www.idpf.org/2007/opf"}
        items = {}
        for item in opf_root.xpath("//opf:manifest/opf:item", namespaces=ns):
            item_id = item.get("id")
            href = item.get("href")
            media_type = item.get("media-type")
            properties = item.get("properties", "")
            if item_id and href:
                items[item_id] = {"href": href, "media_type": media_type, "properties": properties}
        return items

    def _parse_spine(self, opf_root: etree._Element) -> list[dict[str, Any]]:
        ns = {"opf": "http://www.idpf.org/2007/opf"}
        spine_items = []
        position = 0
        for itemref in opf_root.xpath("//opf:spine/opf:itemref", namespaces=ns):
            position += 1
            idref = itemref.get("idref")
            linear = itemref.get("linear", "yes")
            spine_items.append({
                "idref": idref,
                "linear": linear,
                "spine_position": position,
            })
        return spine_items

    def _parse_metadata(self, opf_root: etree._Element, warnings: list[str]) -> EpubMetadata:
        ns = {
            "opf": "http://www.idpf.org/2007/opf",
            "dc": "http://purl.org/dc/elements/1.1/",
        }
        raw_meta: dict[str, Any] = {}

        def get_dc(tag: str) -> str | None:
            elems = opf_root.xpath(f"//opf:metadata/dc:{tag}", namespaces=ns)
            if elems:
                return elems[0].text or ""
            return None

        for elem in opf_root.xpath("//opf:metadata/*", namespaces=ns):
            tag = etree.QName(elem).localname
            ns_uri = etree.QName(elem).namespace
            key = f"{ns_uri}:{tag}" if ns_uri else tag
            raw_meta[key] = elem.text or ""

        return EpubMetadata(
            title=get_dc("title"),
            author=get_dc("creator"),
            language=get_dc("language"),
            identifier=get_dc("identifier"),
            publisher=get_dc("publisher"),
            date=get_dc("date"),
            raw=MappingProxyType(raw_meta),
        )

    def _parse_nav(
        self, zf: zipfile.ZipFile, manifest_items: dict[str, dict[str, Any]], opf_path: str
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
        warnings: list[str] = []
        nav_items = [item for item in manifest_items.values() if "nav" in item.get("properties", "")]
        if not nav_items:
            return [], [], warnings

        nav_href = nav_items[0]["href"]
        opf_dir = posixpath.dirname(opf_path)
        nav_full_path = posixpath.join(opf_dir, nav_href) if opf_dir else nav_href

        try:
            nav_content_bytes = zf.read(nav_full_path)
        except KeyError:
            warnings.append(f"Nav document not found: {nav_full_path}")
            return [], [], warnings

        ns = {"xhtml": "http://www.w3.org/1999/xhtml", "epub": "http://www.idpf.org/2007/ops"}
        nav_root = etree.fromstring(nav_content_bytes)
        toc_entries: list[dict[str, Any]] = []
        landmarks: list[dict[str, Any]] = []

        for nav in nav_root.xpath("//xhtml:nav[@epub:type='toc']", namespaces=ns):
            self._parse_nav_ol(nav, toc_entries, level=0, ns=ns)

        for nav in nav_root.xpath("//xhtml:nav[@epub:type='landmarks']", namespaces=ns):
            for li in nav.xpath(".//xhtml:li/xhtml:a", namespaces=ns):
                href = li.get("href", "")
                epub_type = li.get("{http://www.idpf.org/2007/ops}type", "")
                landmarks.append({"href": href, "type": epub_type})

        return toc_entries, landmarks, warnings

    def _parse_nav_ol(
        self, ol: etree._Element, entries: list[dict[str, Any]], level: int, ns: dict[str, str]
    ) -> None:
        for li in ol.xpath("./xhtml:li", namespaces=ns):
            a = li.xpath("./xhtml:a", namespaces=ns)
            if a:
                href = a[0].get("href", "")
                title = "".join(a[0].itertext()).strip()
                entries.append({"href": href, "title": title, "level": level})
            nested_ol = li.xpath("./xhtml:ol", namespaces=ns)
            if nested_ol:
                self._parse_nav_ol(nested_ol[0], entries, level + 1, ns)

    def _parse_ncx(
        self, zf: zipfile.ZipFile, manifest_items: dict[str, dict[str, Any]], opf_path: str
    ) -> tuple[list[dict[str, Any]], list[str]]:
        warnings: list[str] = []
        ncx_items = [
            item for item in manifest_items.values()
            if item.get("media_type") == "application/x-dtbncx+xml"
        ]
        if not ncx_items:
            return [], warnings

        ncx_href = ncx_items[0]["href"]
        opf_dir = posixpath.dirname(opf_path)
        ncx_full_path = posixpath.join(opf_dir, ncx_href) if opf_dir else ncx_href

        try:
            ncx_content = zf.read(ncx_full_path).decode("utf-8")
        except KeyError:
            warnings.append(f"NCX document not found: {ncx_full_path}")
            return [], warnings

        ncx_root = etree.fromstring(ncx_content.encode("utf-8"))
        ns = {"ncx": "http://www.daisy.org/z3986/2005/ncx/"}

        toc_entries: list[dict[str, Any]] = []

        def parse_navpoint(np: etree._Element, level: int) -> None:
            content = np.xpath("./ncx:content", namespaces=ns)
            text = np.xpath("./ncx:navLabel/ncx:text", namespaces=ns)
            if content and text:
                href = content[0].get("src", "")
                title = text[0].text or ""
                toc_entries.append({"href": href, "title": title, "level": level})
            for child in np.xpath("./ncx:navPoint", namespaces=ns):
                parse_navpoint(child, level + 1)

        for np in ncx_root.xpath("//ncx:navMap/ncx:navPoint", namespaces=ns):
            parse_navpoint(np, 0)

        return toc_entries, warnings

    def _build_toc_map(
        self,
        nav_toc: list[dict[str, Any]],
        ncx_toc: list[dict[str, Any]],
        spine_items: list[dict[str, Any]],
        manifest_items: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        toc_map: dict[str, dict[str, Any]] = {}

        all_toc = nav_toc + ncx_toc

        for entry in all_toc:
            href = entry["href"]
            base_href = href.split("#")[0]
            if base_href not in toc_map:
                toc_map[base_href] = {"title": entry["title"], "level": entry["level"]}

        for item in spine_items:
            item_id = item["idref"]
            if item_id in manifest_items:
                pass

        return toc_map

    def _detect_fixed_layout(
        self,
        opf_root: etree._Element,
        zf: zipfile.ZipFile,
        manifest_items: dict[str, dict[str, Any]],
        spine_items: list[dict[str, Any]],
    ) -> MappingProxyType[str, Any] | None:
        ns = {
            "opf": "http://www.idpf.org/2007/opf",
            "rendition": "http://www.idpf.org/vocab/rendition/#",
        }

        layout = opf_root.xpath("//opf:metadata/opf:meta[@property='rendition:layout']", namespaces=ns)
        layout_content = (layout[0].get("content") or layout[0].text or "").strip() if layout else ""
        if not layout or layout_content != "pre-paginated":
            return None

        def get_meta_content(metas):
            """Get content from meta element - check both content attribute and text."""
            if not metas:
                return None
            meta = metas[0]
            return (meta.get("content") or meta.text or "").strip()

        viewport_meta = opf_root.xpath("//opf:metadata/opf:meta[@property='rendition:viewport']", namespaces=ns)
        spread_meta = opf_root.xpath("//opf:metadata/opf:meta[@property='rendition:spread']", namespaces=ns)
        orientation_meta = opf_root.xpath("//opf:metadata/opf:meta[@property='rendition:orientation']", namespaces=ns)
        page_prog = opf_root.xpath("//opf:spine/@page-progression-direction", namespaces=ns)

        viewport = {"width": 1200, "height": 1600, "orientation": "portrait"}
        viewport_content = get_meta_content(viewport_meta)
        if viewport_content:
            for part in viewport_content.split(","):
                part = part.strip()
                if part.startswith("width="):
                    try:
                        viewport["width"] = int(part.split("=")[1])
                    except ValueError:
                        pass
                elif part.startswith("height="):
                    try:
                        viewport["height"] = int(part.split("=")[1])
                    except ValueError:
                        pass
                elif part in ("portrait", "landscape"):
                    viewport["orientation"] = part

        fixed_layout = {
            "viewport": viewport,
            "spread": get_meta_content(spread_meta) or "auto",
            "orientation": get_meta_content(orientation_meta) or "auto",
            "page_progression_direction": page_prog[0] if page_prog else "ltr",
        }

        return MappingProxyType(fixed_layout)

    def _partition_spine_items(
        self, spine_items: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        linear = [item for item in spine_items if item.get("linear", "yes") == "yes"]
        supplementary = [item for item in spine_items if item.get("linear", "yes") == "no"]
        return linear, supplementary

    def _extract_chapter(
        self,
        zf: zipfile.ZipFile,
        spine_item: dict[str, Any],
        manifest_items: dict[str, dict[str, Any]],
        chapter_index: int,
        toc_map: dict[str, dict[str, Any]],
        opf_dir: str = "",
    ) -> tuple[str, list[ResourceRef], list[str], str | None]:
        import re
        from collections import Counter
        warnings: list[str] = []
        resources: list[ResourceRef] = []

        item_id = spine_item["idref"]
        if item_id not in manifest_items:
            warnings.append(f"Spine item {item_id} not found in manifest")
            return "", resources, warnings, None

        item = manifest_items[item_id]
        href = item["href"]
        media_type = item.get("media_type", "")

        if not href or not media_type or "xhtml" not in media_type and "html" not in media_type:
            warnings.append(f"Non-XHTML spine item skipped: {href} ({media_type})")
            return "", resources, warnings, None

        # Resolve href relative to OPF directory
        full_href = posixpath.normpath(posixpath.join(opf_dir, href)) if opf_dir else href

        try:
            content_bytes = zf.read(full_href)
        except KeyError:
            warnings.append(f"Spine item content not found: {full_href}")
            return "", resources, warnings, None

        # Detect encoding from XML declaration first (for UTF-16 support)
        detected_encoding = self._detect_encoding(content_bytes)
        try:
            content = content_bytes.decode(detected_encoding)
        except UnicodeDecodeError:
            content = content_bytes.decode("utf-8", errors="replace")
            warnings.append(f"Encoding fallback for {href}")

        # Strip XML declaration and xmlns to avoid namespace issues
        content = re.sub(r'<\?xml[^>]*\?>', '', content)
        content = re.sub(r'\s+xmlns:?[a-zA-Z0-9_]*="[^"]*"', '', content)
        content = re.sub(r"\s+xmlns:?[a-zA-Z0-9_]*='[^']*'", '', content)

        # Escape bare & characters to prevent XML parser from treating them as malformed entities
        # This preserves & characters that are not part of valid entities
        content_bytes = self._escape_bare_ampersands(content_bytes)

        # Use HTML parser for better entity handling and recovery
        # HTML parser handles entities (including numeric refs) and recovers from malformed markup
        try:
            from lxml import html
            doc = html.fromstring(content_bytes, parser=html.HTMLParser(recover=True, encoding=detected_encoding))
        except Exception as e:
            warnings.append(f"Parse error in {full_href}: {e}")
            return "", resources, warnings, None

        # Find body element handling namespaces (XHTML body is in http://www.w3.org/1999/xhtml namespace)
        body = None
        for elem in doc.iter():
            if elem.tag.endswith("}body") or elem.tag == "body":
                body = elem
                break
        if body is None:
            body = doc

        # Extract title from the document before stripping elements
        title = self._extract_title_from_doc(doc)

        # Collect resources from full document (including head)
        self._collect_resources(doc, href, chapter_index, resources, warnings)
        # Strip scripts from full document
        self._strip_scripts(doc, warnings)
        # Remove unwanted elements from body
        if body is not doc:
            self._remove_unwanted_elements(body)

        # Use XML tree for text extraction (preserves entities as text, handles malformed XML)
        text = self._extract_text_from_xml_tree(body if body is not None else doc)
        # Decode HTML entities in the extracted text (single pass, no double decoding)
        text = self._decode_html_entities(text)
        text = self._normalize_text(text)

        # Check for malformed content - detect unclosed tags
        # Simple heuristic: count opening vs closing tags in original content
        import re
        from collections import Counter
        opening_tags = re.findall(rb'<([a-zA-Z][a-zA-Z0-9]*)[^>]*>', content_bytes)
        closing_tags = re.findall(rb'</([a-zA-Z][a-zA-Z0-9]*)>', content_bytes)
        # Filter out self-closing tags
        self_closing = {b'br', b'img', b'hr', b'meta', b'link', b'input', b'col', b'area', b'base', b'param', b'source', b'track', b'wbr'}
        opening_filtered = [t for t in opening_tags if t.lower() not in self_closing]
        closing_filtered = [t.lower() for t in closing_tags]
        opening_filtered = [t.lower() for t in opening_filtered]
        opening_counts = Counter(opening_filtered)
        closing_counts = Counter(closing_filtered)
        for tag, count in opening_counts.items():
            if count > closing_counts.get(tag, 0):
                tag_str = tag.decode() if isinstance(tag, bytes) else tag
                warnings.append(f"Malformed XHTML detected: unclosed <{tag_str}> tag")
                break

        return text, resources, warnings, title

    def _detect_encoding(self, content_bytes: bytes) -> str:
        if content_bytes.startswith(b"\xef\xbb\xbf"):
            return "utf-8-sig"
        if content_bytes.startswith(b"\xff\xfe") or content_bytes.startswith(b"\xfe\xff"):
            return "utf-16"
        # Check for UTF-16 without BOM first (alternating null bytes pattern)
        # UTF-16LE: char, 0x00, char, 0x00...
        if len(content_bytes) >= 4 and content_bytes[1] == 0 and content_bytes[3] == 0:
            try:
                decoded = content_bytes[:1024].decode("utf-16-le")
                if 'encoding="' in decoded or "charset=" in decoded:
                    import re
                    m = re.search(r'encoding=["\']([^"\']+)', decoded)
                    if m:
                        return m.group(1)
                    m = re.search(r'charset=["\']?([^"\'\s>]+)', decoded)
                    if m:
                        return m.group(1)
                return "utf-16-le"
            except UnicodeDecodeError:
                pass
        # UTF-16BE: 0x00, char, 0x00, char...
        if len(content_bytes) >= 4 and content_bytes[0] == 0 and content_bytes[2] == 0:
            try:
                decoded = content_bytes[:1024].decode("utf-16-be")
                if 'encoding="' in decoded or "charset=" in decoded:
                    import re
                    m = re.search(r'encoding=["\']([^"\']+)', decoded)
                    if m:
                        return m.group(1)
                    m = re.search(r'charset=["\']?([^"\'\s>]+)', decoded)
                    if m:
                        return m.group(1)
                return "utf-16-be"
            except UnicodeDecodeError:
                pass
        # Try ASCII decode for regular UTF-8 content
        try:
            decoded = content_bytes[:1024].decode("ascii")
            if 'encoding="' in decoded or "charset=" in decoded:
                import re
                m = re.search(r'encoding=["\']([^"\']+)', decoded)
                if m:
                    return m.group(1)
                m = re.search(r'charset=["\']?([^"\'\s>]+)', decoded)
                if m:
                    return m.group(1)
        except UnicodeDecodeError:
            pass
        return "utf-8"

    def _remove_unwanted_elements(self, body: html.HtmlElement) -> None:
        # Use namespace-agnostic approach: iterate all elements and check local name
        for tag_name in ["script", "style", "template", "noscript", "head"]:
            for elem in body.xpath(".//*"):
                if elem.tag.endswith(f"}}{tag_name}") or elem.tag == tag_name:
                    elem.getparent().remove(elem) if elem.getparent() is not None else None

    def _collect_resources(
        self,
        doc: html.HtmlElement,
        base_href: str,
        chapter_index: int,
        resources: list[ResourceRef],
        warnings: list[str],
    ) -> None:
        base_dir = posixpath.dirname(base_href) if posixpath.dirname(base_href) else "."

        def is_tag(elem, tag_name):
            return elem.tag.endswith(f"}}{tag_name}") or elem.tag == tag_name

        for elem in doc.iter():
            if is_tag(elem, "img"):
                src = elem.get("src", "")
                alt = elem.get("alt", "")
                if src:
                    if src.startswith("http://") or src.startswith("https://"):
                        warnings.append(f"Remote image resource detected: {src}")
                        resources.append(ResourceRef(
                            type="image", href=src, chapter_index=chapter_index,
                            metadata=MappingProxyType({"alt": alt, "remote": True})
                        ))
                    elif src.startswith("data:"):
                        resources.append(ResourceRef(
                            type="image", href="data:", chapter_index=chapter_index,
                            metadata=MappingProxyType({"alt": alt, "data_uri": True})
                        ))
                    else:
                        full_href = posixpath.normpath(posixpath.join(base_dir, src))
                        resources.append(ResourceRef(
                            type="image", href=full_href, chapter_index=chapter_index,
                            metadata=MappingProxyType({"alt": alt})
                        ))
            elif is_tag(elem, "link") and elem.get("rel") == "stylesheet":
                href = elem.get("href", "")
                media = elem.get("media", "all")
                if href:
                    if href.startswith("http://") or href.startswith("https://"):
                        warnings.append(f"Remote CSS resource detected: {href}")
                        resources.append(ResourceRef(
                            type="css", href=href, chapter_index=chapter_index,
                            metadata=MappingProxyType({"media": media, "remote": True})
                        ))
                    else:
                        full_href = posixpath.normpath(posixpath.join(base_dir, href))
                        resources.append(ResourceRef(
                            type="css", href=full_href, chapter_index=chapter_index,
                            metadata=MappingProxyType({"media": media})
                        ))
            elif is_tag(elem, "style"):
                if elem.text:
                    warnings.append("Inline style element found; not extracted to text")

    def _strip_scripts(self, doc: html.HtmlElement, warnings: list[str]) -> None:
        def is_tag(elem, tag_name):
            return elem.tag.endswith(f"}}{tag_name}") or elem.tag == tag_name

        # Collect scripts first to avoid modifying tree during iteration
        scripts_to_remove = []
        for elem in doc.iter():
            if is_tag(elem, "script"):
                scripts_to_remove.append(elem)
            else:
                for attr in ["onclick", "onload", "onerror", "onmouseover", "onmouseout"]:
                    if attr in elem.attrib:
                        warnings.append(f"Event handler stripped: {attr}")
                        del elem.attrib[attr]

        for elem in scripts_to_remove:
            src = elem.get("src", "")
            if src:
                warnings.append(f"Script resource stripped: {src}")
            else:
                warnings.append("Script resource stripped")
            elem.getparent().remove(elem) if elem.getparent() is not None else None

    def _extract_text_from_body(self, body: html.HtmlElement) -> str:
        parts: list[str] = []

        def get_local_name(tag: str) -> str:
            """Extract local name from namespaced tag."""
            if tag.startswith("{"):
                return tag.split("}", 1)[1]
            return tag

        def has_element_children(elem: html.HtmlElement) -> bool:
            """Check if element has any element children (not just text)."""
            for child in elem:
                if isinstance(child.tag, str):
                    return True
            return False

        def process_element(elem: html.HtmlElement, depth: int = 0) -> None:
            tag = elem.tag if isinstance(elem.tag, str) else ""
            local_tag = get_local_name(tag)

            # Special handling for ruby - process before children to capture base+rt together
            if local_tag == "ruby":
                base_text = (elem.text or "").strip()
                rt_text = ""
                for child in elem:
                    child_tag = get_local_name(child.tag if isinstance(child.tag, str) else "")
                    if child_tag == "rt":
                        rt_text = "".join(child.itertext()).strip()
                    elif child_tag == "rp":
                        pass
                if base_text and rt_text:
                    parts.append(f"{base_text}({rt_text})")
                elif base_text:
                    parts.append(base_text)
                # Don't process children separately - we already handled them
                return

            # Process children first for proper nesting
            for child in elem:
                process_element(child, depth + 1)

            # Then handle the element itself - only add text for leaf elements
            # (elements without element children) to avoid duplication
            if local_tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                if not has_element_children(elem):
                    text = (elem.text or "").strip()
                    if text:
                        parts.append(text)
            elif local_tag == "p":
                if not has_element_children(elem):
                    text = (elem.text or "").strip()
                    if text:
                        parts.append(text)
            elif local_tag == "li":
                if not has_element_children(elem):
                    text = (elem.text or "").strip()
                    if text:
                        parts.append(f"- {text}")
            elif local_tag == "table":
                self._process_table(elem, parts)
            elif local_tag in {"span", "em", "strong", "i", "b", "u", "sub", "sup", "code", "a"}:
                if not has_element_children(elem):
                    text = (elem.text or "").strip()
                    if text:
                        parts.append(text)
            elif local_tag == "ruby":
                # Already handled above
                pass
            elif local_tag == "img":
                src = elem.get("src", "")
                alt = elem.get("alt", "")
                parts.append(f"[IMAGE: src=\"{src}\" alt=\"{alt}\"]")
            elif local_tag == "svg":
                parts.append("[SVG]")
            elif local_tag == "math":
                math_text = "".join(elem.itertext()).strip()
                parts.append(f"[MATHML] {math_text}")
            elif local_tag == "br":
                parts.append("\n")
            elif local_tag in {"div", "section", "article", "blockquote", "pre", "ul", "ol", "header", "footer", "aside", "nav", "body", "html"}:
                # Container elements - children already processed
                pass
            elif isinstance(elem.tag, str) and not has_element_children(elem):
                # Leaf elements with text content
                text = (elem.text or "").strip()
                if text:
                    parts.append(text)
                warnings_list = getattr(self, "_extraction_warnings", [])
                warnings_list.append(f"Unknown element extracted: {local_tag}")

        process_element(body)
        return "\n".join(parts)

    def _extract_text_from_xml_tree(self, root: Any) -> str:
        """Extract text from XML tree (lxml.etree._Element) with HTML-like semantics.
        This preserves entities as text and handles malformed XML."""
        parts: list[str] = []

        def get_local_name(tag: str) -> str:
            """Extract local name from namespaced tag."""
            if tag.startswith("{"):
                return tag.split("}", 1)[1]
            return tag

        def has_element_children(elem: Any) -> bool:
            """Check if element has any element children (not just text)."""
            for child in elem:
                if isinstance(child.tag, str):
                    return True
            return False

        def process_element(elem: Any, depth: int = 0) -> None:
            tag = elem.tag if isinstance(elem.tag, str) else ""
            local_tag = get_local_name(tag)

            # Special handling for ruby - process before children to capture base+rt together
            if local_tag == "ruby":
                base_text = (elem.text or "").strip()
                rt_text = ""
                for child in elem:
                    child_tag = get_local_name(child.tag if isinstance(child.tag, str) else "")
                    if child_tag == "rt":
                        rt_text = "".join(child.itertext()).strip()
                    elif child_tag == "rp":
                        pass
                if base_text and rt_text:
                    parts.append(f"{base_text}({rt_text})")
                elif base_text:
                    parts.append(base_text)
                # Don't process children separately - we already handled them
                return

            # Process children first for proper nesting
            for child in elem:
                process_element(child, depth + 1)

            # Then handle the element itself - only add text for leaf elements
            # (elements without element children) to avoid duplication
            if local_tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                if not has_element_children(elem):
                    text = (elem.text or "").strip()
                    if text:
                        parts.append(text)
            elif local_tag == "p":
                if not has_element_children(elem):
                    text = (elem.text or "").strip()
                    if text:
                        parts.append(text)
            elif local_tag == "li":
                if not has_element_children(elem):
                    text = (elem.text or "").strip()
                    if text:
                        parts.append(f"- {text}")
            elif local_tag == "table":
                self._process_xml_table(elem, parts)
            elif local_tag in {"span", "em", "strong", "i", "b", "u", "sub", "sup", "code", "a"}:
                if not has_element_children(elem):
                    text = (elem.text or "").strip()
                    if text:
                        parts.append(text)
            elif local_tag == "ruby":
                # Already handled above
                pass
            elif local_tag == "img":
                src = elem.get("src", "")
                alt = elem.get("alt", "")
                parts.append(f"[IMAGE: src=\"{src}\" alt=\"{alt}\"]")
            elif local_tag == "svg":
                parts.append("[SVG]")
            elif local_tag == "math":
                math_text = "".join(elem.itertext()).strip()
                parts.append(f"[MATHML] {math_text}")
            elif local_tag == "br":
                parts.append("\n")
            elif local_tag in {"div", "section", "article", "blockquote", "pre", "ul", "ol", "header", "footer", "aside", "nav", "body", "html"}:
                # Container elements - children already processed
                pass
            elif isinstance(elem.tag, str) and not has_element_children(elem):
                # Leaf elements with text content - include tag name for unknown elements
                text = (elem.text or "").strip()
                if text:
                    # For unknown elements, include the tag name to preserve it in output
                    known_tags = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "span", "em", "strong", "i", "b", "u", "sub", "sup", "code", "a", "img", "svg", "math", "br", "div", "section", "article", "blockquote", "pre", "ul", "ol", "header", "footer", "aside", "nav", "body", "html", "ruby", "rt", "rp", "table", "tr", "th", "td"}
                    if local_tag not in known_tags:
                        parts.append(f"<{local_tag}>")
                    parts.append(text)
                warnings_list = getattr(self, "_extraction_warnings", [])
                warnings_list.append(f"Unknown element extracted: {local_tag}")

        process_element(root)
        return "\n".join(parts)

    def _process_xml_table(self, table: Any, parts: list[str]) -> None:
        def get_local_name(tag: str) -> str:
            if tag.startswith("{"):
                return tag.split("}", 1)[1]
            return tag

        for elem in table.iter():
            if get_local_name(elem.tag) == "tr":
                row_parts = []
                for cell in elem.iter():
                    cell_local = get_local_name(cell.tag)
                    if cell_local in ("th", "td"):
                        text = "".join(cell.itertext()).strip()
                        if cell_local == "th":
                            row_parts.append(f"[TH] {text}")
                        else:
                            row_parts.append(text)
                if row_parts:
                    parts.append(" | ".join(row_parts))

    def _process_table(self, table: html.HtmlElement, parts: list[str]) -> None:
        def get_local_name(tag: str) -> str:
            if tag.startswith("{"):
                return tag.split("}", 1)[1]
            return tag

        for elem in table.iter():
            if get_local_name(elem.tag) == "tr":
                row_parts = []
                for cell in elem.iter():
                    cell_local = get_local_name(cell.tag)
                    if cell_local in ("th", "td"):
                        text = "".join(cell.itertext()).strip()
                        if cell_local == "th":
                            row_parts.append(f"[TH] {text}")
                        else:
                            row_parts.append(text)
                if row_parts:
                    parts.append(" | ".join(row_parts))

    def _normalize_text(self, text: str) -> str:
        import unicodedata
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = unicodedata.normalize("NFC", text)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def _escape_bare_ampersands(self, content_bytes: bytes) -> bytes:
        """Escape bare & characters that are not part of valid entities.
        This prevents XML parser from treating them as malformed entities."""
        import re
        # Decode to string for processing
        try:
            text = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return content_bytes
        # Replace bare & (not followed by valid entity pattern) with &
        # Valid entity: &name; or &#nnn; or &#xhhhh;
        # Bare &: & not followed by #, letter, or &
        amp_entity = chr(38) + "amp;"
        text = re.sub(r'&(?!#[0-9]+;|#x[0-9a-fA-F]+;|[a-zA-Z][a-zA-Z0-9]*;)', amp_entity, text)
        return text.encode('utf-8')

    def _decode_html_entities(self, text: str) -> str:
        """Decode HTML entities in a single pass (no double decoding)."""
        import html.entities

        # Handle numeric entities first: &#nnn; and &#xhhhh;
        def replace_numeric(match):
            try:
                if match.group(1).startswith('x'):
                    return chr(int(match.group(1)[1:], 16))
                else:
                    return chr(int(match.group(1)))
            except (ValueError, OverflowError):
                return match.group(0)

        text = re.sub(r'&#(x[0-9a-fA-F]+|\d+);', replace_numeric, text)

        # Handle named entities (HTML5)
        def replace_named(match):
            name = match.group(1)
            if name in html.entities.html5:
                return html.entities.html5[name]
            return match.group(0)  # Keep unknown entities as-is

        text = re.sub(r'&([a-zA-Z][a-zA-Z0-9]*);', replace_named, text)

        return text

    def _resolve_chapter_title(
        self,
        spine_item: dict[str, Any],
        toc_map: dict[str, dict[str, Any]],
        chapter_text: str,
        chapter_index: int,
    ) -> str | None:
        """Legacy method - kept for compatibility. Use _extract_title_from_doc + _resolve_chapter_title_fallback instead."""
        return self._resolve_chapter_title_fallback(spine_item, toc_map, chapter_index)

    def _extract_title_from_doc(self, doc: html.HtmlElement) -> str | None:
        """Extract chapter title from parsed document using precedence:
        1. First <h1> in document order
        2. First <h2> in document order
        3. Document <title> element
        """
        # Find first h1
        for elem in doc.iter():
            if elem.tag.endswith("}h1") or elem.tag == "h1":
                text = "".join(elem.itertext()).strip()
                if text:
                    return text

        # Find first h2
        for elem in doc.iter():
            if elem.tag.endswith("}h2") or elem.tag == "h2":
                text = "".join(elem.itertext()).strip()
                if text:
                    return text

        # Find document title
        for elem in doc.iter():
            if elem.tag.endswith("}title") or elem.tag == "title":
                text = "".join(elem.itertext()).strip()
                if text:
                    return text

        return None

    def _resolve_chapter_title_fallback(
        self,
        spine_item: dict[str, Any],
        toc_map: dict[str, dict[str, Any]],
        chapter_index: int,
    ) -> str | None:
        """Fallback title resolution when no title extracted from document:
        1. Mapped nav/NCX TOC title
        2. Generated 'Chapter N'
        """
        href = spine_item.get("href", "")
        base_href = href.split("#")[0]

        if base_href in toc_map:
            return toc_map[base_href]["title"]

        return f"Chapter {chapter_index}"

    def _deduplicate_and_sort_resources(self, resources: list[ResourceRef]) -> list[ResourceRef]:
        seen = set()
        unique = []
        for r in resources:
            key = (r.type, r.href, r.chapter_index)
            if key not in seen:
                seen.add(key)
                unique.append(r)
        unique.sort(key=lambda r: (r.type, r.href or "", r.chapter_index or 0))
        return unique

    def _build_manifest(
        self,
        chapter_count: int,
        total_characters: int,
        total_words: int,
        warnings: tuple[str, ...],
        resources: tuple[ResourceRef, ...],
        spine_item_count: int,
        nav_toc_entries: int,
        encoding_used: str,
        parsing_duration_ms: int,
        fixed_layout: MappingProxyType[str, Any] | None,
    ) -> ExtractionManifest:
        return ExtractionManifest(
            extractor_version=self.extractor_version,
            extracted_at=datetime.now(timezone.utc).isoformat(),
            chapter_count=chapter_count,
            total_characters=total_characters,
            total_words=total_words,
            warnings=warnings,
            resources=resources,
            spine_item_count=spine_item_count,
            nav_toc_entries=nav_toc_entries,
            encoding_used=encoding_used,
            parsing_duration_ms=parsing_duration_ms,
            fixed_layout=fixed_layout,
        )

    def _determine_status(self, warnings: list[str]) -> str:
        blocked_keywords = [
            "path traversal", "zip bomb", "encrypted", "executable",
            "duplicate canonical path", "nested archive", "missing META-INF",
            "no rootfile", "not a valid OCF", "invalid ZIP",
        ]
        manual_keywords = [
            "remote image resource", "all spine items linear=no",
        ]
        partial_keywords = [
            "parse error", "not found", "malformed xhtml",
        ]

        for w in warnings:
            if any(kw in w.lower() for kw in blocked_keywords):
                return "blocked"
            if any(kw in w.lower() for kw in manual_keywords):
                return "manual_review_required"
            if any(kw in w.lower() for kw in partial_keywords):
                return "partial"

        return "success"


# Backwards compatibility - the spec requires these at module level for tests
__all__ = [
    "EpubMetadata",
    "ChapterBoundary",
    "ResourceRef",
    "ExtractionManifest",
    "EpubExtractionResult",
    "EpubExtractionError",
    "ExtractedTextIntakeRequest",
    "EpubExtractionBoundary",
]