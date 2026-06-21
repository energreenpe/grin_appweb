"""
cleanup.py — Tarea periódica de limpieza de temporales del módulo LIST.

Patrón de recurrencia sin dependencias extra (sin rq-scheduler): la tarea se
RE-PROGRAMA a sí misma vía `enqueue_in`, y el worker corre con `with_scheduler=True`
para disparar los jobs diferidos cuando vencen.

El worker, al arrancar, llama a `programar_limpieza()` solo si no hay ya una
programada (`esta_programada()`), evitando que reinicios acumulen cadenas.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from app.modules.list.maintenance import limpiar_temporales
from app.queue import QUEUE_MAINTENANCE, get_queue_unchecked

logger = logging.getLogger("list.tasks.cleanup")

# Ruta de import de esta tarea (para encolar/identificar).
CLEANUP_TASK = "workers.tasks.cleanup.cleanup_temporales"

# Cada cuánto corre la limpieza.
CLEANUP_INTERVAL_MIN = 30


def programar_limpieza(delay_min: int = CLEANUP_INTERVAL_MIN) -> None:
    """Programa la próxima corrida de limpieza dentro de `delay_min` minutos."""
    q = get_queue_unchecked(QUEUE_MAINTENANCE)
    q.enqueue_in(timedelta(minutes=delay_min), CLEANUP_TASK)


def esta_programada() -> bool:
    """¿Ya hay una limpieza en la cola de programados? Evita duplicar cadenas."""
    from rq.registry import ScheduledJobRegistry

    q = get_queue_unchecked(QUEUE_MAINTENANCE)
    reg = ScheduledJobRegistry(queue=q)
    for jid in reg.get_job_ids():
        try:
            job = q.job_class.fetch(jid, connection=q.connection)
        except Exception:
            continue
        if job is not None and job.func_name == CLEANUP_TASK:
            return True
    return False


def cleanup_temporales() -> dict:
    """Ejecuta la limpieza y reprograma la siguiente corrida."""
    borrados = limpiar_temporales()
    try:
        programar_limpieza()
    except Exception:
        logger.exception("No se pudo reprogramar la limpieza de temporales")
    return borrados
