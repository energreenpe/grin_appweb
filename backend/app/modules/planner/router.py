"""
router.py — Endpoints HTTP del módulo PLANNER.

APIRouter SIN prefix: el prefijo `/api/planner` se aplica en `app/main.py`.

E0 (andamiaje): solo `GET /health`. El CRUD de proyectos/personal/cuadrillas/
actividades, asistencia, evidencia, Curva S y los reportes PDF se agregan en los
entregables siguientes.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "module": "planner"}
