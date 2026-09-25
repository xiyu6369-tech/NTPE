import xml.etree.ElementTree as ET

container_xml = '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml" /></rootfiles></container>'

root = ET.fromstring(container_xml)
print('root tag:', root.tag)

ns = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
rootfile = root.find('.//container:rootfile', ns)
print('rootfile:', rootfile)
if rootfile is not None:
    print('rootfile attrib:', rootfile.attrib)
    print('full-path:', rootfile.get('full-path'))