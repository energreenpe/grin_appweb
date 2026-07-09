"""
seed_usuarios.py — Siembra usuarios de PRUEBA en la tabla `usuarios` (shared).

Lee backend/seeds/usuarios.json. Estos son las CUENTAS del sistema
(vendedor/técnico/ingeniero) que alimentan los desplegables de responsables en
QUOTE, INSPECTOR y MATH. NO son el personal de campo de PLANNER (eso es
planner_personal, ver seed_personal_planner.py).

IMPORTANTE — valores de `rol`: el código filtra por valores EXACTOS en minúscula:
  QUOTE -> rol="vendedor"   INSPECTOR -> rol="tecnico"   MATH -> rol="ingeniero"

Es IDEMPOTENTE: si ya existe un usuario con el mismo correo, actualiza sus
datos en vez de duplicar. La tabla no tiene columna de contraseña (aún no hay
auth), así que no se setea.

Uso (desde grin_web/backend, con el venv activado y la BD migrada):
    python scripts/seed_usuarios.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal  # noqa: E402
from app.modules.shared.models import Usuario  # noqa: E402

SEEDS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "seeds"))


def seed():
    with open(os.path.join(SEEDS_DIR, "usuarios.json"), encoding="utf-8") as f:
        usuarios = json.load(f)

    db = SessionLocal()
    creados = 0
    actualizados = 0
    try:
        for item in usuarios:
            existente = db.query(Usuario).filter(Usuario.correo == item["correo"]).first()
            if existente:
                existente.nombre = item["nombre"]
                existente.telefono = item["telefono"]
                existente.rol = item["rol"]
                existente.activo = True
                actualizados += 1
            else:
                db.add(Usuario(
                    nombre=item["nombre"], correo=item["correo"],
                    telefono=item["telefono"], rol=item["rol"], activo=True,
                ))
                creados += 1
        db.commit()
        print(f"[OK] Usuarios: {creados} creados, {actualizados} actualizados.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
