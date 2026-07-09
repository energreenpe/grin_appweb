"""
seed_personal_planner.py — Siembra el personal de PRUEBA del módulo PLANNER.

Lee backend/seeds/planner_personal.json (6 trabajadores de campo de ejemplo) y
los carga en la tabla planner_personal para empezar a probar el módulo
(asignar a cuadrillas, asistencia, etc.). El email queda vacío a propósito.

Es IDEMPOTENTE: si ya existe una persona con el mismo DNI, actualiza sus datos
en vez de duplicar.

Uso (desde grin_web/backend, con el venv activado y la BD migrada):
    python scripts/seed_personal_planner.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal  # noqa: E402
from app.modules.planner.models import Personal, EstadoMiembro  # noqa: E402

SEEDS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "seeds"))


def seed():
    with open(os.path.join(SEEDS_DIR, "planner_personal.json"), encoding="utf-8") as f:
        personal = json.load(f)

    db = SessionLocal()
    creados = 0
    actualizados = 0
    try:
        for item in personal:
            existe = db.query(Personal).filter(Personal.dni == item["dni"]).first()
            if existe:
                existe.nombre = item["nombre"]
                existe.celular = item["celular"]
                existe.profesion = item["profesion"]
                existe.estado = EstadoMiembro.activo
                actualizados += 1
            else:
                db.add(Personal(
                    nombre=item["nombre"], dni=item["dni"], celular=item["celular"],
                    profesion=item["profesion"], estado=EstadoMiembro.activo, email="",
                ))
                creados += 1
        db.commit()
        print(f"[OK] Personal de prueba PLANNER: {creados} creados, {actualizados} actualizados.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
