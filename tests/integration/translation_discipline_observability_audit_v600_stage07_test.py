from pathlib import Path
from core.translation_discipline import DISCIPLINE_AUDIT_VERSION, orchestrate_runtime_discipline

def test_stage07_audit_metadata_and_runtime_wiring():
    report={'decision':'accepted','unified_quality_report':{'score':100,'decision':'accepted','merged_issues':[]}}
    outcome=orchestrate_runtime_discipline('譯文',report)
    audit=outcome.qa_report['discipline_audit_trail']
    assert audit['schema_version']==DISCIPLINE_AUDIT_VERSION
    assert audit['quality']['score']==100
    assert audit['quality']['issue_count']==0
    assert audit['final_action']=='accept'
    runtime=Path('lts/txt_translation_runtime.py').read_text(encoding='utf-8')
    assert 'discipline_audit_attempt_' in runtime
    assert 'discipline-audit' in runtime
    assert 'discipline_audit_trail' in runtime
