"""
maintenance.py — Tareas de mantenimiento del módulo QUOTE.

Job de limpieza de logos huérfanos: compara los archivos en uploads/quote/{banks,empresa}
contra las referencias en la BD (logo de empresa, plantilla global y todas las
cotizaciones) y elimina los que ya no están referenciados.

SEGURIDAD: solo borra archivos más viejos que `min_age_hours` (por defecto 24h), para
no eliminar un logo recién subido que aún no se guardó en una cotización/plantilla.

Uso como job periódico (cron en Linux / Task Scheduler en Windows):
    python -m app.modules.quote.maintenance            # simulación (dry-run, no borra, te muestra qué borraría)
    python -m app.modules.quote.maintenance --apply    # borra de verdad (pero aplica cuando pasen 24 horas)
    python -m app.modules.quote.maintenance --apply --min-age-hours 48  # puedes elegir 48 horas si quieres
    python -m app.modules.quote.maintenance --apply --min-age-hours 0  # borra de verdad (sin esperar, imediato)
"""
from __future__ import annotations

import argparse
import os
import time

from app import storage
from app.db import SessionLocal
from app.modules.quote.models import Cotizacion, EmpresaConfig, PlantillasGlobales

# Subcarpetas del módulo quote que contienen logos (no toca inspector ni otros).
_QUOTE_LOGO_SUBDIRS = ["quote/banks", "quote/empresa"]


def _referenced_logos(db) -> set[str]:
    """Reúne todas las rutas de logo referenciadas en la BD (relativas tipo
    'uploads/quote/banks/x.webp')."""
    refs: set[str] = set()

    empresa = db.query(EmpresaConfig).first()
    if empresa and empresa.logo_path:
        refs.add(empresa.logo_path)

    def add_from_cuentas(cuentas):
        for banco in (cuentas or []):
            logo = banco.get("logo")
            if logo:
                refs.add(logo)

    plantilla = db.query(PlantillasGlobales).first()
    if plantilla:
        add_from_cuentas(plantilla.cuentas_bancarias)

    for cot in db.query(Cotizacion).all():
        add_from_cuentas(cot.cuentas_bancarias)

    return refs


def cleanup_orphan_logos(db, *, min_age_hours: int = 24, apply: bool = False) -> dict:
    """Elimina logos de quote sin referencia y más viejos que `min_age_hours`.
    Si apply=False (default) solo simula. Devuelve un resumen."""
    referenced = _referenced_logos(db)
    now = time.time()
    min_age_secs = min_age_hours * 3600

    scanned = 0
    deleted: list[str] = []
    skipped_recent = 0

    for sub in _QUOTE_LOGO_SUBDIRS:
        dir_abs = os.path.join(storage.UPLOADS_DIR, sub)
        if not os.path.isdir(dir_abs):
            continue
        for name in os.listdir(dir_abs):
            full = os.path.join(dir_abs, name)
            if not os.path.isfile(full):
                continue
            scanned += 1
            rel = f"uploads/{sub}/{name}"
            if rel in referenced:
                continue
            # Huérfano: respetar la edad mínima para no borrar subidas recientes.
            if now - os.path.getmtime(full) < min_age_secs:
                skipped_recent += 1
                continue
            if apply:
                storage.delete(rel)
            deleted.append(rel)

    return {
        "scanned": scanned,
        "referenced": len(referenced),
        "orphans": len(deleted),
        "deleted": deleted,
        "skipped_recent": skipped_recent,
        "applied": apply,
    }


def _main():
    parser = argparse.ArgumentParser(description="Limpieza de logos huérfanos (módulo quote).")
    parser.add_argument("--apply", action="store_true", help="Borra de verdad (sin esto, solo simula).")
    parser.add_argument("--min-age-hours", type=int, default=24, help="Edad mínima del huérfano para borrarlo (default 24).")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = cleanup_orphan_logos(db, min_age_hours=args.min_age_hours, apply=args.apply)
    finally:
        db.close()

    modo = "APLICADO (borrado real)" if result["applied"] else "DRY-RUN (simulación)"
    print(f"[{modo}] escaneados={result['scanned']} referenciados={result['referenced']} "
          f"huérfanos={result['orphans']} omitidos_recientes={result['skipped_recent']}")
    for rel in result["deleted"]:
        print(("  borrado: " if result["applied"] else "  huérfano: ") + rel)


if __name__ == "__main__":
    _main()
