"""
seed_feriados_peru.py — Siembra los feriados NACIONALES del Perú para un año.

Alimenta el motor de cronograma del módulo PLANNER (días laborables que descuentan
feriados). Los feriados regionales se agregan desde la app (POST /api/planner/feriados).

Es IDEMPOTENTE: no duplica (omite los que ya existen para ese año/fecha).

Uso (desde grin_web/backend, con el venv activado y la BD migrada):
    python scripts/seed_feriados_peru.py           # año en curso
    python scripts/seed_feriados_peru.py 2026       # año específico
"""
import os
import sys
from datetime import date

# Permite importar `app...` sin importar desde dónde se ejecute el script.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal  # noqa: E402
from app.modules.planner.models import Feriado, TipoFeriado  # noqa: E402

# Feriados nacionales de fecha FIJA (mes, día, nombre). Vigentes en Perú.
FIJOS = [
    (1, 1, "Año Nuevo"),
    (5, 1, "Día del Trabajo"),
    (6, 7, "Batalla de Arica y Día de la Bandera"),
    (6, 29, "San Pedro y San Pablo"),
    (7, 23, "Día de la Fuerza Aérea del Perú"),
    (7, 28, "Fiestas Patrias"),
    (7, 29, "Fiestas Patrias"),
    (8, 6, "Batalla de Junín"),
    (8, 30, "Santa Rosa de Lima"),
    (10, 8, "Combate de Angamos"),
    (11, 1, "Todos los Santos"),
    (12, 8, "Inmaculada Concepción"),
    (12, 9, "Batalla de Ayacucho"),
    (12, 25, "Navidad"),
]

# Feriados MÓVILES (Semana Santa) por año — Jueves y Viernes Santo.
MOVILES = {
    2025: [(date(2025, 4, 17), "Jueves Santo"), (date(2025, 4, 18), "Viernes Santo")],
    2026: [(date(2026, 4, 2), "Jueves Santo"), (date(2026, 4, 3), "Viernes Santo")],
    2027: [(date(2027, 3, 25), "Jueves Santo"), (date(2027, 3, 26), "Viernes Santo")],
}


def seed(anio: int):
    db = SessionLocal()
    creados = 0
    try:
        feriados = [(date(anio, m, d), n) for (m, d, n) in FIJOS]
        feriados += MOVILES.get(anio, [])
        for fecha, nombre in feriados:
            existe = db.query(Feriado).filter(
                Feriado.fecha == fecha, Feriado.tipo == "Nacional"
            ).first()
            if existe:
                continue
            db.add(Feriado(
                nombre=nombre, fecha=fecha, tipo=TipoFeriado.nacional,
                region=None, anio=anio, recurrente=True,
            ))
            creados += 1
        db.commit()
        if anio not in MOVILES:
            print(f"  [AVISO] Sin Semana Santa para {anio}: agregala manualmente o amplia MOVILES.")
        print(f"[OK] Feriados nacionales {anio}: {creados} creados (los ya existentes se omiten).")
    finally:
        db.close()


if __name__ == "__main__":
    anio = int(sys.argv[1]) if len(sys.argv) > 1 else date.today().year
    seed(anio)
