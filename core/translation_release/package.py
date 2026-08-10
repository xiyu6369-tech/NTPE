from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.translation_release.models import DeliveryManifest, QualityCertificate, DeliveryResult


def write_txt_delivery(
    polished_text: str,
    output_dir: Path,
    novel_id: str,
) -> str:
    """Write primary TXT artifact."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{novel_id}_zh.txt"
    path.write_text(polished_text, encoding="utf-8")
    return str(path)


def write_json_delivery(
    obj: Any,
    output_dir: Path,
    novel_id: str,
    suffix: str,
) -> str:
    """Write JSON artifact (manifest or certificate)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{novel_id}_{suffix}.json"
    path.write_text(json.dumps(obj.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def write_delivery_package(
    *,
    polished_text: str,
    delivery_manifest: DeliveryManifest,
    quality_certificate: QualityCertificate,
    output_dir: Path,
    novel_id: str,
    formats: tuple[str, ...] = ("txt",),
) -> DeliveryResult:
    """
    Write all delivery artifacts to output_dir.

    Core artifacts (always):
    - {novel_id}_zh.txt                    # polished novel with metadata header
    - {novel_id}_delivery_manifest.json    # DeliveryManifest
    - {novel_id}_quality_certificate.json  # QualityCertificate

    Optional artifacts (if format in formats):
    - {novel_id}.epub                      # via epub_exporter
    - {novel_id}.pdf                       # via pdf_exporter

    Returns: DeliveryResult with all paths
    """
    # This function writes core artifacts only.
    # Exporters are handled by delivery_pipeline.py to maintain single DeliveryResult construction.
    txt_path = write_txt_delivery(polished_text, output_dir, novel_id)
    manifest_path = write_json_delivery(delivery_manifest, output_dir, novel_id, "delivery_manifest")
    qc_path = write_json_delivery(quality_certificate, output_dir, novel_id, "quality_certificate")

    return DeliveryResult(
        status="success",
        output_path=txt_path,
        manifest_path=manifest_path,
        qc_certificate_path=qc_path,
        epub_path=None,
        pdf_path=None,
        error=None,
    )