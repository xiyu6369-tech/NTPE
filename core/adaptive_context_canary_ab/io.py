from __future__ import annotations
import json,re
from pathlib import Path
from .model import QualityEvidence,CanaryABReport

def _issue_texts(data: dict) -> tuple[str,...]:
    rows=data.get('issues',[]) or []
    out=[]
    for row in rows:
        if isinstance(row,str): out.append(row)
        elif isinstance(row,dict): out.append(str(row.get('code') or row.get('message') or row))
    return tuple(out)

def load_stage_evidence(root: str|Path, stage: str, chunk: int, set_name: str='Golden_Set') -> QualityEvidence:
    base=Path(root)/'tests'/'literary'/'outputs'/stage/set_name
    resume=base/'original_ko_resume_state.json'
    if not resume.exists(): raise FileNotFoundError(f'missing resume state: {resume}')
    rd=json.loads(resume.read_text(encoding='utf-8'))
    key=f'{chunk:06d}'; row=(rd.get('chunks') or {}).get(key)
    if not isinstance(row,dict): raise ValueError(f'missing chunk evidence: {key}')
    source_hash=str(row.get('source_hash',''))
    chunk_dir=base/'original_ko_chunks'
    reports=sorted(chunk_dir.glob(f'original_ko_chunk_{key}_quality_v5_attempt_*.json'))
    if not reports: raise FileNotFoundError(f'missing quality report for chunk {key}')
    data=json.loads(reports[-1].read_text(encoding='utf-8'))
    metrics=data.get('metrics') if isinstance(data.get('metrics'),dict) else {}
    status=str(row.get('status',''))
    provider_complete=status in {'success','pass_with_warning'}
    return QualityEvidence(stage,chunk,source_hash,bool(data.get('accepted',False)),str(data.get('status','unknown')),
        int(data.get('quality_score',0) or 0),_issue_texts(data),int(metrics.get('source_chars',0) or 0),
        int(metrics.get('translated_chars',0) or 0),int(metrics.get('source_paragraph_count',0) or 0),
        int(metrics.get('translated_paragraph_count',0) or 0),float(metrics.get('length_ratio',0.0) or 0.0),provider_complete)

def write_ab_report(report: CanaryABReport,path: str|Path)->Path:
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report.to_dict(),ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return p
