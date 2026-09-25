with open('D:\\Python\\NTPE\\core\\epub_translation\\runtime\\epub_packager.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add pack_epub_resource_aware function before the last few lines
# Find the position before validate_packaging_input
idx = content.rfind('def validate_packaging_input')
if idx >= 0:
    # Insert the pack_epub_resource_aware function before validate_packaging_input
    pack_func = '''\n\ndef pack_epub_resource_aware(
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

        spine_items: list = ["nav"]
        chapter_items: list = []
        href_map: dict[str, str] = {}  # chapter_id -> output href

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
        toc_items: list = []
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
'''

    # Insert before validate_packaging_input
    new_content = content[:idx] + pack_func + '\n\n' + content[idx:]
    with open('D:\\Python\\NTPE\\core\\epub_translation\\runtime\\epub_packager.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Added pack_epub_resource_aware function')
"