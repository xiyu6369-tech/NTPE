from ebooklib import epub
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    output_path = tmp_path / "output.epub"
    
    book = epub.EpubBook()
    book.set_identifier("test-book")
    book.set_title("Test Book")
    book.set_language("ko")
    book.add_author("Test Author")
    
    # Add a simple chapter
    chapter = epub.EpubHtml(title="Chapter 1", file_name="chapter1.xhtml", lang="ko")
    chapter.content = b"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body><p>Content</p></body></html>"""
    book.add_item(chapter)
    
    # Add nav
    nav = epub.EpubHtml(title="Navigation", file_name="nav.xhtml", lang="ko")
    nav.content = b"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Navigation</title></head>
<body><nav epub:type="toc"><ol><li><a href="chapter1.xhtml">Chapter 1</a></li></ol></nav></body></html>"""
    book.add_item(nav)
    
    # Add CSS
    css = epub.EpubItem(uid="style_css", file_name="style.css", media_type="text/css", content=b"body { font-family: serif; }")
    book.add_item(css)
    
    book.spine = ["nav", chapter]
    book.toc = [epub.Link("chapter1.xhtml", "Chapter 1", "ch1")]
    book.add_item(epub.EpubNcx())  # This might be the issue
    
    try:
        epub.write_epub(str(output_path), book)
        print("SUCCESS with NCX!")
    except Exception as e:
        print(f"ERROR with NCX: {e}")
        import traceback
        traceback.print_exc()