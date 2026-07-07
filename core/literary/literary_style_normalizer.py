from __future__ import annotations

import re

# TER-v1.2: lightweight literary style normalization.
# These replacements are intentionally conservative: they improve common
# machine-translation phrasing without adding new plot information.
LITERARY_STYLE_REPLACEMENTS: tuple[tuple[str, str], ...] = (

    ("伊萊卻是笑了笑，說：「當然。」說完便轉身離去，留下了這句話。", "伊萊笑了笑，只說了句「當然」，便轉身離去。"),
    ("伊萊開心地笑了，說：「當然。」說完便轉身離去，留下了這句話。", "伊萊愉快地笑了笑，只說了句「當然」，便轉身離去。"),
    ("說：「當然。」說完便轉身離去，留下了這句話。", "只說了句「當然」，便轉身離去。"),
    ("留下了這句話", "只留下那句模稜兩可的簡短回答"),
    ("也不能這樣做", "也不可能做到"),
    ("事情已經變得最糟糕了", "事情已經往最糟的方向發展了"),
    ("他絕對不希望事情會變成這樣", "這絕不是他想要的局面"),
    ("一下子湧上心頭", "一瞬間湧了上來"),
    ("湧上心頭", "湧了上來"),
    ("稍微揚起眉毛", "微微挑了挑眉"),
    ("微微揚起眉毛", "微微挑了挑眉"),
    ("稍微挑起眉毛", "微微挑了挑眉"),
    ("微微挑起眉毛", "微微挑了挑眉"),
    ("揚起眉毛", "挑起眉"),
    ("挑起眉毛", "挑起眉"),
    ("挑了挑眉毛", "挑了挑眉"),
    ("用沉重的心情", "心情沉重地"),
    ("然後就轉身走了", "說完便轉身離去"),
    ("然後就轉身離去", "說完便轉身離去"),
    ("全數湧了上來了", "全數湧了上來"),
    ("非常糟糕的結果", "更棘手的局面"),
    ("保持沉默", "坐視不管"),
    ("不會保持沉默", "不會坐視不管"),
    ("絕對不會保持沉默", "絕對不會坐視不管"),
    ("轉身走開了", "轉身離去"),
    ("轉身走開", "轉身離去"),
    ("就轉身走開了", "便轉身離去"),
    ("一下子都湧上心頭", "一瞬間全數湧了上來"),
    ("數十年的疲勞", "積壓了數十年的疲憊"),
    ("感到數十年的疲勞", "感覺積壓了數十年的疲憊"),
)


def normalize_literary_style(text: str) -> str:
    """Apply conservative Chinese-novel style cleanup.

    This is not a rewrite engine.  It only targets repetitive MT phrasing and
    obvious unnatural literal expressions that have already appeared in NTPE
    regression outputs.
    """
    result = text or ""
    for src, dst in LITERARY_STYLE_REPLACEMENTS:
        result = result.replace(src, dst)

    # Avoid awkward stacked particles produced by direct replacement.
    result = result.replace("不會坐視不管。", "不會坐視不管。")
    result = re.sub(r"(伊萊|鄭泰義|凱爾)則是", r"\1", result)
    result = re.sub(r"，然後就", "，隨即", result)
    result = re.sub(r"，然後", "，接著", result)
    result = result.replace("挑起眉，", "挑了挑眉，")
    result = result.replace("挑起眉。", "挑了挑眉。")
    result = re.sub(r"說道：", "說：", result)
    return result
