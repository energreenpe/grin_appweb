"""
export.py — Tarea de estampado de campos/overlays sobre un PDF (worker).

Envoltorio delgado: lee el PDF base vía `storage`, delega el estampado a
`app.modules.list.pdf_stamp` (reportlab+pypdf) y guarda el resultado vía
`app.modules.list.output_store` (Redis, NO disco: ver ese módulo para el porqué).

Se encola por RUTA de string ("workers.tasks.export.stamp_document") desde el
service, de modo que `app/` no importa `workers/`.
"""
from __future__ import annotations

import logging
import uuid
from typing import List

from app import storage
from app.modules.list.pdf_stamp import stamp_pdf
from app.modules.list.output_store import save_output

logger = logging.getLogger("list.tasks.export")

PDF_SUBDIR = "list/pdf"


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
    save_output(output_name, out_bytes)

    logger.info("stamp_document OK: %s → %s", pdf_name, output_name)
    return {"output_name": output_name, "output_url": f"/api/list/output/{output_name}"}
