"""
seed_productos.py — Carga el catálogo real de productos del módulo QUOTE.

Lee backend/seeds/productos.json (71 productos reales de Energreen: paneles,
baterías, inversores, estructuras) y los siembra en la tabla `productos`.

Es IDEMPOTENTE: puede correrse varias veces sin duplicar (identifica cada
producto por su `nombre` exacto; si ya existe, actualiza sus datos).

Uso (desde grin_web/backend, con el venv activado y la BD migrada):
    python scripts/seed_productos.py
o dentro del contenedor:
    docker compose exec api python scripts/seed_productos.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal  # noqa: E402
from app.modules.quote.models import Producto  # noqa: E402

SEEDS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "seeds"))


def seed():
    with open(os.path.join(SEEDS_DIR, "productos.json"), encoding="utf-8") as f:
        productos = json.load(f)

    db = SessionLocal()
    creados = 0
    actualizados = 0
    try:
        for item in productos:
            existente = db.query(Producto).filter_by(nombre=item["nombre"]).first()
            if existente:
                existente.categoria = item["categoria"]
                existente.descripcion = item.get("descripcion")
                existente.marca = item.get("marca")
                existente.unidad = item.get("unidad", "und")
                existente.precio = item.get("precio", 0)
                existente.moneda = item.get("moneda", "PEN")
                actualizados += 1
            else:
                db.add(Producto(
                    categoria=item["categoria"],
                    nombre=item["nombre"],
                    descripcion=item.get("descripcion"),
                    marca=item.get("marca"),
                    unidad=item.get("unidad", "und"),
                    precio=item.get("precio", 0),
                    moneda=item.get("moneda", "PEN"),
                ))
                creados += 1
        db.commit()
        print(f"[OK] Productos: {creados} creados, {actualizados} actualizados.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
