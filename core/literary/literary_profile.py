from __future__ import annotations


def normalize_profile(profile: str | None) -> str:
    value = (profile or "literary").lower().strip()
    aliases = {"novel": "literary", "quality": "premium"}
    return aliases.get(value, value)


def profile_guidance(profile: str | None) -> str:
    profile = normalize_profile(profile)
    if profile == "fast":
        return "快譯；人名與劇情必須正確。"
    if profile == "balanced":
        return "速度與品質平衡；主詞清楚、中文自然。"
    if profile == "premium":
        return "品質優先；細緻處理語氣與節奏，不增刪劇情。"
    return "文學模式；主詞清楚、角色一致、中文像小說正文。"
