"""
images.py — Validación y conversión de imágenes subidas por el usuario a WEBP.

Todo logo (empresa o banco) se reencoda a .webp. El reencode con Pillow es además
una medida de seguridad: descarta payloads/polyglots y metadatos EXIF. La detección
de formato se hace por contenido real (magic bytes), no por la extensión ni el
content-type que envía el cliente.
"""
from __future__ import annotations

from io import BytesIO

from PIL import Image

# Anti "decompression bomb": rechaza imágenes con demasiados píxeles.
Image.MAX_IMAGE_PIXELS = 40_000_000

MAX_BYTES = 2 * 1024 * 1024          # 2 MB
_ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP", "MPO"}   # MPO = algunas fotos JPEG


class ImageError(Exception):
    """Imagen inválida o no permitida (el router lo mapea a HTTP 400)."""


def to_webp(raw: bytes) -> bytes:
    """Valida `raw` como imagen y devuelve sus bytes reencodados a WEBP."""
    if not raw:
        raise ImageError("Archivo vacío.")
    if len(raw) > MAX_BYTES:
        raise ImageError("No puede insertar un logo de más de 2 MB.")

    # 1) Verificar que es una imagen real (magic bytes vía Pillow).
    try:
        Image.open(BytesIO(raw)).verify()
    except Exception:
        raise ImageError("El archivo no es una imagen válida.")

    # 2) Reabrir (verify() deja la imagen inutilizable) y validar el formato.
    img = Image.open(BytesIO(raw))
    if img.format not in _ALLOWED_FORMATS:
        raise ImageError("Formato no permitido. Usa PNG, JPG o WEBP.")

    # 3) Normalizar el modo (conservar transparencia si la hay) y reencodar.
    img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
    out = BytesIO()
    img.save(out, "WEBP", quality=85, method=6)
    return out.getvalue()
