"""
seed_usuarios.py — Siembra usuarios de PRUEBA en la tabla `usuarios` (shared).

Estos son las CUENTAS del sistema (vendedor/técnico/ingeniero) que alimentan los
desplegables de responsables en QUOTE, INSPECTOR y MATH. NO son el personal de
campo de PLANNER (eso es planner_personal, ver seed_personal_planner.py).

IMPORTANTE — valores de `rol`: el código filtra por valores EXACTOS en minúscula:
  QUOTE -> rol="vendedor"   INSPECTOR -> rol="tecnico"   MATH -> rol="ingeniero"
Por eso "Inspector" se guarda como "tecnico" (es el rol que consume ese módulo).

Idempotente: si ya existe un usuario con el mismo correo, lo omite.
La tabla no tiene columna de contraseña (aún no hay auth), así que no se setea.

Uso (desde grin_web/backend, con el venv activado y la BD migrada):
    python scripts/seed_usuarios.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal  # noqa: E402
from app.modules.shared.models import Usuario  # noqa: E402

# (nombre, correo, telefono, rol). rol ya normalizado a los valores que el sistema usa.
USUARIOS = [
    ("Javier Viera",    "javierviera@gmail.com", "987654321", "vendedor"),   # Vendedor
    ("Anel Enmita",     "anelenmita@gmail.com",  "987654321", "tecnico"),    # Inspector -> tecnico
    ("Daniel Parrilla", "energreenpe@gmail.com", "945486818", "ingeniero"),  # Ingeniero
]


def seed():
    db = SessionLocal()
    creados = 0
    try:
        for nombre, correo, telefono, rol in USUARIOS:
            if db.query(Usuario).filter(Usuario.correo == correo).first():
                continue
            db.add(Usuario(nombre=nombre, correo=correo, telefono=telefono, rol=rol, activo=True))
            creados += 1
        db.commit()
        print(f"[OK] Usuarios de prueba: {creados} creados (los ya existentes por correo se omiten).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
