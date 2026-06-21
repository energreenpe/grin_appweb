"""
settings.py — Parámetros de runtime del worker (no del API).

Los nombres de cola viven en `app.queue` (fuente única). Aquí van solo los knobs
del proceso worker: timeouts y retención de resultados.
"""
from app.queue import QUEUE_NAMES  # re-export por conveniencia

# Tiempo máximo (segundos) que una tarea puede ejecutarse antes de matarse.
# Cubre la conversión LibreOffice de archivos grandes (el converter usa timeout 60s
# internamente; dejamos margen). Ajustable por entregable.
DEFAULT_JOB_TIMEOUT = 180

# Cuánto se conserva el resultado de un job en Redis tras terminar (segundos).
# El frontend hace polling de /jobs/{id}; 1h es holgado para una sesión de edición.
DEFAULT_RESULT_TTL = 60 * 60

__all__ = ["QUEUE_NAMES", "DEFAULT_JOB_TIMEOUT", "DEFAULT_RESULT_TTL"]
