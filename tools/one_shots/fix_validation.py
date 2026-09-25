import re

# Read the file
with open("D:\\Python\\NTPE\\core\\epub_translation\\runtime\\epub_packager.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the broken _validate_xhtml_references function and replace it
old_pattern = r'def _validate_xhtml_references\(.*?def _validate_epub_archive'
new_code = '''def _validate_xhtml_references(
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
        
        def get_archive_paths(namelist: list[str]) -> set[str]:
            paths = set(namelist)
            for name in namelist:
                basename = os.path.basename(name)
                if basename:
                    paths.add(basename)
            return paths
        
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
        
        archive_paths = set(namelist)
        for name in namelist:
            basename = os.path.basename(name)
            if basename:
                paths.add(basename)
        
        archive_paths = set(namelist)
        for name in namelist:
            basename = os.path.basename(name)
            if basename:
                archive_paths.add(basename)
        
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
                archive_paths = set(namelist)
                for name in namelist:
                    basename = os.path.basename(name)
                    if basename:
                        archive_paths.add(basename)
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
                archive_paths = set(namelist)
                for name in namelist:
                    basename = os.path.basename(name)
                    if basename:
                        archive_paths.add(basename)
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
                    archive_paths = set(namelist)
                    for name in namelist:
                        basename = os.path.basename(name)
                        if basename:
                            archive_paths.add(basename)
                    if resolved not in archive_paths and os.path.basename(resolved) not in archive_paths:
                        if '#' in href:
                            base_href = href.split('#')[0]
                            if base_href and base_href not in set(namelist):
                                errors.append(f"Internal link target not found in archive: {href} (base: {base_href}) in {xhtml_href}")
                        else:
                            errors.append(f"Internal link target not found in archive: {href} (resolved to {resolved}) in {xhtml_href}")
        
    except Exception as e:
        errors.append(f"XHTML reference validation error in {xhtml_href}: {e}")
    
    return errors


def _validate_epub_archive(epub_path: Path) -> list[str]:
'''

# Read the file
with open("D:\\Python\\NTPE\\core\\epub_translation\\runtime\\epub_packager.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find and replace the broken function
pattern = r'def _validate_xhtml_references\(.*?def _validate_epub_archive'
content = re.sub(pattern, new_code, content, flags=re.DOTALL)

with open("D:\\Python\\NTPE\\core\\epub_translation\\runtime\\epub_packager.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed!")