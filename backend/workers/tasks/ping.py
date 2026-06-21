"""
ping.py — Tarea trivial de salud del circuito Redis→Worker.

NO tiene valor de negocio: solo prueba que encolar y ejecutar funciona de punta a
punta (web encola → Redis → worker ejecuta → resultado disponible). Se conserva como
smoke-test de la infraestructura async.
"""
from __future__ import annotations

import os
import socket
import time


def ping(message: str = "pong") -> dict:
    """Devuelve metadatos del worker que la ejecutó."""
    return {
        "message": message,
        "worker_pid": os.getpid(),
        "host": socket.gethostname(),
        "executed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
