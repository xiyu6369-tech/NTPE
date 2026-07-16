from __future__ import annotations

import re
from typing import Mapping

from .models import ExtractedSemanticFeatures
from .validation import normalize, sha256_text

NUMBER_RE = re.compile(r"(?<![A-Za-z])(?:\d+(?:\.\d+)?(?:天|日|年|月|歲|次|個|人|點|分|秒|%|％)?|[零〇一二兩三四五六七八九十百千萬億幾數多]+(?:天|日|年|月|歲|次|個|人|點|分|秒|%|％)?)")
TIME_RE = re.compile(r"(?:昨天|今天|明天|前天|後天|之前|之後|同時|稍後|\d{1,4}[年/-]\d{1,2}(?:[月/-]\d{1,2}日?)?|[零一二三四五六七八九十]+(?:年|月|日|點|分))")
NEGATIONS = ("不可能", "不能", "不得", "不必", "沒有", "未", "不")
MODALITIES = ("一定", "必須", "應該", "可能", "似乎", "或許", "大概", "可以")
CAUSAL = ("因為", "所以", "因此", "由於", "導致", "為了", "如果", "若", "雖然", "但是")
ORDER = ("首先", "然後", "接著", "最後", "之前", "之後", "同時", "先", "再")
AMBIGUITY = ("某人", "那個人", "對方", "幾", "數", "多個", "似乎", "或許", "大概", "可能")
SURNAME = "趙錢孫李周吳鄭王馮陳褚衛蔣沈韓楊朱秦尤許何呂施張孔曹嚴華金魏陶姜戚謝鄒喻柏水竇章雲蘇潘葛范彭郎魯韋昌馬苗鳳花方俞任袁柳鮑史唐費廉岑薛雷賀倪湯滕殷羅畢郝鄔安常樂于時傅皮卞齊康伍余元顧孟黃和穆蕭尹姚邵汪祁毛禹狄米貝明臧計伏成戴宋茅龐熊紀舒屈項祝董梁杜阮藍閔席季麻強賈路婁危江童顏郭梅盛林刁鍾徐邱駱高夏蔡田樊胡凌霍虞萬支柯昝管盧莫房裘繆解應宗丁宣賁鄧郁單杭洪包諸左石崔吉龔程嵇邢裴陸榮翁荀羊惠甄曲家封芮羿儲靳汲邴糜松井段富巫烏焦巴弓牧隗山谷車侯宓蓬全郗班仰秋仲伊宮寧仇欒暴甘鈄厲戎祖武符劉景詹束龍葉幸司韶黎喬蒼雙聞莘黨翟譚貢勞逄姬申扶堵冉宰酈雍璩桑桂濮牛壽通邊扈燕冀郟浦尚農溫別莊晏柴瞿閻充慕連茹習宦艾魚容向古易慎戈廖庾終暨居衡步都耿滿弘匡國文寇廣祿闕東歐殳沃利蔚越夔隆師鞏厙聶晁勾敖融冷訾辛闞那簡饒空曾毋沙乜養鞠須豐巢關蒯相查后荊紅游竺權逯蓋益桓公"
NAME_RE = re.compile(rf"(?<![\u4e00-\u9fff])[{SURNAME}][\u4e00-\u9fff]{{1,2}}(?![\u4e00-\u9fff])")


def _ordered(patterns, text):
    return tuple(x for _, x in sorted((text.find(x), x) for x in patterns if x in text))


def extract_semantic_features(text: str, *, glossary: Mapping[str, str] | None = None) -> ExtractedSemanticFeatures:
    value = normalize(text)
    dialogues = tuple(m.group(1) for m in re.finditer(r"[「『](.*?)[」』]", value, re.DOTALL))
    residues = tuple(sorted(set(re.findall(r"[가-힣]+|[ぁ-んァ-ヶ]+|[A-Za-z]{3,}", value))))
    return ExtractedSemanticFeatures(
        text_hash=sha256_text(value), names=tuple(sorted(set(NAME_RE.findall(value)))),
        numbers=tuple(NUMBER_RE.findall(value)), times=tuple(TIME_RE.findall(value)),
        negations=_ordered(NEGATIONS, value), modalities=_ordered(MODALITIES, value),
        causal_markers=_ordered(CAUSAL, value), order_markers=_ordered(ORDER, value),
        dialogue_spans=dialogues, paragraphs=tuple(value.splitlines()) if value else (),
        glossary_terms=tuple(sorted(k for k, approved in (glossary or {}).items() if approved in value)),
        ambiguity_markers=_ordered(AMBIGUITY, value), source_language_residue=residues,
        target_script_consistent=not bool(re.search(r"[\u4e00-\u9fff]", value)) or not bool(re.search(r"[\u4e00-\u9fff][가-힣ぁ-んァ-ヶ]", value)),
    )
