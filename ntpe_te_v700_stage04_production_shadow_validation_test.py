from __future__ import annotations
import hashlib, json, os
from pathlib import Path
import lts.txt_translation_runtime as runtime
from core.adaptive_context_runtime_shadow import clear_shadow_records, install_txt_runtime_shadow_hook, shadow_records
from core.adaptive_context_production_validation import build_production_shadow_report, production_shadow_session


def main() -> int:
    root = Path(__file__).resolve().parent
    old_now = runtime.now_iso
    try:
        runtime.now_iso = lambda: "2026-07-12T00:00:00+00:00"
        install_txt_runtime_shadow_hook()
        options = runtime.TxtTranslationOptions(input_path=root/'tests/literary/Golden_Set/original_ko.txt', output_dir=root/'output')
        with production_shadow_session():
            runtime.build_prompt_package(options=options, chunk_text='정태의는 창밖을 보았다.', chunk_index=1, chunk_total=1, locked_dictionary={'정태의':'鄭泰義'}, previous_context='일라이는 문가에 서 있었다.')
            report = build_production_shadow_report({'status':'success'}, provider_execution_requested=False)
        assert report.ready
        assert report.shadow_records == 1
        assert report.payload_equivalent_records == 1
        assert report.provider_calls_added == 0
        assert report.metadata['content_redacted'] is True
        assert '정태의' not in repr(report.to_dict())
        manifest = json.loads((root/'manifests/te_v700_stage04_production_shadow_validation_manifest.json').read_text(encoding='utf-8'))
        for name,digest in manifest['integrity']['files'].items():
            assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest, name
        for spec in manifest.get('mutable_artifacts', []):
            artifact_path = root / spec['path']
            payload = json.loads(artifact_path.read_text(encoding='utf-8'))
            assert payload.get('version') == spec['version'], spec['path']
            assert isinstance(payload.get('status'), str), spec['path']
            assert isinstance(payload.get('ready'), bool), spec['path']
            assert payload.get('execution_mode') == 'shadow', spec['path']
            if 'provider_calls_added' in payload:
                assert payload.get('provider_calls_added') == 0, spec['path']
            if 'metadata' in payload:
                assert payload.get('metadata', {}).get('content_redacted') is True, spec['path']
                assert payload.get('metadata', {}).get('prompt_payload_unchanged') is True, spec['path']
            else:
                assert payload.get('provider_execution_observed') is False, spec['path']
                assert payload.get('translation_quality_improvement_claimed') is False, spec['path']
                assert payload.get('provider_latency_improvement_claimed') is False, spec['path']
    finally:
        runtime.now_iso = old_now
        clear_shadow_records()
    print('TE v7.0 Stage 04 Production Shadow Validation ALL PASS')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
