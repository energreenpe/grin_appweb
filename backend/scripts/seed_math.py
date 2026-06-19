"""
seed_math.py — Carga los catálogos del módulo MATH y un usuario ingeniero.

Lee los JSON de backend/seeds/ (copiados del sistema legacy) y siembra:
  - equipos_tecnicos      (paneles, baterías, inversores aislados y de autoconsumo)
  - regiones              (con HSP mínimo/promedio/mayor)
  - electrodomesticos_catalogo (potencias base)
  - usuarios              (ingeniero responsable)

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
from app.modules.math.models import (  # noqa: E402
    EquipoTecnico, Region, ElectrodomesticoCatalogo,
)
from app.modules.shared.models import Usuario  # noqa: E402

SEEDS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "seeds"))

# Potencias base de electrodomésticos (W). Copiado de
# MATH/models/electrodomestico_model.py::POTENCIAS. Las variantes (focos LED vs
# incandescente, aire acondicionado por BTU) las resuelve el motor, no el catálogo.
POTENCIAS = {
    "PC": 150, "FOCO DORMITORIO": 10, "CELULAR": 15, "LAMPARA": 20,
    "VENTILADOR": 50, "REFRIGERADORA": 300, "MICROONDAS": 1100,
    "OLLA ARROCERA": 1000, "THERMA ELECTRICA": 1500, "COCINA ELECTRICA": 4500,
    "LICUADORA": 600, "TV LED": 120, "LAPTOP": 150, "REPRODUCTOR DVD": 20,
    "EQUIPO DE SONIDO": 30, "FOCO SALA": 100, "CALENTADOR ELECTRICO": 1500,
    "DUCHA ELECTRICA": 4000, "SECADORA DE CABELLO": 1200, "FOCO BAÑO": 10,
    "ASPIRADORA": 1400, "PLANCHA DE ROPA": 1000, "SECADORA DE ROPA": 2500,
    "LAVADORA": 500, "FOCO LAVANDERIA": 20, "LAMPARA SALA": 20, "BATIDORA": 1200,
    "WAFLERA": 1300, "FOCO COCINA": 10, "ELECTRO BOMBA": 13000, "FLUORESCENTE": 40,
    "REFLECTOR LED": 150, "HERVIDOR ELECTRICO": 1500, "LUSTRADORA": 600,
    "RADIOGRABADORA": 30, "CONGELADORA": 600, "TURBO CARGADOR CELULAR": 160,
    "MODEM INTERNET": 30, "DECODIFICADOR TV": 43.4, "LECTOR DE HUELLAS": 200,
    "CAMARA DE VIGILANCIA": 7, "MOTOR MONOFASICO": 2200, "TOMACORRIENTES": 30,
}

# Ingeniero responsable a sembrar (rol="ingeniero").
INGENIERO = {
    "nombre": "Luis Parrilla",
    "correo": "luis@gmail.com",
    "telefono": "987654321",
    "rol": "ingeniero",
    "activo": True,
}


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
    for nombre, potencia in POTENCIAS.items():
        item = db.query(ElectrodomesticoCatalogo).filter_by(nombre=nombre).first()
        if item:
            item.potencia_w = potencia
        else:
            db.add(ElectrodomesticoCatalogo(nombre=nombre, potencia_w=potencia))
    print(f"  electrodomesticos_catalogo: {len(POTENCIAS)} registros procesados")


def seed_ingeniero(db):
    usuario = db.query(Usuario).filter_by(correo=INGENIERO["correo"]).first()
    if usuario:
        usuario.nombre = INGENIERO["nombre"]
        usuario.telefono = INGENIERO["telefono"]
        usuario.rol = INGENIERO["rol"]
        usuario.activo = INGENIERO["activo"]
        print(f"  usuario ingeniero actualizado: {INGENIERO['nombre']}")
    else:
        db.add(Usuario(**INGENIERO))
        print(f"  usuario ingeniero creado: {INGENIERO['nombre']}")


def main():
    db = SessionLocal()
    try:
        print("Sembrando catálogos del módulo MATH...")
        seed_equipos(db)
        seed_regiones(db)
        seed_electrodomesticos(db)
        seed_ingeniero(db)
        db.commit()
        print("Seed MATH completado correctamente.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
