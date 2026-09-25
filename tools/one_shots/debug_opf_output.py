import xml.etree.ElementTree as ET

opf = ET.Element("package")
opf.set("xmlns", "http://www.idpf.org/2007/opf")
opf.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
opf.set("unique-identifier", "bookid")
opf.set("version", "3.0")
metadata = ET.SubElement(opf, "metadata")
ET.SubElement(metadata, "{http://purl.org/dc/elements/1.1/}identifier", id="bookid").text = "test-book"
ET.SubElement(metadata, "{http://purl.org/dc/elements/1.1/}title").text = "Test Book"
ET.SubElement(metadata, "{http://purl.org/dc/elements/1.1/}language").text = "ko"

print("OPF output:")
print(ET.tostring(opf, encoding="unicode"))