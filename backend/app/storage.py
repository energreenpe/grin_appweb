"""
storage.py — Capa de almacenamiento de archivos subidos por el usuario.

Punto ÚNICO de cambio para el destino de almacenamiento: hoy escribe en disco
local (carpeta `uploads/`, ya servida en /uploads y fuera de git). El día que se
migre a almacenamiento de objetos (S3 / Cloudflare R2 / Supabase), se reescribe
SOLO este módulo y nada más del proyecto cambia.

Convención: las rutas que se guardan en la BD y se devuelven al frontend son
RELATIVAS y con barras '/', de la forma  "uploads/<subdir>/<archivo>".
Nunca rutas absolutas (rompen al cambiar de máquina/contenedor).
"""
from __future__ import annotations

import os

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_UPLOADS_ROOT = os.path.join(_BACKEND_ROOT, "uploads")


def _safe_full_path(rel_path: str) -> str:
    """Resuelve una ruta relativa a absoluta garantizando que quede DENTRO de
    uploads/ (evita path traversal con '..')."""
    full = os.path.abspath(os.path.join(_BACKEND_ROOT, rel_path))
    if os.path.commonpath([full, _UPLOADS_ROOT]) != _UPLOADS_ROOT:
        raise ValueError("Ruta fuera del directorio de uploads")
    return full


def save_bytes(data: bytes, subdir: str, filename: str) -> str:
    """Guarda `data` en uploads/<subdir>/<filename>. Devuelve la ruta relativa."""
    rel_path = f"uploads/{subdir}/{filename}"
    full = _safe_full_path(rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as f:
        f.write(data)
    return rel_path


def delete(rel_path: str | None) -> None:
    """Borra el archivo apuntado por una ruta relativa de uploads. No-op si está
    vacío, no existe o no es una ruta válida de uploads (silencioso a propósito)."""
    if not rel_path:
        return
    try:
        full = _safe_full_path(rel_path)
        if os.path.isfile(full):
            os.remove(full)
    except (ValueError, OSError):
        pass


def resolve(rel_path: str | None) -> str | None:
    """Devuelve la ruta absoluta en disco para LEER el archivo (usado por el PDF),
    o None si está vacío / no existe / no es una ruta válida de uploads."""
    if not rel_path:
        return None
    try:
        full = _safe_full_path(rel_path)
        return full if os.path.isfile(full) else None
    except ValueError:
        return None
