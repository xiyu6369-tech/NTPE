from __future__ import annotations

from pathlib import Path


class ChunkMerger:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.final_output_dir = self.root / "final_output"
        self.final_output_dir.mkdir(parents=True, exist_ok=True)

    def merge_file(self, source_stem: str, chunk_outputs: list[Path]) -> Path:
        final_path = self.final_output_dir / f"{source_stem}_zh.txt"

        ordered = sorted(chunk_outputs, key=lambda p: p.name)

        with final_path.open("w", encoding="utf-8", newline="\n") as out:
            for p in ordered:
                text = p.read_text(encoding="utf-8-sig").strip()
                if text:
                    out.write(text)
                    out.write("\n\n")

        return final_path
