from __future__ import annotations

import json
from typing import Any, Dict


class JSONReportRenderer:
    def render(self, report: Dict[str, Any]) -> str:
        payload = dict(report)
        payload.setdefault("schema", "ntpe.performance.report.v1")
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def render_json_report(report: Dict[str, Any]) -> str:
    return JSONReportRenderer().render(report)
