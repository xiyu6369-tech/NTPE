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
        if 'xmlns' not in root.attrib:
            root.set('xmlns', 'http://www.w3.org/1999/xhtml')
        if 'xmlns:epub' not in root.attrib:
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
        
        # Pretty print using minidom
        pretty_xml = None
        try:
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ", encoding=None)
            lines = pretty_xml.split('\n')
            if lines[0].startswith('<?xml'):
                lines = lines[1:]
            lines = [line for line in lines if line.strip() or line.startswith('<')]
            pretty_xml = '\n'.join(lines)
        except Exception:
            pretty_xml = None
        
        if pretty_xml:
            final_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
{pretty_xml}"""
            return final_xml
        else:
            # Fallback: use ElementTree's serialization without minidom
            try:
                ET.indent(root, space="  ")
            except AttributeError:
                pass
            rough_string = ET.tostring(root, encoding='unicode', method='xml')
            final_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
{rough_string}"""
            return final_xml
        
    except Exception:
        # If any error occurs, return None to use fallback
        return None