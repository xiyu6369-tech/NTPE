from __future__ import annotations
import hashlib,json,tempfile
from pathlib import Path
from core.adaptive_context_canary_ab import QualityEvidence,evaluate_canary_ab,write_ab_report
ROOT=Path(__file__).resolve().parent

def ev(stage='base',accepted=True,score=100,issues=(),paras=3,ratio=.65,chars=360,complete=True):
    return QualityEvidence(stage,3,'same-hash',accepted,'accepted' if accepted else 'retry_required',score,tuple(issues),514,chars,4,paras,ratio,complete)

def main()->int:
    passed=evaluate_canary_ab(ev(),ev('canary'))
    assert passed.ready and passed.status=='pass'
    assert evaluate_canary_ab(ev(),ev('canary',score=80)).blockers==('quality-score-regression',)
    assert 'new-omission-issue' in evaluate_canary_ab(ev(),ev('canary',issues=('PARAGRAPH_OMISSION_SUSPECTED',))).blockers
    assert 'new-unsupported-detail-issue' in evaluate_canary_ab(ev(),ev('canary',issues=('ADDED_DETAIL',))).blockers
    assert 'canary-not-accepted' in evaluate_canary_ab(ev(),ev('canary',accepted=False)).blockers
    assert evaluate_canary_ab(ev(),QualityEvidence('x',3,'other',True,'accepted',100,(),514,360,4,3,.65,True)).ready is False
    with tempfile.TemporaryDirectory(dir=ROOT) as td:
        path=write_ab_report(passed,Path(td)/'report.json'); data=json.loads(path.read_text(encoding='utf-8'))
        assert data['metadata']['content_redacted'] is True and 'normalized_text' not in data
    manifest=json.loads((ROOT/'manifests/te_v700_stage075_canary_ab_quality_validation_manifest.json').read_text(encoding='utf-8'))
    for name,digest in manifest['files'].items():
        p=ROOT/name; assert p.exists(),name
        if name.startswith('manifests/') or name.startswith('artifacts/'): continue
        assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
    print('TE v7.0 Stage 07.5 Canary A/B Quality Validation ALL PASS');return 0
if __name__=='__main__': raise SystemExit(main())
