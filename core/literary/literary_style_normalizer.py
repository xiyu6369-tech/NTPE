from __future__ import annotations

import re

# TER-v1.6: semantic-guarded literary normalization.
#
# The normalizer is intentionally conservative.  It may smooth recurring
# machine-translation phrasing, but it must not introduce new plot content or
# change who does what.  TER-v1.6 adds guards for the TER-v1.5 regressions:
# awkward "leaving someone an answer" structures and duplicated disappearance
# descriptions.
LITERARY_STYLE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    # Ambiguous reply / Ilay response handling.
    (
        "伊萊笑著回答道：「當然。」說完便轉身離去，只留下了一句模糊的話。",
        "伊萊笑著只答了一句「當然」，便轉身離去。那句簡短的回答，怎麼解讀都說得通。",
    ),
    (
        "伊萊笑著回答道：「當然。」說完便轉身離去，只留下那句曖昧不明的回答。",
        "伊萊笑著只答了一句「當然」，便轉身離去。那句簡短的回答，怎麼解讀都說得通。",
    ),
    (
        "伊萊笑著回答道：「當然。」說完便轉身離去，只留下那句曖昧不明的回答",
        "伊萊笑著只答了一句「當然」，便轉身離去。那句簡短的回答，怎麼解讀都說得通",
    ),
    ("伊萊笑著回答道：「當然。」", "伊萊笑著只答了一句「當然」。"),
    ("伊萊笑著說：「當然。」", "伊萊笑著只答了一句「當然」。"),
    ("伊萊輕笑著說：「當然。」說完便轉身離去，留下了鄭泰義一個簡短的回答。", "伊萊輕笑著只答了一句「當然」，便轉身離去。"),
    ("伊萊笑著回答道：「當然。」說完便轉身離去，留下了鄭泰義一個簡短的回答。", "伊萊笑著只答了一句「當然」，便轉身離去。"),
    ("留下了鄭泰義一個簡短的回答", "只留下那句簡短的回答"),
    ("留下了鄭泰義一個回答", "只留下那句回答"),
    ("只留下了一句模糊的話", "只留下那句曖昧不明的回答"),
    ("只留下了一句模糊的回答", "只留下那句曖昧不明的回答"),
    ("留下了一句模糊的話", "留下那句曖昧不明的回答"),
    ("留下了這句話", "只留下那句模稜兩可的簡短回答"),

    # Light literary phrasing fixes.
    ("抬了抬眉毛", "挑了挑眉"),
    ("抬起眉毛", "挑起眉"),
    ("抬了抬眉", "挑了挑眉"),
    ("事情已經變得最壞了", "事情已經糟到不能再糟"),
    ("事情已經變得最糟了", "事情已經糟到不能再糟"),
    ("事情已經變得最糟糕了", "事情已經糟到不能再糟"),
    ("最壞的狀況", "最糟的局面"),
    ("最壞的局面", "最糟的局面"),
    ("完全消失在視線中", "徹底消失在視線裡"),
    ("消失在視線中", "消失在視線裡"),
    ("他感到積壓了數十年的疲憊", "積壓了數十年的疲憊彷彿"),
    ("如果他堅持拒絕，伊萊可能會採取極端的措施", "如果他堅持拒絕，伊萊未必不會使出更極端的手段"),
    ("伊萊卻是笑了笑，說：「當然。」說完便轉身離去，留下了這句話。", "伊萊笑了笑，只說了句「當然」，便轉身離去。"),
    ("伊萊開心地笑了，說：「當然。」說完便轉身離去，留下了這句話。", "伊萊愉快地笑了笑，只說了句「當然」，便轉身離去。"),
    ("說：「當然。」說完便轉身離去，留下了這句話。", "只說了句「當然」，便轉身離去。"),
    ("也不能這樣做", "也不可能做到"),
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


def _normalize_ambiguous_reply(text: str) -> str:
    """Repair common mistranslations around `只答一句「當然」`.

    The Korean source implies that Ilay leaves only a short answer behind, not
    that he gives an answer *to Jeong Tae-ui as an object*.  This guard avoids
    the TER-v1.5 regression `留下了鄭泰義一個簡短的回答`.
    """
    result = text
    result = re.sub(
        r"伊萊([^。]{0,14})說[：:]「當然。」說完便轉身離去，只留下那句[^。]{0,12}回答。",
        r"伊萊\1只答了一句「當然」，便轉身離去。",
        result,
    )
    result = re.sub(
        r"伊萊([^。]{0,14})說[：:]「當然。」說完便轉身離去，留下了鄭泰義一個[^。]{0,12}回答。",
        r"伊萊\1只答了一句「當然」，便轉身離去。",
        result,
    )
    result = re.sub(
        r"伊萊([^。]{0,14})回答道[：:]「當然。」說完便轉身離去，留下了鄭泰義一個[^。]{0,12}回答。",
        r"伊萊\1只答了一句「當然」，便轉身離去。",
        result,
    )
    return result


def _dedupe_disappearance_sentences(text: str) -> str:
    """Remove duplicate consecutive disappearance descriptions.

    Example regression:
    `直到伊萊轉過彎角...消失為止。等伊萊徹底消失在視線裡...`
    The second sentence repeats the same event and should be collapsed.
    """
    result = text
    patterns = [
        (
            r"鄭泰義站在原地，直到伊萊轉過彎角，徹底消失在視線裡為止。等伊萊徹底消失在視線裡，鄭泰義就靠在牆上，滑坐在地上。",
            "鄭泰義站在原地，直到伊萊轉過彎角、徹底消失在視線裡，才靠在牆上，滑坐在地上。",
        ),
        (
            r"鄭泰義站在原地，直到伊萊從視線裡消失為止。等伊萊徹底消失在視線裡，鄭泰義就靠在牆上，滑坐在地上。",
            "鄭泰義站在原地，直到伊萊徹底消失在視線裡，才靠在牆上，滑坐在地上。",
        ),
        (
            r"鄭泰義就站在那裡，直到伊萊轉過彎角，徹底消失在視線裡為止。等伊萊徹底消失在視線裡，鄭泰義就靠在牆上，滑坐在地上。",
            "鄭泰義就站在那裡，直到伊萊轉過彎角、徹底消失在視線裡，才靠在牆上，滑坐在地上。",
        ),
    ]
    for src, dst in patterns:
        result = re.sub(src, dst, result)

    # Generic fallback for adjacent sentences that both mention Ilay disappearing
    # from sight and Jeong Tae-ui sliding down the wall.
    result = re.sub(
        r"鄭泰義([^。]{0,40})直到伊萊([^。]{0,30})消失在視線裡為止。等伊萊徹底消失在視線裡，鄭泰義([^。]{0,20})靠在牆上，滑坐在地上。",
        r"鄭泰義\1直到伊萊\2徹底消失在視線裡，才\3靠在牆上，滑坐在地上。",
        result,
    )
    return result


def normalize_literary_style(text: str) -> str:
    """Apply conservative Chinese-novel style cleanup.

    This is not a rewrite engine. It targets known MT phrasing, then applies
    semantic guards that prevent cleanup from creating wrong or duplicated
    meaning.
    """
    result = text or ""
    for src, dst in LITERARY_STYLE_REPLACEMENTS:
        result = result.replace(src, dst)

    # TER-v1.6 semantic guards.
    result = _normalize_ambiguous_reply(result)
    result = _dedupe_disappearance_sentences(result)

    # Avoid awkward stacked particles produced by direct replacement.
    result = re.sub(r"(伊萊|鄭泰義|凱爾)則是", r"\1", result)
    result = re.sub(r"，然後就", "，隨即", result)
    result = re.sub(r"，然後", "，接著", result)
    result = result.replace("挑起眉，", "挑了挑眉，")
    result = result.replace("挑起眉。", "挑了挑眉。")
    result = re.sub(r"說道：", "說：", result)
    result = result.replace("全數湧了上來了", "全數湧了上來")
    result = result.replace("湧了上來了", "湧了上來")
    result = result.replace("糟到不能再糟了", "糟到不能再糟")
    result = result.replace("挑了挑眉毛", "挑了挑眉")
    result = result.replace("挑起眉毛", "挑起眉")
    result = result.replace("抬了抬眉毛", "挑了挑眉")
    return result
