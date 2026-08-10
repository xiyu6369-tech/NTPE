from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from core.translation_release.models import DeliveryManifest, TOCEntry


class BaseExporter(ABC):
    format_name: str
    file_extension: str

    @abstractmethod
    def export(
        self,
        *,
        polished_text: str,
        manifest: DeliveryManifest,
        toc: list[TOCEntry],
        output_path: Path,
    ) -> bool:
        """Returns True on success, False on failure."""
        pass