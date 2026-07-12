from __future__ import annotations
import os
from core.adaptive_context_canary import apply_prompt_package_canary,clear_canary_records

def _p(i,tail):return {"package_id":str(i),"session":{"chunk_index":i},"context":{"previous_chunk_tail":tail},"prompt":{"user_prompt":"CTX\n"+tail+"\nSRC"}}
def test_single_chunk_canary_and_no_automatic_expansion(monkeypatch):
 monkeypatch.setenv("NTPE_TE_V7_ACE_MODE","canary");monkeypatch.setenv("NTPE_TE_V7_ACE_CANARY_CHUNK","2");monkeypatch.setenv("NTPE_TE_V7_ACE_CANARY_CONTEXT_TOKENS","8");clear_canary_records();tail="第一句。第二句。第三句。第四句。";r=apply_prompt_package_canary(_p(2,tail));assert r and r.activated;assert not apply_prompt_package_canary(_p(3,tail)).attempted
def test_ambiguous_prompt_falls_back(monkeypatch):
 monkeypatch.setenv("NTPE_TE_V7_ACE_MODE","canary");monkeypatch.setenv("NTPE_TE_V7_ACE_CANARY_CHUNK","2");clear_canary_records();p=_p(2,"第一句。第二句。");p["prompt"]["user_prompt"]="第一句。第二句。 / 第一句。第二句。";before=repr(p);r=apply_prompt_package_canary(p);assert r and r.fallback_used and repr(p)==before
