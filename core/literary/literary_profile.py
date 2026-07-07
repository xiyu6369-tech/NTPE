from __future__ import annotations


def normalize_profile(profile: str | None) -> str:
    value = (profile or "literary").lower().strip()
    aliases = {"novel": "literary", "quality": "premium"}
    return aliases.get(value, value)


def profile_guidance(profile: str | None) -> str:
    profile = normalize_profile(profile)
    if profile == "fast":
        return "速度優先，但仍必須保持人名與劇情正確；避免冗長潤飾。"
    if profile == "balanced":
        return "品質與速度平衡；保持自然中文與主詞正確。"
    if profile == "premium":
        return "品質優先；可更細緻處理語氣、節奏與長句，但不可增刪劇情。"
    return "文學翻譯預設模式；優先敘事自然、角色一致、主詞清楚與中文小說閱讀體驗。"
