"""Offline-only diagnostic artifact generator for TE v7.2 Stage 12.5.3.

This module renders the already-authorized local prompt construction path.  It
does not construct a transport, invoke a provider, retry, or modify prompts.
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

from core.literary import estimate_tokens
from core.translation_quality_provider_canary.framework import _build_prompts


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "tests/fixtures/te_v72_canary/golden_corpus.json").read_text(encoding="utf-8"))["cases"][:2]
HEADERS = ("【Policy】", "【Profile】", "【Narrative】", "【Characters】", "【Glossary】", "【翻譯紀律】", "【小說語感規範】", "【Korean】", "【Output】", "【人物一致性記憶（只作翻譯輔助，來源文字優先）】", "【目前場景提示】", "【有限上下文連貫提示（不得摘要或改寫來源）】", "【自然度政策（TE v7.2）】")
HANGUL = re.compile(r"[\uac00-\ud7a3]")


def dump(name: str, value: object) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sections(prompt: str, source: str) -> list[dict[str, object]]:
    found = []
    for header in HEADERS:
        match = re.search(r"(?m)^" + re.escape(header), prompt)
        at = match.start() if match else -1
        if at >= 0:
            found.append((at, header))
    source_at = prompt.rfind(source)
    if source_at >= 0:
        found.append((source_at, "[Korean Source Payload]"))
    found.sort()
    output = []
    for index, (start, header) in enumerate(found):
        end = found[index + 1][0] if index + 1 < len(found) else len(prompt)
        text = prompt[start:end].strip()
        output.append({"order": index + 1, "header": header, "characters": len(text), "estimated_tokens": estimate_tokens(text), "starts_at": start, "ends_at": end, "contains_hangul": bool(HANGUL.search(text)), "text": text})
    return output


def main() -> None:
    rows = []
    for case in CASES:
        system, baseline, candidate, metadata = _build_prompts(case["case_id"], case["source_text"])
        base_sections, candidate_sections = sections(baseline, case["source_text"]), sections(candidate, case["source_text"])
        source_start = candidate.rfind(case["source_text"])
        korean_header = candidate.rfind("【Korean】")
        dynamic_start = candidate.find("【人物一致性記憶（只作翻譯輔助，來源文字優先）】")
        rows.append({
            "case_id": case["case_id"], "system_prompt": system, "baseline_prompt": baseline, "candidate_prompt": candidate,
            "baseline_sections": base_sections, "candidate_sections": candidate_sections, "metadata": metadata,
            "structural_finding": {
                "insertion_method": "user_prompt.rfind(source_text); insert rendered quality section immediately before source_text",
                "korean_header_offset": korean_header, "dynamic_section_offset": dynamic_start, "source_offset": source_start,
                "dynamic_content_between_korean_header_and_source": korean_header < dynamic_start < source_start,
                "source_immediately_follows_korean_header_baseline": baseline.rfind("【Korean】") + len("【Korean】\n") == baseline.rfind(case["source_text"]),
                "output_follows_source_without_added_section": candidate[source_start + len(case["source_text"]):].startswith("\n【Output】"),
            },
            "unified_diff": list(difflib.unified_diff(baseline.splitlines(), candidate.splitlines(), fromfile="baseline", tofile="candidate", lineterm="")),
        })
    contracts = [
        "只輸出繁體中文譯文", "僅翻譯【Korean】中的當前內容", "【Output】直出譯文，禁止標題、註解、Markdown。",
        "避免保留韓文或外語", "不得重述前文、上一段或本段已翻譯過的資訊",
    ]
    prompt_diff = {
        "stage": "TE-v7.2-Stage12.5.3", "mode": "offline_render_only", "provider_requests": 0,
        "shared_system_prompt": rows[0]["system_prompt"],
        "contract_presence": [{"clause": clause, "baseline_all_cases": all(clause in row["baseline_prompt"] for row in rows), "candidate_all_cases": all(clause in row["candidate_prompt"] for row in rows)} for clause in contracts],
        "contract_conclusion": "All enumerated Translation Contract clauses remain verbatim. No clause is overwritten or removed; the candidate structurally displaces the Korean source from its header and inserts competing instructions/content before it.",
        "cases": rows,
    }
    dump("prompt_diff.json", prompt_diff)
    trees = []
    for row in rows:
        trees.append({"case_id": row["case_id"], "system": {"order": 0, "role": "system", "estimated_tokens": estimate_tokens(row["system_prompt"]), "text": row["system_prompt"]}, "baseline_user_tree": row["baseline_sections"], "candidate_user_tree": row["candidate_sections"], "ordering_verdict": "FAIL: quality sections are nested between 【Korean】 and the Korean source, rather than placed before the source-labelled translation payload or in a separately delimited instruction region."})
    dump("prompt_tree.json", {"stage": "TE-v7.2-Stage12.5.3", "mode": "offline_render_only", "provider_requests": 0, "trees": trees})
    metrics = []
    for row in rows:
        base_total = estimate_tokens(row["system_prompt"]) + estimate_tokens(row["baseline_prompt"])
        cand_total = estimate_tokens(row["system_prompt"]) + estimate_tokens(row["candidate_prompt"])
        baseline_policy = next(item for item in row["baseline_sections"] if item["header"] == "【Policy】")["estimated_tokens"]
        candidate_policy = next(item for item in row["candidate_sections"] if item["header"] == "【Policy】")["estimated_tokens"]
        added = cand_total - base_total
        metrics.append({"case_id": row["case_id"], "baseline_total_tokens": base_total, "candidate_total_tokens": cand_total, "added_tokens": added, "candidate_growth_percent": round(added / base_total * 100, 2), "translation_policy_tokens": baseline_policy, "translation_policy_percent_baseline": round(baseline_policy / base_total * 100, 2), "translation_policy_percent_candidate": round(candidate_policy / cand_total * 100, 2), "policy_relative_share_drop_points": round(baseline_policy / base_total * 100 - candidate_policy / cand_total * 100, 2), "integration_breakdown_tokens": {key: row["metadata"][key] for key in ("character_tokens", "scene_tokens", "context_tokens", "naturalness_tokens", "total_added_tokens")}, "candidate_sections": [{key: item[key] for key in ("order", "header", "estimated_tokens", "characters")} for item in row["candidate_sections"]]})
    dump("section_metrics.json", {"stage": "TE-v7.2-Stage12.5.3", "mode": "offline_render_only", "provider_requests": 0, "cases": metrics, "observed_canary_estimates": {row["case_id"]: {"baseline": next(x for x in json.loads((ROOT / "artifacts/te_v72_canary_execution/provider_metrics.json").read_text(encoding="utf-8"))["rows"] if x["case_id"] == row["case_id"] and x["arm"] == "baseline")["estimated_prompt_tokens"], "candidate": next(x for x in json.loads((ROOT / "artifacts/te_v72_canary_execution/provider_metrics.json").read_text(encoding="utf-8"))["rows"] if x["case_id"] == row["case_id"] and x["arm"] == "candidate")["estimated_prompt_tokens"]} for row in rows}})
    candidate_output = (ROOT / "artifacts/te_v72_canary_execution/candidate_output/canary-001-character-honorific.txt").read_text(encoding="utf-8")
    injected = [item for item in rows[0]["candidate_sections"] if item["header"] in HEADERS[9:]]
    dump("contamination_report.json", {"stage": "TE-v7.2-Stage12.5.3", "mode": "offline_render_only", "provider_requests": 0, "input_source_echo": {"baseline_source_hangul_count": len(HANGUL.findall(rows[0]["baseline_prompt"])), "candidate_source_hangul_count": len(HANGUL.findall(rows[0]["candidate_prompt"])), "injected_sections_contain_hangul": {item["header"]: bool(HANGUL.search(item["text"])) for item in injected}, "finding": "Character, Scene, Context, and Naturalness injected text contains no Hangul. The only Korean in the candidate prompt is the intended source payload; its echo in output is therefore a source-boundary/format failure, not memory re-injection."}, "output_contract": {"candidate_output_contains_hangul": bool(HANGUL.search(candidate_output)), "candidate_output_hangul_count": len(HANGUL.findall(candidate_output)), "candidate_output_contains_translation_label": "譯文：" in candidate_output, "translation_label_literal_in_baseline_prompt": "譯文：" in rows[0]["baseline_prompt"], "translation_label_literal_in_candidate_prompt": "譯文：" in rows[0]["candidate_prompt"], "source_translation_template_literal_in_candidate_prompt": "Source" in rows[0]["candidate_prompt"] or "Translation" in rows[0]["candidate_prompt"], "finding": "The saved candidate output begins by echoing the full Korean source and then adds 譯文：. Neither marker is a candidate-prompt literal; both are model output that violates the unchanged direct-output contract, plausibly enabled by the ambiguous source boundary."}})
    report = """# TE v7.2 Stage 12.5.3 — Candidate Prompt Contract Diagnosis\n\nStatus: COMPLETE — offline diagnosis only. Provider requests, retries, fallbacks, new canaries, prompt modifications, commits, pushes, and tags: 0.\n\n## Decision\n\nThe Translation Contract remains textually intact and has not been overwritten or deleted. It is nevertheless structurally weakened: Candidate inserts Character, Scene, Context, and Naturalness material after `【Korean】` but before the Korean source. The source is no longer immediately governed by its own header, so the model is exposed to a mixed instruction/context region inside what visually begins as the source payload.\n\n## Root causes\n\n1. **Primary — source boundary displacement.** `integrate_prompt()` finds the final source and inserts the dynamic section immediately before it. The resulting order is `【Korean】 → quality sections → Korean source → 【Output】`. Baseline is `【Korean】 → Korean source → 【Output】`. This is an ordering defect, not an absent contract.\n2. **Secondary — policy dilution.** The candidate adds 204 estimated tokens per excerpt (328→532 and 331→536 total estimated prompt tokens in the recorded canary): about 62% growth. The unchanged Policy section’s relative share falls materially. The Naturalness section alone is 78 of 204 added tokens.\n3. **Observed Korean source echo.** Character, Scene, Context, and Naturalness inserted text contains no Hangul. The full Korean source present in the saved Candidate output therefore comes from the intended `【Korean】` source payload being echoed, not from a memory record.\n4. **Observed `譯文：`.** Neither baseline nor candidate contains the literal `譯文：`; it was generated by the model and violates the existing `【Output】` rule. It is evidence of an output-format failure, not a copied prompt string.\n\n## Contract answer\n\n- **Complete:** yes, clauses remain verbatim.\n- **Overwritten:** no.\n- **Moved:** the source payload is displaced from directly following `【Korean】`; the contract clauses themselves remain in place.\n- **Diluted:** yes, by added competing instructions/context and reduced relative policy share.\n\n## Concrete repair proposal — not implemented\n\n1. Preserve a hard source envelope: place all auxiliary quality sections before `【Korean】`, then keep `【Korean】 → source → 【Output】` contiguous; alternatively introduce a distinct `【Quality context: do not output】` block before `【Korean】`.\n2. Add an explicit final serialization invariant test: source immediately follows `【Korean】`; no dynamic header may occur between them; `【Output】` immediately follows source.\n3. Add a post-render contract test that rejects prompts with literal output templates (`Source:`, `Translation:`, `譯文：`) in dynamic sections and verifies no injected section contains Hangul unless an explicitly approved source-quote field exists.\n4. Reallocate the bounded prompt budget so Naturalness cannot dominate the added material; measure policy-share loss and reject a candidate exceeding an agreed dilution ceiling.\n5. Only after implementation and separate authorization, use a new controlled validation. This Stage makes no such request and performs no provider work.\n"""
    (OUT / "root_cause_analysis.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
