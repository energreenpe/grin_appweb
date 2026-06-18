"""
ratelimit.py — Rate limiting simple en memoria (por IP), sin dependencias extra.

Pensado para proteger endpoints costosos (subida de imágenes, generación de PDF)
contra abuso/saturación. Ventana deslizante por IP. Nota: el contador vive en el
proceso; con varios workers/instancias cada uno lleva el suyo (suficiente para esta
escala). Si en el futuro se escala horizontalmente, migrar a Redis (slowapi/limits).
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Dependencia FastAPI: limita a `max_requests` por `window_seconds` por IP."""

    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def __call__(self, request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        dq = self._hits[key]

        # Purga las marcas fuera de la ventana de tiempo.
        while dq and now - dq[0] > self.window:
            dq.popleft()

        if len(dq) >= self.max_requests:
            retry_after = int(self.window - (now - dq[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Demasiadas solicitudes. Intenta de nuevo en {retry_after} segundos.",
                headers={"Retry-After": str(retry_after)},
            )

        dq.append(now)
        if not dq:                       # housekeeping: no dejar IPs vacías acumuladas
            self._hits.pop(key, None)
