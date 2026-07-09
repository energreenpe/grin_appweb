"""
seed_math.py — Carga los catálogos del módulo MATH.

Lee los JSON de backend/seeds/ y siembra:
  - equipos_tecnicos           (paneles, baterías, inversores aislados y de autoconsumo)
  - regiones                   (con HSP mínimo/promedio/mayor)
  - electrodomesticos_catalogo (potencias base)

El usuario ingeniero de prueba vive en seed_usuarios.py (Daniel Parrilla ya
cubre el rol "ingeniero") — no se duplica aquí.

Es IDEMPOTENTE: puede correrse varias veces sin duplicar (actualiza si ya existe).

Uso (desde grin_web/backend, con el venv activado y la BD migrada):
    python scripts/seed_math.py
"""
import json
import os
import sys

# Permite importar `app...` sin importar desde dónde se ejecute el script.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal  # noqa: E402
# Necesario aunque no se use directo: registra DatosCliente/Usuario en el
# mapper de SQLAlchemy, que Calculo (math/models.py) referencia por nombre de
# cadena ("DatosCliente") en su relationship(). Mismo motivo que en alembic/env.py.
from app.modules.shared import models as shared_models  # noqa: F401,E402
from app.modules.math.models import (  # noqa: E402
    EquipoTecnico, Region, ElectrodomesticoCatalogo,
)

SEEDS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "seeds"))


def _load(name):
    with open(os.path.join(SEEDS_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def seed_equipos(db):
    mapping = [
        ("paneles.json", "panel"),
        ("baterias.json", "bateria"),
        ("inversores_aislados.json", "inversor_aislado"),
        ("inversores_autoconsumo.json", "inversor_autoconsumo"),
    ]
    total = 0
    for filename, tipo in mapping:
        for item in _load(filename):
            descripcion = item.get("descripcion")
            if not descripcion:
                continue
            equipo = (
                db.query(EquipoTecnico)
                .filter_by(tipo=tipo, descripcion=descripcion)
                .first()
            )
            if equipo:
                equipo.marca = item.get("marca")
                equipo.specs = item
                equipo.activo = True
            else:
                db.add(EquipoTecnico(
                    tipo=tipo,
                    descripcion=descripcion,
                    marca=item.get("marca"),
                    specs=item,
                    activo=True,
                ))
            total += 1
    print(f"  equipos_tecnicos: {total} registros procesados")


def seed_regiones(db):
    data = _load("regiones_peru.json")
    for reg in data:
        nombre = reg["region"]
        hsp = reg.get("HSP", {})
        region = db.query(Region).filter_by(nombre=nombre).first()
        if region:
            region.hsp_minimo = hsp.get("minimo")
            region.hsp_promedio = hsp.get("promedio")
            region.hsp_mayor = hsp.get("mayor")
        else:
            db.add(Region(
                nombre=nombre,
                hsp_minimo=hsp.get("minimo"),
                hsp_promedio=hsp.get("promedio"),
                hsp_mayor=hsp.get("mayor"),
            ))
    print(f"  regiones: {len(data)} registros procesados")


def seed_electrodomesticos(db):
    data = _load("electrodomesticos.json")
    for item in data:
        nombre = item["nombre"]
        potencia = item["potencia_w"]
        equipo = db.query(ElectrodomesticoCatalogo).filter_by(nombre=nombre).first()
        if equipo:
            equipo.potencia_w = potencia
        else:
            db.add(ElectrodomesticoCatalogo(nombre=nombre, potencia_w=potencia))
    print(f"  electrodomesticos_catalogo: {len(data)} registros procesados")


def main():
    db = SessionLocal()
    try:
        print("Sembrando catálogos del módulo MATH...")
        seed_equipos(db)
        seed_regiones(db)
        seed_electrodomesticos(db)
        db.commit()
        print("Seed MATH completado correctamente.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
