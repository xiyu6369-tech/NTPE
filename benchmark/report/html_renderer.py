from __future__ import annotations

from html import escape
from typing import Any, Dict


class HTMLReportRenderer:
    def render(self, report: Dict[str, Any]) -> str:
        summary = report.get("summary", {})
        rows = []
        for item in report.get("results", []):
            metrics = item.get("metrics") or {}
            rows.append(
                "<tr>"
                f"<td>{escape(str(item.get('name', '')))}</td>"
                f"<td>{escape(str(item.get('status', '')))}</td>"
                f"<td>{escape(str(item.get('elapsed_ms', 0)))}</td>"
                f"<td>{escape(str(metrics.get('category', 'general')))}</td>"
                "</tr>"
            )
        return "".join([
            "<!doctype html><html><head><meta charset='utf-8'>",
            "<title>", escape(str(report.get("title", "NTPE Performance Report"))), "</title>",
            "<style>body{font-family:Arial,sans-serif;margin:24px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:8px}th{background:#f4f4f4}</style>",
            "</head><body>",
            f"<h1>{escape(str(report.get('title', 'NTPE Performance Report')))}</h1>",
            f"<p>Status: <strong>{escape(str(summary.get('status', 'UNKNOWN')))}</strong></p>",
            f"<p>Total: {escape(str(summary.get('total', 0)))} | Passed: {escape(str(summary.get('passed', 0)))} | Failed: {escape(str(summary.get('failed', 0)))}</p>",
            "<table><thead><tr><th>Name</th><th>Status</th><th>Elapsed ms</th><th>Category</th></tr></thead><tbody>",
            "".join(rows),
            "</tbody></table></body></html>",
        ])


def render_html_report(report: Dict[str, Any]) -> str:
    return HTMLReportRenderer().render(report)
