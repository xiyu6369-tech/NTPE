import zipfile
import xml.etree.ElementTree as ET
import os
from pathlib import Path

# Recreate the test scenario
tmp_path = Path('D:/Temp/test_broken_css4')
tmp_path.mkdir(exist_ok=True)
broken_epub = tmp_path / 'broken_css.epub'

with zipfile.ZipFile(broken_epub, 'w') as z:
    z.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
    
    container = ET.Element('container', version='1.0', xmlns='urn:oasis:names:tc:opendocument:xmlns:container')
    rootfiles = ET.SubElement(container, 'rootfiles')
    rootfile = ET.SubElement(rootfiles, 'rootfile', media_type='application/oebps-package+xml')
    rootfile.set('full-path', 'OEBPS/content.opf')
    z.writestr('META-INF/container.xml', ET.tostring(container, encoding='unicode'))
    
    opf = ET.Element('package')
    opf.set('xmlns', 'http://www.idpf.org/2007/opf')
    opf.set('unique-identifier', 'bookid')
    opf.set('version', '3.0')
    metadata = ET.SubElement(opf, 'metadata')
    ET.SubElement(metadata, '{http://purl.org/dc/elements/1.1/}identifier', id='bookid').text = 'test-book'
    ET.SubElement(metadata, '{http://purl.org/dc/elements/1.1/}title').text = 'Test Book'
    ET.SubElement(metadata, '{http://purl.org/dc/elements/1.1/}language').text = 'ko'
    manifest = ET.SubElement(opf, 'manifest')
    ET.SubElement(manifest, 'item', id='nav', href='nav.xhtml', media_type='application/xhtml+xml', properties='nav')
    ET.SubElement(manifest, 'item', id='ch1', href='chapter01.xhtml', media_type='application/xhtml+xml')
    spine = ET.SubElement(opf, 'spine')
    ET.SubElement(spine, 'itemref', idref='nav')
    ET.SubElement(spine, 'itemref', idref='ch1')
    z.writestr('OEBPS/content.opf', ET.tostring(opf, encoding='unicode'))
    
    nav = ET.Element('html', xmlns='http://www.w3.org/1999/xhtml', xmlns_epub='http://www.idpf.org/2007/ops')
    head = ET.SubElement(nav, 'head')
    ET.SubElement(head, 'title').text = 'Navigation'
    body = ET.SubElement(nav, 'body')
    nav_elem = ET.SubElement(body, 'nav', epub_type='toc')
    ol = ET.SubElement(nav_elem, 'ol')
    li = ET.SubElement(ol, 'li')
    ET.SubElement(li, 'a', href='chapter01.xhtml').text = 'Chapter 1'
    z.writestr('OEBPS/nav.xhtml', ET.tostring(nav, encoding='unicode'))
    
    # Chapter with CSS reference that doesn't exist in manifest
    ch1 = ET.Element('html', xmlns='http://www.w3.org/1999/xhtml', xmlns_epub='http://www.idpf.org/2007/ops')
    head1 = ET.SubElement(ch1, 'head')
    ET.SubElement(head1, 'title').text = 'Chapter 1'
    ET.SubElement(head1, 'link', rel='stylesheet', href='../Styles/missing.css')
    body1 = ET.SubElement(ch1, 'body')
    ET.SubElement(body1, 'p').text = 'Content'
    z.writestr('OEBPS/chapter01.xhtml', ET.tostring(ch1, encoding='unicode'))

# Now run the validation
from core.epub_translation.runtime.epub_packager import _validate_epub_archive
errors = _validate_epub_archive(Path('D:/Temp/test_broken_css3/broken_css.epub'))
print('Errors:', errors)
print('Test passed!' if errors else 'TEST FAILED - no errors found!')