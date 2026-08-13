"""
output_store.py — Almacenamiento TRANSITORIO en Redis de los PDF exportados (LIST).

Los documentos de salida (resultado de "Exportar PDF") los descarga el propio
frontend automáticamente en cuanto el job termina — no hay un flujo donde el
usuario vuelva más tarde a buscarlos. Guardarlos en uploads/ solo acumula
archivos que nadie vuelve a pedir. Por eso viven un rato corto en Redis (la
misma infraestructura que ya usa la cola de tareas) en vez de en disco:
expiran solos por TTL y, además, se borran de inmediato la primera vez que se
sirven (lectura única).
"""
from __future__ import annotations

import logging

from redis.exceptions import RedisError

from app.queue import get_redis

logger = logging.getLogger("list.output_store")

_KEY_PREFIX = "list:output:"
_TTL_SECONDS = 10 * 60  # 10 min: de sobra para que el frontend descargue justo tras exportar


def _key(output_name: str) -> str:
    return f"{_KEY_PREFIX}{output_name}"


def save_output(output_name: str, data: bytes) -> None:
    """Guarda el PDF exportado en Redis con TTL corto. Se llama desde el worker
    justo al terminar el estampado; si Redis falla aquí, el job debe fallar
    (no hay a dónde más guardar el resultado), por eso NO se atrapa la excepción."""
    get_redis().set(_key(output_name), data, ex=_TTL_SECONDS)


def pop_output(output_name: str) -> bytes | None:
    """Lee y BORRA el PDF exportado (lectura única). Devuelve None si no existe,
    ya expiró, o Redis no está disponible — así el endpoint de descarga responde
    404 en vez de un error 500 si Redis tiene un problema pasajero."""
    try:
        r = get_redis()
        key = _key(output_name)
        data = r.get(key)
        if data is not None:
            r.delete(key)
        return data
    except RedisError:
        logger.warning("Redis no disponible al leer el output %s", output_name)
        return None
