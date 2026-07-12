from pathlib import Path
import json, tempfile
from core.adaptive_context_canary_resume import prepare_canary_resume
import hashlib

def main():
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
        root=Path(tmp); src=root/'tests/literary/outputs/source/Golden_Set'; (src/'original_ko_chunks').mkdir(parents=True)
        (src/'original_ko_chunks/original_ko_chunk_000001_zh.txt').write_text('完成譯文。',encoding='utf-8')
        (src/'original_ko_resume_state.json').write_text(json.dumps({'chunks':{'000001':{'status':'success','source_hash':'abc'}}}),encoding='utf-8')
        plan=prepare_canary_resume(root,source_stage='source',target_stage='target',target_chunk=2)
        assert plan.ready and plan.copied_chunks==(1,)
        state=json.loads((root/'tests/literary/outputs/target/Golden_Set/original_ko_resume_state.json').read_text(encoding='utf-8'))
        assert state['chunks']['000001']['status']=='success'
    manifest=json.loads(Path('manifests/te_v700_stage07_ace_canary_resume_manifest.json').read_text(encoding='utf-8'))
    for name, digest in manifest['integrity']['files'].items():
        target = Path(name)
        assert target.exists(), name
        if name.startswith('manifests/'):
            json.loads(target.read_text(encoding='utf-8'))
            continue
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, name
    print('TE v7.0 Stage 07 ACE Canary Resume ALL PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
