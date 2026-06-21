"""
convert.py — Tarea de conversión DOCX/XLSX→PDF (ejecutada por el worker).

Envoltorio delgado: lee el archivo subido vía `storage`, delega la conversión a
`app.modules.list.converter` (Gotenberg) y guarda el PDF resultante vía `storage`.
Devuelve metadatos que el frontend usa para cargar el PDF en el editor.

Se encola por RUTA de string ("workers.tasks.convert.convert_document") desde el
service del módulo, de modo que `app/` no importa `workers/`.
"""
from __future__ import annotations

import logging
import uuid

from app import storage
from app.modules.list.converter import convert_office_to_pdf

logger = logging.getLogger("list.tasks.convert")

PDF_SUBDIR = "list/pdf"


def convert_document(rel_in: str, original_name: str) -> dict:
    """Convierte el archivo subido `rel_in` a PDF y lo guarda.

    Devuelve {"pdf_name", "pdf_url"}. El input se borra tras convertir.
    """
    src = storage.resolve(rel_in)
    if src is None:
        raise FileNotFoundError(f"Archivo de entrada no encontrado: {rel_in}")

    with open(src, "rb") as f:
        data = f.read()

    pdf_bytes = convert_office_to_pdf(data, original_name)

    pdf_name = f"{uuid.uuid4().hex}.pdf"
    storage.save_bytes(pdf_bytes, PDF_SUBDIR, pdf_name)

    # El archivo de entrada ya cumplió su propósito.
    storage.delete(rel_in)

    logger.info("convert_document OK: %s → %s", rel_in, pdf_name)
    return {"pdf_name": pdf_name, "pdf_url": f"/api/list/pdf/{pdf_name}"}
