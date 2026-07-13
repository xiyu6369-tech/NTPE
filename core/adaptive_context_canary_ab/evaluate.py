from __future__ import annotations
from .model import QualityEvidence, CanaryABReport
VERSION='7.0.0-stage07.5'
_OMISSION=('OMISSION','漏段','漏譯','PARAGRAPH_OMISSION')
_UNSUPPORTED=('UNSUPPORTED','ADDED_DETAIL','不支持','新增原文未支持')

def _risk(issue: str, needles: tuple[str,...]) -> bool:
    value=issue.upper()
    return any(n.upper() in value for n in needles)

def evaluate_canary_ab(baseline: QualityEvidence, canary: QualityEvidence) -> CanaryABReport:
    blockers=[]; limitations=[]
    if baseline.chunk != canary.chunk: blockers.append('target-chunk-mismatch')
    if not baseline.source_hash or baseline.source_hash != canary.source_hash: blockers.append('source-hash-mismatch')
    if not baseline.provider_complete: blockers.append('baseline-provider-incomplete')
    if not canary.provider_complete: blockers.append('canary-provider-incomplete')
    if not baseline.accepted: blockers.append('baseline-not-accepted')
    if not canary.accepted: blockers.append('canary-not-accepted')
    if canary.score < baseline.score: blockers.append('quality-score-regression')
    base=set(baseline.issues); new=tuple(i for i in canary.issues if i not in base)
    if any(_risk(i,_OMISSION) for i in new): blockers.append('new-omission-issue')
    if any(_risk(i,_UNSUPPORTED) for i in new): blockers.append('new-unsupported-detail-issue')
    if canary.translated_paragraphs < baseline.translated_paragraphs: blockers.append('paragraph-coverage-regression')
    if baseline.length_ratio > 0 and canary.length_ratio + 0.05 < baseline.length_ratio: blockers.append('length-coverage-regression')
    if canary.translated_chars < max(1, int(baseline.translated_chars * 0.90)): blockers.append('translated-length-regression')
    ready=not blockers
    return CanaryABReport(VERSION,'pass' if ready else 'fail',ready,baseline.chunk,baseline.stage,canary.stage,
        baseline.score,canary.score,baseline.accepted,canary.accepted,new,tuple(dict.fromkeys(blockers)),tuple(limitations),{
            'content_redacted':True,'same_source_required':True,'canary_must_be_accepted':True,
            'quality_score_non_regression':True,'omission_non_regression':True,
            'unsupported_detail_non_regression':True,'automatic_active_expansion':False,
            'translation_quality_improvement_claimed':False,
        })
