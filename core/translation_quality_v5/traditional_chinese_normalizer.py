from __future__ import annotations

import re
import unicodedata
from typing import Any, Callable, Dict, Mapping, Optional


Converter = Callable[[str], str]


class TraditionalChineseNormalizer:
    """Conservative Traditional Chinese normalizer.

    A caller may inject a full OpenCC-compatible converter. Without one, the
    class performs only safe punctuation, Unicode, and common-character fixes.
    """

    version = "TE-v5.0"
    stage = "5.0.4"

    _COMMON_MAP = str.maketrans({
        "这": "這", "个": "個", "们": "們", "为": "為", "说": "說",
        "对": "對", "后": "後", "里": "裡", "来": "來", "时": "時",
        "会": "會", "发": "發", "过": "過", "还": "還", "没": "沒",
        "从": "從", "问": "問", "听": "聽", "见": "見", "开": "開",
        "关": "關", "东": "東", "书": "書", "长": "長", "门": "門",
        "间": "間", "头": "頭", "脸": "臉", "让": "讓", "现": "現",
        "实": "實", "样": "樣", "话": "話", "应": "應", "该": "該",
        "经": "經", "觉": "覺", "气": "氣", "爱": "愛", "边": "邊",
        "远": "遠", "进": "進", "动": "動", "亲": "親", "无": "無",
    })

    def normalize(
        self,
        text: Optional[str],
        *,
        converter: Optional[Converter] = None,
        config: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        original = str(text or "")
        cfg = dict(config or {})
        normalized = unicodedata.normalize("NFC", original)

        if callable(converter):
            normalized = str(converter(normalized))
            conversion_mode = "injected_converter"
        else:
            normalized = normalized.translate(self._COMMON_MAP)
            conversion_mode = "conservative_builtin"

        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
        normalized = normalized.replace("“", "「").replace("”", "」")
        normalized = normalized.replace("‘", "『").replace("’", "』")
        normalized = re.sub(r"[ \t]+\n", "\n", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        normalized = re.sub(r"[ \t]{2,}", " ", normalized)

        if cfg.get("normalize_ellipsis", True):
            normalized = normalized.replace("......", "……")
            normalized = normalized.replace("...", "……")

        changed = normalized != original
        simplified_residue = self._simplified_residue(normalized)

        return {
            "status": "normalized",
            "stage": self.stage,
            "changed": changed,
            "conversion_mode": conversion_mode,
            "normalized_text": normalized,
            "simplified_residue": simplified_residue,
            "simplified_residue_count": len(simplified_residue),
            "source_text_retained": False,
        }

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "status", "stage", "changed", "conversion_mode",
            "normalized_text", "simplified_residue",
            "simplified_residue_count", "source_text_retained"
        }
        return (
            required.issubset(result)
            and result.get("stage") == self.stage
            and result.get("source_text_retained") is False
            and result.get("simplified_residue_count")
            == len(result.get("simplified_residue", []))
        )

    @staticmethod
    def _simplified_residue(text: str) -> list[str]:
        suspects = "这们为说对后里来时会发过还没从问听见开关东书长门间头脸让现实样话应该经觉气爱边远进动亲无"
        return sorted({ch for ch in text if ch in suspects})
