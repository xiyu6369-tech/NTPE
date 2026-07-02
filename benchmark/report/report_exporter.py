from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .html_renderer import render_html_report
from .json_renderer import render_json_report


class PerformanceReportExporter:
    def export_json(self, report: Dict[str, Any], path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_json_report(report), encoding="utf-8")
        return path

    def export_html(self, report: Dict[str, Any], path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_html_report(report), encoding="utf-8")
        return path

    def export(self, report: Dict[str, Any], output_dir: str | Path, basename: str = "benchmark") -> Dict[str, Path]:
        output_dir = Path(output_dir)
        return {
            "json": self.export_json(report, output_dir / f"{basename}.json"),
            "html": self.export_html(report, output_dir / f"{basename}.html"),
        }


def export_performance_report(report: Dict[str, Any], output_dir: str | Path, basename: str = "benchmark") -> Dict[str, Path]:
    return PerformanceReportExporter().export(report, output_dir, basename)
