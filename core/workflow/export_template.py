# =====================================================
# NTPE 1.2 Professional
# Stage-17.5 Export Framework
# =====================================================

from dataclasses import dataclass


@dataclass(frozen=True)
class ExportTemplate:
    header: str = ""
    footer: str = ""

    def render(self, content: str) -> str:
        parts = []
        if self.header:
            parts.append(self.header.rstrip())
        parts.append(content.strip() if content else "")
        if self.footer:
            parts.append(self.footer.lstrip())
        return "\n\n".join(part for part in parts if part != "")
