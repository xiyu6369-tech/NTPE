from pathlib import Path
import chardet


def read_text_auto(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr", "big5", "gb18030"]:
        try:
            return raw.decode(enc).replace("\x00", "")
        except Exception:
            pass
    detected = chardet.detect(raw)
    enc = detected.get("encoding") or "utf-8"
    return raw.decode(enc, errors="replace").replace("\x00", "")
