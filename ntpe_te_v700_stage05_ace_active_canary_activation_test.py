from __future__ import annotations
import os,tempfile
from pathlib import Path
from core.adaptive_context_canary import apply_prompt_package_canary, clear_canary_records, canary_records, build_canary_report

def package(index:int,tail:str)->dict[str,object]:
    return {"package_id":f"p{index}","session":{"chunk_index":index},"context":{"previous_chunk_tail":tail},"prompt":{"user_prompt":f"前文：\n{tail}\n待翻譯："}}
def main()->int:
    old=dict(os.environ)
    try:
        os.environ["NTPE_TE_V7_ACE_MODE"]="canary";os.environ["NTPE_TE_V7_ACE_CANARY_CHUNK"]="2";os.environ["NTPE_TE_V7_ACE_CANARY_CONTEXT_TOKENS"]="12";clear_canary_records()
        tail="他走進房間。窗外正在下雨。那封信仍放在桌上。沒有人知道他為何回來。"
        p1=package(1,tail);r1=apply_prompt_package_canary(p1);assert r1 and not r1.attempted
        p2=package(2,tail);before=p2["prompt"]["user_prompt"];r2=apply_prompt_package_canary(p2);assert r2 and r2.attempted and r2.activated and r2.estimated_tokens_saved>0;assert p2["prompt"]["user_prompt"]!=before
        p3=package(3,tail);r3=apply_prompt_package_canary(p3);assert r3 and not r3.attempted
        assert len([r for r in canary_records() if r.activated])==1
        bad=package(2,"沒有句號而且無法安全壓縮的內容");clear_canary_records();rb=apply_prompt_package_canary(bad);assert rb and rb.fallback_used and bad["context"]["previous_chunk_tail"]=="沒有句號而且無法安全壓縮的內容"
        report=build_canary_report();assert report["ready"] and report["provider_calls_added"]==0
        print("TE v7.0 Stage 05 ACE Active Canary Activation ALL PASS");return 0
    finally:
        os.environ.clear();os.environ.update(old);clear_canary_records()
if __name__=="__main__":raise SystemExit(main())
