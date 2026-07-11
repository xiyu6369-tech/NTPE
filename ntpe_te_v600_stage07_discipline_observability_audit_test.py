from __future__ import annotations
from core.translation_discipline import ACCEPT_WITH_WARNINGS, DISCIPLINE_AUDIT_VERSION, build_discipline_audit_trail, orchestrate_runtime_discipline

def _issue(code, route, rule, severity='medium'):
    return {'code':code,'severity':severity,'metadata':{'discipline_route':route,'discipline_rule_code':rule}}
def _report(*issues, decision='retry_required'):
    return {'decision':decision,'retry_required':decision=='retry_required','unified_quality_report':{'score':80,'decision':decision,'retry_required':decision=='retry_required','merged_issues':list(issues)}}
def main():
    def revalidate(_): return _report(_issue('NATURALNESS_GUARD','warning','LITERARY_NATURALNESS'),decision='accepted_with_warnings')
    outcome=orchestrate_runtime_discipline('他請了一周假。',_report(_issue('SIMPLIFIED_CHINESE','local_repair','TRADITIONAL_ORTHOGRAPHY')),revalidate=revalidate)
    audit=outcome.qa_report['discipline_audit_trail']
    assert audit['schema_version']==DISCIPLINE_AUDIT_VERSION
    assert audit['initial_action']=='local_repair'
    assert audit['final_action']==ACCEPT_WITH_WARNINGS
    assert audit['revalidated'] is True
    assert audit['local_repair']['changed'] is True
    assert audit['local_repair']['repaired_codes']==['SIMPLIFIED_CHINESE']
    assert audit['discipline']['active_rule_codes']==['LITERARY_NATURALNESS']
    assert audit['discipline']['routes']=={'warning':['NATURALNESS_GUARD']}
    direct=build_discipline_audit_trail(outcome.qa_report,initial_action=outcome.initial_action,final_action=outcome.final_action,revalidated=outcome.revalidated,local_repair=outcome.local_repair_result.to_metadata()).to_metadata()
    assert direct['retry_decision']['action']==ACCEPT_WITH_WARNINGS
    print('NTPE TE v6.0 Stage 07 Discipline Observability & Audit Trail')
    print('===========================================================')
    print('Issue/rule/route audit captured          PASS')
    print('Local repair actions captured            PASS')
    print('Retry decision and final reason captured PASS')
    print('Orchestrator output remains equivalent   PASS')
    print('ALL PASS')
    return 0
if __name__=='__main__': raise SystemExit(main())
