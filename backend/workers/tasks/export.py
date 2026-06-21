"""
export.py — Tarea de estampado de campos/overlays sobre un PDF (worker).

Envoltorio delgado: lee el PDF base vía `storage`, delega el estampado a
`app.modules.list.pdf_stamp` (reportlab+pypdf) y guarda el resultado vía `storage`.

Se encola por RUTA de string ("workers.tasks.export.stamp_document") desde el
service, de modo que `app/` no importa `workers/`.
"""
from __future__ import annotations

import logging
import uuid
from typing import List

from app import storage
from app.modules.list.pdf_stamp import stamp_pdf

logger = logging.getLogger("list.tasks.export")

PDF_SUBDIR = "list/pdf"
OUTPUT_SUBDIR = "list/output"


def stamp_document(pdf_name: str, fields: List[dict], overlays: List[dict]) -> dict:
    """Estampa fields/overlays sobre el PDF base `pdf_name` y guarda el resultado.

    Devuelve {"output_name", "output_url"}.
    """
    src = storage.resolve(f"uploads/{PDF_SUBDIR}/{pdf_name}")
    if src is None:
        raise FileNotFoundError(f"PDF base no encontrado: {pdf_name}")

    with open(src, "rb") as fh:
        source_bytes = fh.read()

    out_bytes = stamp_pdf(source_bytes, fields, overlays)

    output_name = f"{uuid.uuid4().hex}.pdf"
    storage.save_bytes(out_bytes, OUTPUT_SUBDIR, output_name)

    logger.info("stamp_document OK: %s → %s", pdf_name, output_name)
    return {"output_name": output_name, "output_url": f"/api/list/output/{output_name}"}
