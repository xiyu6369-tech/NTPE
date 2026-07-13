from __future__ import annotations
import json, shutil
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class CanaryResumePlan:
    source_stage: str
    target_stage: str
    target_chunk: int
    copied_chunks: tuple[int, ...]
    missing_chunks: tuple[int, ...]
    ready: bool


def _stage_dir(root: Path, stage: str) -> Path:
    return root / 'tests' / 'literary' / 'outputs' / stage / 'Golden_Set'


def prepare_canary_resume(root: str | Path, *, source_stage: str, target_stage: str, target_chunk: int) -> CanaryResumePlan:
    root = Path(root)
    target_chunk = max(1, int(target_chunk))
    src = _stage_dir(root, source_stage)
    dst = _stage_dir(root, target_stage)
    dst.mkdir(parents=True, exist_ok=True)
    copied: list[int] = []
    missing: list[int] = []
    state_path = src / 'original_ko_resume_state.json'
    source_state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {'chunks': {}}
    target_state = {'version': source_state.get('version', '1.0'), 'status': 'pending', 'chunks': {}, 'events': []}
    for idx in range(1, target_chunk):
        key = f'{idx:06d}'
        chunk = src / 'original_ko_chunks' / f'original_ko_chunk_{idx:06d}_zh.txt'
        entry = dict(source_state.get('chunks', {}).get(key, {}))
        if entry.get('status') not in {'success', 'pass_with_warning'} or not chunk.exists() or not chunk.read_text(encoding='utf-8').strip():
            missing.append(idx); continue
        out_dir = dst / 'original_ko_chunks'; out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / chunk.name; shutil.copy2(chunk, out)
        entry['output_path'] = str(out)
        target_state['chunks'][key] = entry
        copied.append(idx)
    target_state['resume_seed'] = {'source_stage': source_stage, 'target_chunk': target_chunk, 'copied_chunks': copied}
    (dst / 'original_ko_resume_state.json').write_text(json.dumps(target_state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return CanaryResumePlan(source_stage, target_stage, target_chunk, tuple(copied), tuple(missing), not missing)
