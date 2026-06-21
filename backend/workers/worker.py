"""
worker.py — Bootstrap del worker RQ.

Proceso separado del API. Consume las colas definidas en `app.queue.QUEUE_NAMES`
y ejecuta las tareas de `workers/tasks/`.

Ejecución (dev, desde la carpeta backend/):
    python -m workers.worker

Multiplataforma:
- Linux (producción/contenedor): `Worker` estándar (hace fork por job).
- Windows (dev): `os.fork` no existe, así que usamos `SimpleWorker` (mismo proceso)
  con `TimerDeathPenalty` (timeout por threading.Timer, ya que SIGALRM tampoco
  existe en Windows). Esto permite levantar el worker en el equipo de desarrollo.
"""
from __future__ import annotations

import logging
import os

from rq import Queue, SimpleWorker, Worker

from app.config import get_settings
from app.queue import QUEUE_NAMES, get_redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("worker")


def _worker_class():
    """Elige la clase de worker compatible con el SO actual."""
    if os.name == "nt":  # Windows (dev)
        from rq.timeouts import TimerDeathPenalty

        class WindowsWorker(SimpleWorker):
            death_penalty_class = TimerDeathPenalty

        return WindowsWorker
    return Worker  # Linux/macOS (producción)


def main() -> None:
    settings = get_settings()
    conn = get_redis()
    worker_cls = _worker_class()

    queues = [Queue(name, connection=conn) for name in QUEUE_NAMES]
    logger.info(
        "Iniciando %s | Redis=%s | colas=%s",
        worker_cls.__name__,
        settings.redis_url,
        QUEUE_NAMES,
    )

    # Programa la limpieza periódica de temporales si no hay ya una en cola.
    try:
        from workers.tasks.cleanup import esta_programada, programar_limpieza

        if not esta_programada():
            programar_limpieza()
            logger.info("Limpieza periódica de temporales programada.")
    except Exception:
        logger.exception("No se pudo programar la limpieza periódica")

    worker = worker_cls(queues, connection=conn)
    # with_scheduler=True: dispara los jobs diferidos (limpieza reprogramada) al vencer.
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
