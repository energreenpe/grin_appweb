"""
converter.py — Conversión DOCX/XLSX → PDF vía Gotenberg.

Gotenberg es un contenedor que incluye LibreOffice. NO ejecutamos `soffice` aquí:
hacemos POST HTTP al endpoint LibreOffice de Gotenberg y recibimos el PDF. Esto saca
de nuestro código toda la gestión de subprocess, perfiles aislados y concurrencia.

Función PURA (sin FastAPI ni Redis). La invoca el worker (`workers/tasks/convert.py`).
"""
from __future__ import annotations

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger("list.converter")

# Extensiones que requieren conversión. El .pdf no pasa por aquí (atajo en service).
CONVERTIBLE_EXTENSIONS = {".docx", ".xlsx"}

# Ruta del endpoint de conversión Office de Gotenberg.
_LIBREOFFICE_ROUTE = "/forms/libreoffice/convert"

# Timeout amplio: cubre archivos Office grandes. Gotenberg tiene además el suyo propio.
_CONVERT_TIMEOUT_S = 120.0


class ConversionError(Exception):
    """Falla de conversión (Gotenberg inaccesible o respondió con error)."""


def convert_office_to_pdf(data: bytes, filename: str) -> bytes:
    """Convierte los bytes de un DOCX/XLSX a PDF usando Gotenberg.

    `filename` debe conservar su extensión: Gotenberg la usa para decidir cómo
    convertir. Devuelve los bytes del PDF resultante.
    """
    settings = get_settings()
    url = settings.gotenberg_url.rstrip("/") + _LIBREOFFICE_ROUTE
    files = {"files": (filename, data)}

    logger.info("Gotenberg: convirtiendo %s (%d bytes) → %s", filename, len(data), url)
    try:
        resp = httpx.post(url, files=files, timeout=_CONVERT_TIMEOUT_S)
    except httpx.HTTPError as e:
        raise ConversionError(f"No se pudo contactar a Gotenberg: {e}") from e

    if resp.status_code != 200:
        raise ConversionError(
            f"Gotenberg devolvió HTTP {resp.status_code}: {resp.text[:500]}"
        )

    if not resp.content:
        raise ConversionError("Gotenberg devolvió un PDF vacío.")

    logger.info("Gotenberg: conversión OK de %s (%d bytes PDF)", filename, len(resp.content))
    return resp.content
