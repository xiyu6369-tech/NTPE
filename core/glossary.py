from pathlib import Path
from typing import Dict, List, Tuple


class Glossary:
    def __init__(self, path: Path):
        self.path = path
        self.terms: Dict[str, str] = {}
        self.load()

    def load(self) -> None:
        self.terms.clear()
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("정태의=鄭泰義\n카일=凱爾\n", encoding="utf-8")
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            src, dst = line.split("=", 1)
            src, dst = src.strip(), dst.strip()
            if src and dst:
                self.terms[src] = dst

    def prompt_block(self) -> str:
        if not self.terms:
            return "無"
        items = sorted(self.terms.items(), key=lambda x: len(x[0]), reverse=True)
        return "\n".join(f"- {src} → {dst}" for src, dst in items)

    def apply_output_fix(self, text: str) -> str:
        # 常見錯譯修正，之後可擴充到檔案化
        fixes = {
            "正太義": "鄭泰義",
            "鄭太義": "鄭泰義",
            "鄭泰意": "鄭泰義",
            "卡爾": "凱爾",
        }
        for bad, good in fixes.items():
            text = text.replace(bad, good)
        return text

    def check_required_terms(self, source: str, translated: str) -> List[str]:
        errors = []
        for src, dst in sorted(self.terms.items(), key=lambda x: len(x[0]), reverse=True):
            if src in source and dst not in translated:
                errors.append(f"術語未固定：{src} 應為 {dst}")
        return errors
