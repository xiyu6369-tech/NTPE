from __future__ import annotations
import json, tempfile
from pathlib import Path
from core.translation_discipline.adaptive_retry_policy import build_adaptive_retry_plan
from core.translation_discipline.production_validation import summarize_stage_output
from core.translation_discipline.runtime_integration import DISCIPLINE_RUNTIME_INTEGRATION_VERSION

def main() -> int:
    warning_report={"merged_issues":[{"code":"PARAGRAPH_STRUCTURE_MERGED","severity":"medium","retry_required":False}]}
    plan=build_adaptive_retry_plan(warning_report, source_text="原文")
    assert plan.tier == "none"
    assert DISCIPLINE_RUNTIME_INTEGRATION_VERSION == "6.0.0-stage10"
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'x_discipline_audit_attempt_1.json'
        p.write_text(json.dumps({"final_action":"accept_with_warnings","quality":{"issues":[{"code":"NATURALNESS_GUARD"}]},"local_repair":{"changed":False},"adaptive_retry_policy":{"retry_tier":"none","provider_call_budget":{"limit":2,"used":0,"remaining":2}}}),encoding='utf-8')
        s=summarize_stage_output(td)
        assert s.audit_reports == 1 and s.accepted_with_warnings == 1
    print('TE v6.0 Stage 10.1 Production Validation')
    print('=========================================')
    print('Paragraph merge remains warning       PASS')
    print('Runtime integration version stage10   PASS')
    print('Audit summary aggregation             PASS')
    print('ALL PASS')
    return 0
if __name__=='__main__': raise SystemExit(main())
