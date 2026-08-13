"""
pdf_stamp.py — Estampado de campos de texto y overlays sobre un PDF.

Implementado con reportlab + pypdf (ambos ya en requirements; SIN licencia AGPL,
a diferencia de PyMuPDF). Estrategia:
  1) Construir un PDF-overlay en memoria con reportlab (misma cantidad y tamaño de
     páginas que el original), dibujando rectángulos (overlays / fondos) y texto
     con auto-wrap (platypus Paragraph + Frame).
  2) Fusionar cada página-overlay sobre la página original con pypdf.

⚠️ Sistema de coordenadas: el frontend/LIST guarda posiciones en PDF points con
ORIGEN ARRIBA-IZQUIERDA (y crece hacia abajo, como PyMuPDF). reportlab usa origen
ABAJO-IZQUIERDA (y crece hacia arriba). `_rect_bottomleft` hace la conversión.

Función PURA (sin FastAPI ni Redis). La invoca el worker (`workers/tasks/export.py`).
"""
from __future__ import annotations

import io
import logging
from typing import List, Tuple

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph

logger = logging.getLogger("list.pdf_stamp")

# Fuentes PDF estándar (mismos nombres en reportlab que en los schemas).
FONT_MAP = {
    "Helvetica": "Helvetica",
    "Times-Roman": "Times-Roman",
    "Courier": "Courier",
}

# Compensa el inset horizontal del <textarea> nativo del frontend (igual que LIST).
_TEXT_X_OFFSET = 3.0


def _color(rgb) -> Color:
    r, g, b = rgb
    return Color(float(r), float(g), float(b))


def _xml_escape(text: str) -> str:
    """Escapa para Paragraph y respeta saltos de línea del usuario."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


# Formas normalizadas (fracción 0..1 del ancho/alto del cuadro, origen abajo-
# izquierda) para check (✔) y aspa (✘). El bullet (•) es un círculo relleno,
# no necesita puntos. Se dibujan a mano en vez de usar los glifos Unicode
# ✔/✘/• porque las fuentes estándar de PDF (Helvetica/Times/Courier) no los
# incluyen — así se ven igual en cualquier lector, sin depender de la fuente.
_CHECK_POINTS = [(0.12, 0.5), (0.4, 0.18), (0.9, 0.8)]
_CROSS_LINES = [
    ((0.15, 0.15), (0.85, 0.85)),
    ((0.15, 0.85), (0.85, 0.15)),
]


def _draw_symbol(c, symbol: str, left: float, y_bottom: float, cw: float, ch: float,
                  color: Color, font_size: int) -> None:
    """Dibuja un símbolo vectorial (check/cross/bullet) centrado en el rect dado."""
    line_width = max(1.2, min(font_size * 0.14, min(cw, ch) * 0.22))
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(line_width)
    c.setLineCap(1)   # extremos redondeados
    c.setLineJoin(1)  # uniones redondeadas

    if symbol == "bullet":
        radius = min(cw, ch) * 0.28
        c.circle(left + cw / 2, y_bottom + ch / 2, radius, fill=1, stroke=0)
        return

    if symbol == "check":
        path = c.beginPath()
        path.moveTo(left + cw * _CHECK_POINTS[0][0], y_bottom + ch * _CHECK_POINTS[0][1])
        for fx, fy in _CHECK_POINTS[1:]:
            path.lineTo(left + cw * fx, y_bottom + ch * fy)
        c.drawPath(path, stroke=1, fill=0)
        return

    if symbol == "cross":
        for (x0, y0), (x1, y1) in _CROSS_LINES:
            c.line(left + cw * x0, y_bottom + ch * y0, left + cw * x1, y_bottom + ch * y1)
        return


def _rect_bottomleft(el: dict, page_w: float, page_h: float) -> Tuple[float, float, float, float]:
    """Convierte un rect en coords top-left (x,y,width,height) a reportlab
    (left, y_bottom, width, height), recortado a los límites de la página."""
    x = float(el["x"])
    y = float(el["y"])
    w = float(el["width"])
    h = float(el["height"])

    left = max(0.0, x)
    top = max(0.0, y)
    right = min(page_w, x + w)
    bottom_tl = min(page_h, y + h)

    cw = right - left
    ch = bottom_tl - top
    y_bottom = page_h - bottom_tl
    return left, y_bottom, cw, ch


def stamp_pdf(source_bytes: bytes, fields: List[dict], overlays: List[dict]) -> bytes:
    """Estampa `fields` y `overlays` sobre `source_bytes` (PDF). Devuelve PDF bytes."""
    reader = PdfReader(io.BytesIO(source_bytes))
    n_pages = len(reader.pages)
    sizes = [(float(p.mediabox.width), float(p.mediabox.height)) for p in reader.pages]

    # ── 1) PDF-overlay con reportlab ───────────────────────────────────────────
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for i in range(n_pages):
        page_w, page_h = sizes[i]
        c.setPageSize((page_w, page_h))

        # Overlays (coberturas)
        for ov in overlays:
            if int(ov["page"]) != i:
                continue
            left, y_bottom, cw, ch = _rect_bottomleft(ov, page_w, page_h)
            if cw <= 0 or ch <= 0:
                continue
            col = _color(ov.get("color") or [1.0, 1.0, 1.0])
            c.setFillColor(col)
            c.setStrokeColor(col)
            c.rect(left, y_bottom, cw, ch, fill=1, stroke=0)

        # Campos de texto (fondo opcional + texto con auto-wrap)
        for f in fields:
            if int(f["page"]) != i:
                continue
            left, y_bottom, cw, ch = _rect_bottomleft(f, page_w, page_h)
            if cw <= 0 or ch <= 0:
                continue

            if f.get("bg_color"):
                bg = _color(f["bg_color"])
                c.setFillColor(bg)
                c.setStrokeColor(bg)
                c.rect(left, y_bottom, cw, ch, fill=1, stroke=0)

            symbol = f.get("symbol")
            if symbol in ("check", "cross", "bullet"):
                _draw_symbol(
                    c, symbol, left, y_bottom, cw, ch,
                    _color(f.get("font_color") or [0.0, 0.0, 0.0]),
                    int(f.get("font_size", 12)),
                )
                continue

            text = f.get("text") or ""
            if not text:
                continue

            font = FONT_MAP.get(f.get("font_family", "Helvetica"), "Helvetica")
            size = int(f.get("font_size", 12))
            style = ParagraphStyle(
                "list_field",
                fontName=font,
                fontSize=size,
                leading=size * 1.2,
                textColor=_color(f.get("font_color") or [0.0, 0.0, 0.0]),
                alignment=TA_LEFT,
            )
            para = Paragraph(_xml_escape(text), style)
            frame = Frame(
                left + _TEXT_X_OFFSET, y_bottom, cw, ch,
                leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                showBoundary=0,
            )
            # addFromList recorta el excedente que no entra (paridad con insert_textbox).
            frame.addFromList([para], c)

        c.showPage()
    c.save()
    buf.seek(0)

    # ── 2) Fusionar overlay sobre el original ──────────────────────────────────
    overlay_reader = PdfReader(buf)
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        if i < len(overlay_reader.pages):
            page.merge_page(overlay_reader.pages[i])
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    logger.info("Estampado OK: %d páginas, %d campos, %d overlays", n_pages, len(fields), len(overlays))
    return out.getvalue()
