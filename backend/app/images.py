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
MAX_DIMENSION = 1000                  # lado mayor (px): un logo no necesita más
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

    # 3) Normalizar el modo (conservar transparencia si la hay).
    img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")

    # 4) Reducir la resolución si es grande. El tiempo de encodeo WEBP escala con
    #    los píxeles, no con los KB: bajar un logo de 4K a <=1000px lo acelera de
    #    ~20s a <1s, sin pérdida visible (se muestra pequeño y en el PDF también).
    #    thumbnail() solo achica (nunca agranda) y conserva la proporción.
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

    # 5) Encodear a WEBP. method=4 (en vez de 6) acelera bastante con calidad casi
    #    idéntica para un logo.
    out = BytesIO()
    img.save(out, "WEBP", quality=85, method=4)
    return out.getvalue()
