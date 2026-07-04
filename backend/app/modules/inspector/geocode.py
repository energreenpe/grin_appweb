"""
Reverse geocoding (coordenadas → nombre de dirección) para el módulo Inspector.

Orden jerárquico para optimizar recursos y respetar la política de Nominatim:
  1) Caché en PostgreSQL (geo_cache, clave = lat/lng redondeados) → hit = 0 llamadas.
  2) Rate limit en Redis (get_redis compartido) → máx 1 petición/segundo a Nominatim.
  3) Nominatim (httpx + User-Agent). Se parsea a un nombre y se guarda en caché.

Nunca propaga excepción: ante cualquier fallo devuelve
{direccion:"", error:..., manual:True} para que el frontend permita edición manual.
"""
from __future__ import annotations

import time
import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.queue import get_redis
from app.modules.inspector.models import GeoCache

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
GRID_DECIMALS = 4                 # ~11 m de grilla para la clave de caché
RATE_LIMIT_KEY = "nominatim:rl"   # ventana de 1 s en Redis
HTTP_TIMEOUT = 6.0


def _grid(v: float) -> float:
    return round(float(v), GRID_DECIMALS)


def _acquire_slot() -> bool:
    """Respeta el máx. 1 req/s a Nominatim con Redis (SET NX EX 1). Reintenta un
    par de veces antes de rendirse. Si Redis no responde, no bloquea (best-effort;
    el caché ya reduce drásticamente las llamadas)."""
    try:
        r = get_redis()
    except Exception:
        return True
    for _ in range(3):
        try:
            if r.set(RATE_LIMIT_KEY, "1", nx=True, ex=1):
                return True
        except Exception:
            return True
        time.sleep(0.7)
    return False


def _format_direccion(data: dict) -> str:
    """Arma un nombre conciso a partir de los componentes de Nominatim."""
    if not data or "error" in data:
        return ""
    addr = data.get("address", {}) or {}
    partes: list[str] = []
    calle = addr.get("road") or addr.get("pedestrian") or addr.get("footway")
    if calle:
        num = addr.get("house_number")
        partes.append(f"{calle} {num}" if num else calle)
    for clave in ("suburb", "neighbourhood", "village", "town", "city", "municipality", "state", "country"):
        val = addr.get(clave)
        if val:
            partes.append(val)
    partes = list(dict.fromkeys(partes))  # dedup preservando orden
    return ", ".join(partes) if partes else (data.get("display_name") or "")


def reverse_geocode(db: Session, lat: float, lng: float) -> dict:
    lat_k, lng_k = _grid(lat), _grid(lng)

    # 1) Caché PostgreSQL
    hit = db.query(GeoCache).filter(GeoCache.lat_key == lat_k, GeoCache.lng_key == lng_k).first()
    if hit:
        return {"direccion": hit.direccion, "manual": False, "cache": True}

    # 2) Rate limit (Redis, 1/s)
    if not _acquire_slot():
        return {"direccion": "", "error": "Servicio de mapas ocupado, intenta de nuevo en unos segundos.", "manual": True}

    # 3) Nominatim (+ guardar en caché). Nunca propaga excepción.
    try:
        params = {"lat": lat, "lon": lng, "format": "jsonv2", "accept-language": "es", "zoom": 18}
        headers = {"User-Agent": get_settings().nominatim_user_agent}
        resp = httpx.get(NOMINATIM_URL, params=params, headers=headers, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        direccion = _format_direccion(resp.json())
        if not direccion:
            return {"direccion": "", "error": "No se encontró una dirección para esa ubicación.", "manual": True}
        try:
            db.add(GeoCache(lat_key=lat_k, lng_key=lng_k, direccion=direccion))
            db.commit()
        except Exception:
            db.rollback()  # otro request pudo cachear la misma celda (carrera): no es fatal
        return {"direccion": direccion, "manual": False, "cache": False}
    except Exception as e:
        # No logueamos coordenadas (privacidad): solo el tipo de error.
        print(f"[geocode] fallo Nominatim: {type(e).__name__}")
        return {"direccion": "", "error": "No se pudo obtener la ubicación automáticamente.", "manual": True}
