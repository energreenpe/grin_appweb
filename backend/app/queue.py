"""
queue.py — Infraestructura ASÍNCRONA compartida (Redis + RQ).

Punto ÚNICO de acceso a la cola de tareas pesadas. Cualquier módulo que necesite
delegar trabajo costoso (p. ej. LIST: conversión LibreOffice y estampado de PDF)
ENCOLA aquí en lugar de ejecutarlo dentro del request de FastAPI.

Regla de oro: el proceso web (FastAPI) NUNCA ejecuta la tarea pesada; solo la
encola. La ejecuta el proceso `workers/worker.py`. Esta separación es lo que evita
bloquear el event loop bajo concurrencia.

Convención de colas: una cola por tipo de carga, para poder escalar/aislar workers
por tipo de tarea más adelante.
"""
from __future__ import annotations

from functools import lru_cache

from redis import Redis
from rq import Queue

from app.config import get_settings

# ── Nombres de colas (fuente única de verdad, compartida entre web y worker) ────
QUEUE_CONVERSION = "conversion"   # DOCX/XLSX → PDF (LibreOffice / Gotenberg)
QUEUE_EXPORT = "export"           # Estampado de campos/overlays sobre PDF
QUEUE_MAINTENANCE = "maintenance" # Limpieza periódica de temporales (job reprogramado)
QUEUE_NAMES = [QUEUE_CONVERSION, QUEUE_EXPORT, QUEUE_MAINTENANCE]


@lru_cache
def get_redis() -> Redis:
    """Conexión Redis del proceso actual (una por proceso, cacheada)."""
    return Redis.from_url(get_settings().redis_url)


def get_queue(name: str) -> Queue:
    """Devuelve una `rq.Queue` por nombre, sobre la conexión Redis compartida.

    Úsala desde la capa de servicio para encolar:  get_queue(QUEUE_CONVERSION).enqueue(...)
    """
    if name not in QUEUE_NAMES:
        raise ValueError(f"Cola desconocida: {name!r}. Válidas: {QUEUE_NAMES}")
    return get_queue_unchecked(name)


def get_queue_unchecked(name: str) -> Queue:
    """Variante sin validar el nombre (uso interno: worker, healthcheck)."""
    return Queue(name, connection=get_redis())
