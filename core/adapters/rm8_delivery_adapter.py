from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.translation_release.delivery_pipeline import run_delivery_pipeline, DeliveryResult
from core.translation_release.models import DeliveryManifest, QualityCertificate
from lts.txt_translation_runtime import TxtTranslationOptions


@dataclass(frozen=True)
class DeliveryRequest:
    assembled_text: str
    translated_chunks: list[str]
    chunk_records: list[dict[str, Any]]
    locked_dictionary: dict[str, str]
    options: TxtTranslationOptions
    input_path: Path
    output_dir: Path


@dataclass(frozen=True)
class DeliveryAdapterResult:
    delivery_result: DeliveryResult
    manifest: DeliveryManifest | None
    quality_certificate: QualityCertificate | None
    epub_path: Path | None
    pdf_path: Path | None
    status: str
    error: str | None


class Rm8DeliveryAdapter:
    def __init__(self):
        pass

    def trigger_delivery(self, request: DeliveryRequest) -> DeliveryAdapterResult:
        try:
            delivery_result = run_delivery_pipeline(
                assembled_text=request.assembled_text,
                translated_chunks=request.translated_chunks,
                chunk_records=request.chunk_records,
                locked_dictionary=request.locked_dictionary,
                options=request.options,
                input_path=request.input_path,
                output_dir=request.output_dir,
            )

            if delivery_result.status == "failed":
                return DeliveryAdapterResult(
                    delivery_result=delivery_result,
                    manifest=None,
                    quality_certificate=None,
                    epub_path=None,
                    pdf_path=None,
                    status="failed",
                    error=delivery_result.error,
                )

            manifest = None
            quality_certificate = None
            if delivery_result.manifest_path:
                import json
                manifest = DeliveryManifest(**json.loads(Path(delivery_result.manifest_path).read_text(encoding="utf-8")))
            if delivery_result.qc_certificate_path:
                import json
                quality_certificate = QualityCertificate(**json.loads(Path(delivery_result.qc_certificate_path).read_text(encoding="utf-8")))

            epub_path = Path(delivery_result.epub_path) if delivery_result.epub_path else None
            pdf_path = Path(delivery_result.pdf_path) if delivery_result.pdf_path else None

            return DeliveryAdapterResult(
                delivery_result=delivery_result,
                manifest=manifest,
                quality_certificate=quality_certificate,
                epub_path=epub_path,
                pdf_path=pdf_path,
                status="success",
                error=None,
            )
        except Exception as e:
            return DeliveryAdapterResult(
                delivery_result=DeliveryResult(
                    status="failed",
                    output_path="",
                    manifest_path="",
                    qc_certificate_path="",
                    error=str(e),
                ),
                manifest=None,
                quality_certificate=None,
                epub_path=None,
                pdf_path=None,
                status="failed",
                error=str(e),
            )

    def is_delivery_enabled(self, options: TxtTranslationOptions) -> bool:
        return getattr(options, "quality_delivery_v83", False)

    def get_delivery_formats(self, options: TxtTranslationOptions) -> tuple[str, ...]:
        return getattr(options, "quality_delivery_formats_v83", ("txt",))