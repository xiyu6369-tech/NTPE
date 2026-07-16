from __future__ import annotations
import hashlib,json
from functools import lru_cache
from pathlib import Path
from .models import ValidationCorpusEntry
from .validation import reject_fixture_result_fields,reject_unsafe
FIXTURE_FILES=("tic_cases.json","golden_historical_cases.json","semantic_mutations.json","memory_cases.json","context_scene_cases.json","cache_resume_cases.json","dual_pass_cases.json","multilingual_cases.json","provider_routing_cases.json","cross_module_cases.json")
def _inside(path:Path,root:Path)->Path:
    resolved=path.resolve();base=root.resolve()
    if resolved!=base and base not in resolved.parents:raise ValueError("path traversal or symlink escape")
    return resolved
@lru_cache(maxsize=32)
def _load_fixed_corpus(base_text:str,allowed_text:str)->tuple[ValidationCorpusEntry,...]:
    base=Path(base_text);allowed=Path(allowed_text);items=[]
    for name in FIXTURE_FILES:
        path=_inside(base/name,allowed)
        value=json.loads(path.read_text(encoding="utf-8"));reject_unsafe(value)
        reject_fixture_result_fields(value)
        if value.get("fixture_schema")!="lcr.batch9.fixture.v1":raise ValueError("unknown fixture schema")
        for case in value.get("cases",[]):
            required=("case_id","evidence_origin","human_approved","synthetic","historical","current_health","evidence_reference","payload")
            if any(k not in case for k in required):raise ValueError("missing fixture evidence metadata")
            items.append(ValidationCorpusEntry(**{k:case[k] for k in required}))
    return tuple(sorted(items,key=lambda x:x.case_id))
@lru_cache(maxsize=32)
def load_validation_corpus(fixtures_root:str|Path,*,allowed_root:str|Path)->tuple[ValidationCorpusEntry,...]:
    allowed=Path(allowed_root).resolve();base=_inside(Path(fixtures_root),allowed)
    return _load_fixed_corpus(str(base),str(allowed))
def corpus_fingerprint(entries)->str:
    data=[{"case_id":x.case_id,"origin":x.evidence_origin,"reference":x.evidence_reference,"payload":x.payload} for x in entries]
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
