import os
from xml.etree import ElementTree as ET
from xml.dom import minidom
from types import SimpleNamespace

# Recreate the extracted resources structure
extracted = SimpleNamespace()
extracted.resource_bytes = {
    'nav.xhtml': b'test',
    'chapter01.xhtml': b'<html xmlns="http://www.w3.org/1999/xhtml" xmlns_epub="http://www.idpf.org/2007/ops"><head><title>Chapter 1</title><link rel="stylesheet" href="../Styles/main.css" /></head><body><h1 id="section-1">Chapter 1 Title</h1><p>This is chapter 1.</p><img src="../Images/image01.png" alt="Test Image" /><a href="chapter02.xhtml">Next Chapter</a><a href="#section-1">Link to Section 1</a></body></html>',
    'chapter02.xhtml': b'test',
    'Styles/main.css': b'test',
    'Images/image01.png': b'test',
}

source_href = 'OEBPS/chapter01.xhtml'
translated_text = '번역된 내용'
title = 'Chapter 1'
default_language = 'ko'

import os
from xml.etree import ElementTree as ET
from xml.dom import minidom

source_href_clean = source_href.split('#')[0]
source_xhtml_bytes = None
source_xhtml_href = None

if source_href_clean in extracted.resource_bytes:
    source_xhtml_bytes = extracted.resource_bytes[source_href_clean]
    source_xhtml_href = source_href_clean
else:
    basename = os.path.basename(source_href_clean)
    if basename in extracted.resource_bytes:
        source_xhtml_bytes = extracted.resource_bytes[basename]
        source_xhtml_href = basename

print(f'source_xhtml_href: {source_xhtml_href}')

if not source_xhtml_bytes:
    print('No source XHTML found')
else:
    try:
        source_xhtml = source_xhtml_bytes.decode('utf-8')
        print('Source XHTML:')
        print(source_xhtml[:500])
        
        parser = ET.XMLParser(encoding='utf-8')
        root = ET.fromstring(source_xhtml, parser=parser)
        print('Parsed successfully')
        print('Root tag:', root.tag)
        
        ET.register_namespace('', 'http://www.w3.org/1999/xhtml')
        ET.register_namespace('epub', 'http://www.idpf.org/2007/ops')
        
        translated_paragraphs = [p.strip() for p in translated_text.split('\n\n') if p.strip()]
        para_iter = iter(translated_paragraphs)
        
        XHTML_NS = 'http://www.w3.org/1999/xhtml'
        
        def process_element(elem):
            # Handle text content replacement for text-bearing elements
            tag_name = elem.tag
            if '}' in tag_name:
                local_name = tag_name.split('}', 1)[1]
            else:
                local_name = tag_name
                
            if local_name in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th', 'span', 'div'):
                try:
                    new_text = next(para_iter)
                    elem.text = new_text
                    for child in list(elem):
                        if child.tail:
                            child.tail = None
                except StopIteration:
                    pass
            
            if local_name == 'a':
                href = elem.get('href')
                if href and not href.startswith('#') and not href.startswith('http://') and not href.startswith('https://'):
                    new_href = os.path.basename(href.split('#')[0])
                    if '#' in href:
                        fragment = href.split('#', 1)[1]
                        new_href = f'{new_href}#{fragment}'
                    elem.set('href', new_href)
            
            if local_name == 'img':
                src = elem.get('src')
                if src and not src.startswith('http://') and not src.startswith('https://') and not src.startswith('data:'):
                    new_src = os.path.basename(src.split('#')[0])
                    elem.set('src', new_src)
            
            if local_name == 'link':
                href = elem.get('href')
                if href and not href.startswith('http://') and not href.startswith('https://'):
                    new_href = os.path.basename(href.split('#')[0])
                    elem.set('href', new_href)
            
            for child in elem:
                process_element(child)
        
        translated_paragraphs = [p.strip() for p in translated_text.split('\n\n') if p.strip()]
        para_iter = iter(translated_paragraphs)
        
        process_element(root)
        
        # Ensure proper namespace declarations
        root.set('xmlns', 'http://www.w3.org/1999/xhtml')
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
        rough_string = ET.tostring(root, encoding='unicode', method='xml')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent='  ', encoding=None)
        lines = pretty_xml.split('\n')
        if lines[0].startswith('<?xml'):
            lines = lines[1:]
        lines = [line for line in lines if line.strip() or line.startswith('<')]
        pretty_xml = '\n'.join(lines)
        
        final_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
{pretty_xml}'''
        
        print('Result:')
        print(final_xml[:1000])
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()