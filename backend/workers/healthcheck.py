"""
healthcheck.py — Verificación end-to-end de la infraestructura async.

Encola la tarea `ping` en la cola de conversión y espera el resultado, demostrando
que Redis + RQ + worker funcionan de punta a punta.

Uso (con Redis arriba y el worker corriendo en otra terminal):
    cd backend
    python -m workers.healthcheck

Salida esperada: "OK" + los metadatos del worker que ejecutó la tarea.
"""
from __future__ import annotations

import sys
import time

from app.queue import QUEUE_CONVERSION, get_queue
from workers.tasks.ping import ping


def main() -> int:
    q = get_queue(QUEUE_CONVERSION)
    print(f"[healthcheck] Encolando 'ping' en la cola '{QUEUE_CONVERSION}'...")
    job = q.enqueue(ping, "hola-worker")
    print(f"[healthcheck] job_id={job.id} status={job.get_status()}")

    deadline = time.time() + 20  # segundos
    while time.time() < deadline:
        job.refresh()
        status = job.get_status()
        if status == "finished":
            print("[healthcheck] OK - resultado:", job.result)
            return 0
        if status == "failed":
            print("[healthcheck] FALLO -", job.exc_info)
            return 1
        time.sleep(0.5)

    print("[healthcheck] TIMEOUT - ¿está corriendo el worker? (python -m workers.worker)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
