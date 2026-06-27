import re
from dataclasses import dataclass, field
from typing import List

from core.glossary import Glossary


@dataclass
class ValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)


class Validator:
    def __init__(self, glossary: Glossary):
        self.glossary = glossary
        self.forbidden_phrases = [
            "很抱歉",
            "無法協助",
            "不能提供",
            "作為AI",
            "作為一個AI",
            "以下是翻譯",
            "翻譯如下",
        ]
        self.bad_name_patterns = ["正太義", "鄭太義", "鄭泰意", "卡爾"]
        self.inference_markers = [
            "他知道那個男人是個種族主義者",
            "對亞洲人有很深的偏見",
            "他的眼睛似乎能看透一切",
            "繼續自己的生活",
        ]

    def validate(self, source: str, translated: str) -> ValidationResult:
        errors: List[str] = []
        clean = translated.strip()

        if not clean:
            errors.append("譯文為空")

        for phrase in self.forbidden_phrases:
            if phrase in clean:
                errors.append(f"出現AI說明/拒答：{phrase}")

        for bad in self.bad_name_patterns:
            if bad in clean:
                errors.append(f"出現錯誤譯名：{bad}")

        korean_count = len(re.findall(r"[가-힣]", clean))
        if korean_count >= 10:
            errors.append(f"韓文殘留過多：{korean_count}")

        if len(clean) < max(80, len(source) * 0.35):
            errors.append("譯文長度過短，疑似摘要或漏翻")

        lines = [x.strip() for x in clean.splitlines() if x.strip()]
        if len(lines) >= 6 and len(lines) - len(set(lines)) >= 3:
            errors.append("重複段落過多")

        for marker in self.inference_markers:
            if marker in clean:
                errors.append(f"疑似新增推論內容：{marker}")

        errors.extend(self.glossary.check_required_terms(source, clean))
        return ValidationResult(ok=not errors, errors=errors)
