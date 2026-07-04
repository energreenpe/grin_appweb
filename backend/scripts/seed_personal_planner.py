"""
seed_personal_planner.py — Siembra el personal de PRUEBA del módulo PLANNER.

Carga los 6 trabajadores de campo de ejemplo en la tabla planner_personal para
empezar a probar el módulo (asignar a cuadrillas, asistencia, etc.). El email
queda vacío a propósito.

Evita duplicar de forma básica: si ya existe una persona con el mismo DNI, la
omite (el manejo formal de duplicados/registro se verá después).

Uso (desde grin_web/backend, con el venv activado y la BD migrada):
    python scripts/seed_personal_planner.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal  # noqa: E402
from app.modules.planner.models import Personal, EstadoMiembro  # noqa: E402

# (nombre, dni, celular, profesion) — datos de prueba de la imagen. Estado: Activo. Email: vacío.
PERSONAL = [
    ("Carlos Vargas",   "47111111", "944 111 222", "Técnico Electricista"),
    ("Maria Lopez",     "48222222", "944 333 444", "Instalador de Paneles Solares"),
    ("Jose Ramirez",    "49333333", "944 555 666", "Operario de Montaje"),
    ("Ana Paredes",     "50444444", "944 777 888", "Supervisor de Obra"),
    ("Luis Mendoza",    "51555555", "944 999 000", "Instalador Eléctrico"),
    ("Ricardo Morales", "52666666", "945 111 222", "Ingeniero Eléctrico"),
]


def seed():
    db = SessionLocal()
    creados = 0
    try:
        for nombre, dni, celular, profesion in PERSONAL:
            existe = db.query(Personal).filter(Personal.dni == dni).first()
            if existe:
                continue
            db.add(Personal(
                nombre=nombre, dni=dni, celular=celular, profesion=profesion,
                estado=EstadoMiembro.activo, email="",
            ))
            creados += 1
        db.commit()
        print(f"[OK] Personal de prueba PLANNER: {creados} creados (los ya existentes por DNI se omiten).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
