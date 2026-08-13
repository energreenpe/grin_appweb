"""
maintenance.py — Limpieza de archivos temporales del módulo LIST.

Reemplaza el `temp_storage` del LIST original (que escaneaba el disco en CADA
request como background_task). Aquí es un barrido por edad con TTL por subdirectorio,
ejecutado por un job periódico del worker (ver workers/tasks/cleanup.py).

TTL (segundos) por subcarpeta de uploads/:
- list/incoming : 1 h  — el archivo crudo subido; se borra tras convertir (esto cubre fallos).

NOTA: list/pdf (PDF base de los documentos) NO se limpia por TTL: es permanente
mientras exista el ListDocumento que lo referencia (se borra al eliminar el documento).

NOTA: el resultado estampado (export) YA NO se guarda en disco — vive un rato
corto en Redis y se borra al descargarse (ver app.modules.list.output_store),
así que no hay nada que limpiar aquí para esa carpeta.
"""
from __future__ import annotations

import logging
import os
import time

from app import storage

logger = logging.getLogger("list.maintenance")

TTL_POR_SUBDIR = {
    "list/incoming": 1 * 3600,
}


def limpiar_temporales(now: float | None = None) -> dict:
    """Borra archivos más viejos que su TTL en cada subcarpeta. Devuelve el conteo
    de borrados por subcarpeta."""
    now = now if now is not None else time.time()
    borrados: dict[str, int] = {}

    for subdir, ttl in TTL_POR_SUBDIR.items():
        full_dir = os.path.join(storage.UPLOADS_DIR, *subdir.split("/"))
        count = 0
        if os.path.isdir(full_dir):
            for name in os.listdir(full_dir):
                fpath = os.path.join(full_dir, name)
                if not os.path.isfile(fpath):
                    continue
                try:
                    age = now - os.path.getmtime(fpath)
                except OSError:
                    continue
                if age > ttl:
                    storage.delete(f"uploads/{subdir}/{name}")
                    count += 1
        borrados[subdir] = count

    total = sum(borrados.values())
    if total:
        logger.info("Limpieza de temporales LIST: %s (total %d)", borrados, total)
    return borrados
