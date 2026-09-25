import zipfile
import xml.etree.ElementTree as ET
import os
from pathlib import Path

# Test the validation logic step by step
with zipfile.ZipFile('D:/Temp/test_broken_css4/broken_css.epub', 'r') as z:
    namelist = z.namelist()
    print('Namelist:', namelist)

    # Read the chapter XHTML
    content = z.read('OEBPS/chapter01.xhtml').decode('utf-8')
    print('Chapter content:', content)

    import xml.etree.ElementTree as ET
    import os

    parser = ET.XMLParser(encoding='utf-8')
    root = ET.fromstring(content, parser=ET.XMLParser(encoding='utf-8'))

    # Check CSS references
    for link in root.findall('.//{http://www.w3.org/1999/xhtml}link[@rel="stylesheet"]'):
        href = link.get('href') or link.get('{http://www.w3.org/1999/xhtml}href')
        print('Found CSS href:', href)
        if href and not href.startswith(('http://', 'https://', 'data:')) and href not in ('#', ''):
            xhtml_href = 'OEBPS/chapter01.xhtml'
            base_dir = os.path.dirname('OEBPS/chapter01.xhtml')
            if base_dir:
                resolved = os.path.normpath(os.path.join(os.path.dirname('OEBPS/chapter01.xhtml'), '../Styles/missing.css'))
            else:
                resolved = '../Styles/missing.css'
            print('  Resolved:', resolved)
            # Check if resolved exists in archive
            archive_paths = set(z.namelist())
            for name in z.namelist():
                basename = os.path.basename(name)
                if basename:
                    pass
            # Check full paths
            if resolved in z.namelist():
                print('  Found in archive:', resolved)
            elif os.path.basename(resolved) in [os.path.basename(n) for n in z.namelist()]:
                print('  Found basename:', os.path.basename(resolved))
            else:
                print('  MISSING:', resolved)