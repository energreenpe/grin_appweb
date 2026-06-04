"""
pdf.py — Generación de PDF para cotizaciones.
Portado directamente desde QUOTE/cotizaciones.py (ReportLab canvas).
Mismas coordenadas, mismas fuentes, mismo layout — réplica exacta del diseño.
"""
from __future__ import annotations

import base64
import datetime
import json
import os
from collections import defaultdict
from io import BytesIO
from math import ceil

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from app.modules.quote.models import Cotizacion, EmpresaConfig, ItemCotizacion
from app.modules.quote.service import _moneda_codigo, calcular_totales

# ── Estilos de párrafo (igual que cotizaciones.py) ───────────────────────────
styles = getSampleStyleSheet()
style_normal = styles["Normal"]
style_normal.fontName = "Helvetica"
style_normal.fontSize = 6
style_normal.leading = 8


import re

def _clean_html_for_reportlab(text: str) -> str:
    if not text: return ""
    
    # 1. Eliminar bloques destructivos completos (scripts, styles, comentarios Word)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # 2. Mapear etiquetas de estructura a saltos de línea compatibles
    text = re.sub(r'<div>(.*?)</div>', r'<br/>\1', text, flags=re.IGNORECASE)
    text = re.sub(r'<div>', r'<br/>', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'<br/>\1', text, flags=re.IGNORECASE)
    text = re.sub(r'<br>', r'<br/>', text, flags=re.IGNORECASE)
    
    # 3. Mapear etiquetas modernas a etiquetas válidas de ReportLab
    text = re.sub(r'<strong[^>]*>', '<b>', text, flags=re.IGNORECASE)
    text = re.sub(r'</strong>', '</b>', text, flags=re.IGNORECASE)
    text = re.sub(r'<em[^>]*>', '<i>', text, flags=re.IGNORECASE)
    text = re.sub(r'</em>', '</i>', text, flags=re.IGNORECASE)
    
    # 4. Rescatar colores de spans a formato <font>
    text = re.sub(r'<span[^>]*style="[^"]*color:\s*([^;"]+)[^"]*"[^>]*>(.*?)</span>', r'<font color="\1">\2</font>', text, flags=re.IGNORECASE)
    
    # 5. Destruir cualquier otra etiqueta basura común (span vacíos, tablas, links, metas)
    text = re.sub(r'</?(span|div|p|h[1-6]|ul|li|ol|table|tbody|tr|td|th|a|img|meta|link)[^>]*>', '', text, flags=re.IGNORECASE)
    
    # 6. Eliminar caracteres invisibles (Zero-Width Spaces, etc.) que rompen el XML parser
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    
    return text

def _strip_all_html(text: str) -> str:
    # Fallback extremo para texto plano
    text = re.sub(r'<br/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    return text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')

def _draw_wrapped_text(c, text: str, x: float, y: float, max_width: float) -> float:
    """Réplica exacta de draw_wrapped_text en cotizaciones.py con protección HTML."""
    cleaned_text = _clean_html_for_reportlab(str(text))
    try:
        p = Paragraph(cleaned_text, style_normal)
        w, h = p.wrap(max_width, 100)
    except Exception as e:
        # Fallback a texto plano si el HTML es inválido para ReportLab
        plain = _strip_all_html(str(text))
        # Reemplazar saltos de linea reales por <br/>
        plain = plain.replace('\n', '<br/>')
        try:
            p = Paragraph(plain, style_normal)
            w, h = p.wrap(max_width, 100)
        except Exception:
            # Fallback final de emergencia vacio
            return y
            
    p.drawOn(c, x, y - h)
    return y - h - 2


def _draw_footer(c):
    """Réplica exacta de draw_footer en cotizaciones.py."""
    texto = "By Grin App"
    font = "Helvetica-BoldOblique"
    font_size = 8
    ancho_pagina, _ = A4
    y_footer = 20

    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.5)
    c.line(40, y_footer + 10, ancho_pagina - 40, y_footer + 10)

    c.setFillColor(colors.grey)
    c.setFont(font, font_size)
    w_texto = stringWidth(texto, font, font_size)
    c.drawString((ancho_pagina - w_texto) / 2, y_footer, texto)


def _check_page_space(c, y: float, required_space: float = 0) -> float:
    """Réplica exacta de check_page_space en cotizaciones.py."""
    MARGIN_BOTTOM = 40
    if y - required_space < MARGIN_BOTTOM:
        _draw_footer(c)
        c.showPage()
        _, alto = A4
        y = alto - 40  # MARGIN_TOP
    return y


# ── Directorio base del módulo ───────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def generar_pdf_cotizacion(
    cotizacion: Cotizacion,
    items: list[ItemCotizacion],
    empresa: EmpresaConfig,
) -> bytes:
    """
    Genera el PDF de cotización en memoria (BytesIO) y retorna bytes.
    Diseño réplica exacta de QUOTE/cotizaciones.py.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    ancho, alto = A4

    # ── Metadata / JSON embebido ──────────────────────────────────────────────
    datos_cotizacion = {
        "version_json": "1.0",
        "correlativo": cotizacion.correlativo,
        "datos_empresa": {
            "correo": empresa.email or "",
            "vendedor": cotizacion.vendedor_nombre or "",
            "telefono": cotizacion.vendedor_tel or "",
            "version": cotizacion.version or "1.0",
        },
        "datos_cliente": {
            "senores": cotizacion.cliente_nombre,
            "ruc": cotizacion.cliente_doc or "",
            "direccion": cotizacion.cliente_dir or "",
            "atencion": cotizacion.cliente_atencion or "",
            "referencia": cotizacion.cliente_referencia or "",
            "correo_cliente": cotizacion.cliente_correo or "",
            "celular_cliente": cotizacion.cliente_tel or "",
        },
        "configuracion": {
            "moneda": cotizacion.moneda,
            "mostrar_precios": cotizacion.mostrar_precios,
            "tipo_cambio": float(cotizacion.tipo_cambio),
            "utilidad": float(cotizacion.utilidad),
        },
        "productos": [
            {
                "cantidad": float(item.cantidad),
                "unidad": item.unidad,
                "descripcion": item.descripcion if item.descripcion else item.nombre,
                "precio": float(item.precio_unit),
                "subtotal": float(item.cantidad) * float(item.precio_unit),
                "partition": item.particion,
                "subpartition": item.subparticion or "",
            }
            for item in items
        ],
    }
    json_encoded = base64.b64encode(
        json.dumps(datos_cotizacion, ensure_ascii=False).encode("utf-8")
    ).decode("utf-8")

    fecha_num = datetime.datetime.now().strftime("%Y")
    num_cot   = cotizacion.correlativo.split("-")[-1] if cotizacion.correlativo else "0001"

    c.setTitle(f"Cotización {cotizacion.correlativo}")
    c.setAuthor("Energreen Perú - EnergiAI")
    c.setSubject(json_encoded)

    MARGIN_TOP    = 40
    MARGIN_BOTTOM = 40
    MARGIN_LEFT   = 30
    MARGIN_RIGHT  = 30

    # ── Logo ─────────────────────────────────────────────────────────────────
    logo_x, logo_y = 30, alto - 95
    logo_w, logo_h = 85, 75
    
    logo_path = None
    if empresa.logo_path and os.path.exists(empresa.logo_path):
        logo_path = empresa.logo_path

    if logo_path:
        try:
            c.drawImage(logo_path, logo_x, logo_y, width=logo_w, height=logo_h)
        except Exception:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(logo_x, logo_y + 20, "Energreen Perú")
    else:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(logo_x, logo_y + 20, "Energreen Perú")

    # ── Datos empresa (izquierda) ────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 7)
    c.drawString(45, logo_y - 5,  "E-mail:")
    c.drawString(45, logo_y - 14, "Vendedor:")
    c.drawString(45, logo_y - 23, "Teléfono:")
    c.drawString(45, logo_y - 32, "Dirección:")
    c.setFont("Helvetica", 7)
    c.drawString(90, logo_y - 5,  cotizacion.vendedor_correo or "")
    c.drawString(90, logo_y - 14, cotizacion.vendedor_nombre or "")
    c.drawString(90, logo_y - 23, cotizacion.vendedor_tel or "")
    c.drawString(90, logo_y - 32, empresa.direccion or "")

    # ── Cuadro RUC (derecha) ─────────────────────────────────────────────────
    ruc_rect_x = ancho - 205
    ruc_rect_y = alto - 85
    ruc_rect_w = 165
    ruc_rect_h = 45
    c.setLineWidth(0.1)
    c.rect(ruc_rect_x, ruc_rect_y, ruc_rect_w, ruc_rect_h)
    center_x = ruc_rect_x + ruc_rect_w / 2
    c.setFont("Helvetica", 9)
    c.drawCentredString(center_x, ruc_rect_y + 35, f"RUC: {empresa.ruc or ''}")
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(center_x, ruc_rect_y + 20, "COTIZACIÓN")
    c.setFont("Helvetica", 9)
    c.drawCentredString(center_x, ruc_rect_y + 5, f"N°: {cotizacion.correlativo}")

    # ── Cuadro cliente ───────────────────────────────────────────────────────
    rect_x = 30
    rect_y = alto - 205
    rect_w = ancho - 70
    rect_h = 72.5
    c.rect(rect_x, rect_y, rect_w, rect_h)

    c.setFont("Helvetica-Bold", 7)
    c.drawString(rect_x + 10, rect_y + rect_h - 15, "SEÑOR(ES):")
    c.drawString(rect_x + 10, rect_y + rect_h - 27, "RUC:")
    c.drawString(rect_x + 10, rect_y + rect_h - 39, "DIRECCIÓN:")
    c.drawString(rect_x + 10, rect_y + rect_h - 51, "ATENCIÓN:")
    c.drawString(rect_x + 10, rect_y + rect_h - 63, "REFERENCIA:")
    c.setFont("Helvetica", 7)
    c.drawString(rect_x + 60, rect_y + rect_h - 15, cotizacion.cliente_nombre or "")
    c.drawString(rect_x + 60, rect_y + rect_h - 27, cotizacion.cliente_doc or "")
    c.drawString(rect_x + 60, rect_y + rect_h - 39, cotizacion.cliente_dir or "")
    c.drawString(rect_x + 60, rect_y + rect_h - 51, cotizacion.cliente_atencion or "")
    c.drawString(rect_x + 60, rect_y + rect_h - 63, cotizacion.cliente_referencia or "")

    fecha_emision = datetime.datetime.today().strftime("%d/%m/%Y")
    c.setFont("Helvetica-Bold", 7)
    c.drawString(rect_x + rect_w - 170, rect_y + rect_h - 15, "FECHA EMISIÓN:")
    c.drawString(rect_x + rect_w - 170, rect_y + rect_h - 27, "CORREO:")
    c.drawString(rect_x + rect_w - 170, rect_y + rect_h - 39, "CELULAR:")
    c.drawString(rect_x + rect_w - 170, rect_y + rect_h - 51, "MONEDA:")
    c.setFont("Helvetica", 7)
    c.drawString(rect_x + rect_w - 110, rect_y + rect_h - 15, fecha_emision)
    c.drawString(rect_x + rect_w - 110, rect_y + rect_h - 27, cotizacion.cliente_correo or "")
    c.drawString(rect_x + rect_w - 110, rect_y + rect_h - 39, cotizacion.cliente_tel or "")
    c.drawString(rect_x + rect_w - 110, rect_y + rect_h - 51, cotizacion.moneda)

    # ── Encabezado tabla ─────────────────────────────────────────────────────
    tabla_y = rect_y - 5
    fila_h  = 13
    c.setLineWidth(0.5)
    c.rect(rect_x, tabla_y - fila_h, rect_w, fila_h)
    headers     = ["Cantidad", "Unidad", "Descripción", "Sub Total"]
    x_positions = [40, 90, 240, 500]
    c.setFont("Helvetica-Bold", 8)
    for i, header in enumerate(headers):
        c.drawString(x_positions[i], tabla_y - 10, header)

    x_positions_rows = [50, 95, 140, 490]
    y = tabla_y - fila_h - 2.5

    # Símbolo de moneda
    moneda_codigo = _moneda_codigo(cotizacion.moneda)
    if moneda_codigo == "PEN":
        symbol = "S/    "
    elif moneda_codigo == "USD":
        symbol = "$     "
    else:
        symbol = ""

    # ── Construir estructura de particiones ──────────────────────────────────
    # Réplica exacta de cotizaciones.py líneas 335-355
    from app.modules.quote.service import convertir_precio

    tipo_cambio = float(cotizacion.tipo_cambio)
    utilidad    = float(cotizacion.utilidad)

    # productos en formato (qty, unit, desc, price, subtotal, part, subpart)
    productos_data = []
    for item in items:
        subtotal_display = convertir_precio(
            precio=float(item.precio_unit) * float(item.cantidad),
            moneda_origen=item.moneda,
            moneda_destino=moneda_codigo,
            tipo_cambio=tipo_cambio,
            utilidad=utilidad,
        )
        desc = item.descripcion if item.descripcion else item.nombre
        productos_data.append((
            float(item.cantidad),
            item.unidad,
            desc,
            float(item.precio_unit),
            subtotal_display,
            item.particion,
            item.subparticion or None,
        ))

    partitions = defaultdict(lambda: defaultdict(list))
    for prod in productos_data:
        qty, unit, desc, price, subtotal, part, subpart = prod
        partitions[part][subpart].append((qty, unit, desc, price, subtotal))

    # Calcular totales por partición
    for part, subparts in partitions.items():
        part_total = 0
        for subpart, items_sp in list(subparts.items()):
            sub_total = sum(float(str(st)) for _, _, _, _, st in items_sp)
            subparts[subpart] = (items_sp, sub_total)
            part_total += sub_total
        subparts["__total__"] = part_total

        # Fila partición (gris oscuro)
        c.setFillColorRGB(115/255, 115/255, 115/255)
        c.rect(rect_x, y - 15, rect_w, fila_h, fill=1)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColorRGB(1, 1, 1)
        c.drawString(rect_x + 110, y - fila_h + 1.5, str(part).upper())
        c.drawRightString(rect_x + rect_w - 10, y - fila_h + 2, f"{symbol}{part_total:,.2f}")
        c.setFillColorRGB(0, 0, 0)
        y -= fila_h

        for subpart, data in subparts.items():
            if subpart == "__total__":
                continue
            items_sp, sub_total = data

            if subpart:
                # Fila subpartición (gris medio)
                c.setFillColorRGB(166/255, 166/255, 166/255)
                c.rect(rect_x, y - 15, rect_w, fila_h, fill=1)
                c.setFont("Helvetica-BoldOblique", 7)
                c.setFillColorRGB(0, 0, 0)
                c.drawString(rect_x + 110, y - fila_h + 1.5, str(subpart))
                c.drawRightString(rect_x + rect_w - 10, y - fila_h + 2, f"{symbol}{sub_total:,.2f}")
                y -= fila_h + 10
            else:
                y -= 10

            for qty, unit, desc, price, subtotal in items_sp:
                y = _check_page_space(c, y)
                try:
                    subtotal_val = float(str(subtotal))
                except Exception:
                    subtotal_val = 0.0

                c.setFont("Helvetica", 7)
                c.setFillColorRGB(0, 0, 0)
                c.drawString(x_positions_rows[0], y, str(qty))
                c.drawString(x_positions_rows[1], y, str(unit))

                desc_lines = str(desc).splitlines() or [""]
                for i, line in enumerate(desc_lines):
                    c.setFillColorRGB(0, 0, 0)
                    c.drawString(x_positions_rows[2], y, line)
                    if i == 0:
                        if cotizacion.mostrar_precios:
                            c.setFillColorRGB(0, 0, 0)
                        else:
                            c.setFillColorRGB(1, 1, 1)
                        c.drawRightString(rect_x + rect_w - 10, y, f"{symbol}{subtotal_val:,.2f}")
                    y -= 10
                c.setFillColorRGB(0, 0, 0)

    # ── Cuadro de totales ────────────────────────────────────────────────────
    total_general = sum(
        subparts["__total__"] for _, subparts in partitions.items()
    )
    igv           = total_general * 0.18
    total_con_igv = total_general + igv

    cuadro_w = 190
    cuadro_h = 35
    cuadro_x = rect_x + rect_w - cuadro_w
    cuadro_y = y - 50
    c.setLineWidth(0.5)
    c.line(rect_x, cuadro_y + cuadro_h + 5, rect_x + rect_w, cuadro_y + cuadro_h + 5)
    c.rect(cuadro_x, cuadro_y, cuadro_w, cuadro_h)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(cuadro_x + 5, cuadro_y + cuadro_h - 12, "VALOR VENTA:")
    c.drawString(cuadro_x + 5, cuadro_y + cuadro_h - 20, "I.G.V. (18%):")
    c.drawString(cuadro_x + 5, cuadro_y + cuadro_h - 28, "IMPORTE TOTAL:")
    c.setFont("Helvetica", 7)
    symbol_x = cuadro_x + cuadro_w - 50
    value_x  = cuadro_x + cuadro_w - 5
    c.drawString(symbol_x, cuadro_y + cuadro_h - 12, symbol)
    c.drawRightString(value_x, cuadro_y + cuadro_h - 12, f"{total_general:,.2f}")
    c.drawString(symbol_x, cuadro_y + cuadro_h - 20, symbol)
    c.drawRightString(value_x, cuadro_y + cuadro_h - 20, f"{igv:,.2f}")
    c.drawString(symbol_x, cuadro_y + cuadro_h - 28, symbol)
    c.drawRightString(value_x, cuadro_y + cuadro_h - 28, f"{total_con_igv:,.2f}")

    # ── Secciones de condiciones ─────────────────────────────────────────────
    y_cond = cuadro_y - 15

    # Técnicas
    if getattr(cotizacion, 'mostrar_cond_tecnicas', True):
        c.setFont("Helvetica-Bold", 6)
        c.drawString(rect_x, y_cond, "CONDICIONES TÉCNICAS:")
        y_cond -= 5
        for i, cond in enumerate(cotizacion.cond_tecnicas or []):
            y_cond = _check_page_space(c, y_cond)
            texto_limpio = re.sub(r'^(<[^>]+>)*\s*\d+\.?\d*\s*[-.)]*\s*', r'\1', cond.strip())
            c.setFont("Helvetica-Bold", 6)
            c.drawString(rect_x + 5, y_cond - 7, f"{i+1}.-")
            y_cond = _draw_wrapped_text(c, texto_limpio, rect_x + 20, y_cond, rect_w - 45)
            y_cond -= -2

    # Comerciales
    if getattr(cotizacion, 'mostrar_cond_comerciales', True):
        y_cond = _check_page_space(c, y_cond, 71)
        y_cond -= 20
        c.setFont("Helvetica-Bold", 6)
        c.drawString(rect_x, y_cond, "CONDICIONES COMERCIALES:")
        y_cond -= 10
        labels_comerciales = [
            "FORMA DE PAGO              :",
            "COSTO DE ENTREGA       :",
            "LUGAR DE ENTREGA       :",
            "TIEMPO DE ENTREGA      :",
            "TIEMPO DE EJECUCIÓN   :",
            "VALIDEZ DE OFERTA       :",
        ]
        cond_comerciales = cotizacion.cond_comerciales or []
        for i, lbl in enumerate(labels_comerciales):
            y_cond = _check_page_space(c, y_cond, 20)
            valor  = cond_comerciales[i] if i < len(cond_comerciales) else ""
            # Strip HTML for this simple field
            valor_plain = _strip_all_html(str(valor)).strip()
            c.setFont("Helvetica-Bold", 5.5)
            c.drawString(rect_x + 5, y_cond, lbl)
            c.setFont("Helvetica", 6)
            c.drawString(rect_x + 90, y_cond, valor_plain)
            y_cond -= 10

    # Otras
    if getattr(cotizacion, 'mostrar_cond_otras', True):
        y_cond = _check_page_space(c, y_cond, 55)
        y_cond -= 12.5
        c.setFont("Helvetica-Bold", 6)
        c.drawString(rect_x, y_cond, "OTRAS CONDICIONES:")
        y_cond -= 5
        for i, cond in enumerate(cotizacion.cond_otras or []):
            y_cond = _check_page_space(c, y_cond, 20)
            texto_limpio = re.sub(r'^(<[^>]+>)*\s*\d+\.?\d*\s*[-.)]*\s*', r'\1', cond.strip())
            c.setFont("Helvetica-Bold", 6)
            c.drawString(rect_x + 5, y_cond - 7, f"{i+1}.-")
            y_cond = _draw_wrapped_text(c, texto_limpio, rect_x + 20, y_cond, rect_w - 45)
            y_cond -= -2

    # Garantía equipos
    if getattr(cotizacion, 'mostrar_cond_garantia', True):
        y_cond = _check_page_space(c, y_cond, 56.7)
        y_cond -= 15
        c.setFont("Helvetica-Bold", 6)
        c.drawString(rect_x, y_cond, "GARANTÍA DE EQUIPOS:")
        y_cond -= 5
        for i, cond in enumerate(cotizacion.cond_garantia or []):
            y_cond = _check_page_space(c, y_cond, 20)
            texto_limpio = re.sub(r'^(<[^>]+>)*\s*\d+\.?\d*\s*[-.)]*\s*', r'\1', cond.strip())
            c.setFont("Helvetica-Bold", 6)
            c.drawString(rect_x + 5, y_cond - 7, f"{i+1}.-")
            y_cond = _draw_wrapped_text(c, texto_limpio, rect_x + 20, y_cond, rect_w - 45)
            y_cond -= -2

    # Garantía servicio
    if getattr(cotizacion, 'mostrar_cond_garantia_servicio', True):
        y_cond = _check_page_space(c, y_cond, 45)
        y_cond -= 15
        c.setFont("Helvetica-Bold", 6)
        c.drawString(rect_x, y_cond, "GARANTÍA DE SERVICIO:")
        y_cond -= 10
        c.setFont("Helvetica", 6)
        for linea in (cotizacion.cond_garantia_servicio or "").split("\n"):
            y_cond = _check_page_space(c, y_cond, 20)
            y_cond = _draw_wrapped_text(c, linea.strip(), rect_x + 5, y_cond, rect_w - 30)
            y_cond -= 2


    # Cuentas bancarias
    _ASSETS_DIR = os.path.join(_BASE_DIR, "..", "..", "..", "assets", "banks")

    cuentas_all = cotizacion.cuentas_bancarias or []
    cuentas = [c for c in cuentas_all if c.get("visible", True)]
    
    if cuentas and getattr(cotizacion, 'mostrar_cuentas_bancarias', True):
        filas_cuentas     = ceil(len(cuentas) / 2)
        row_height        = 70
        required_space_cb = filas_cuentas * row_height + 30
        y_cond = _check_page_space(c, y_cond, required_space_cb)
        y_cond -= 15
        c.setFont("Helvetica-Bold", 7)
        c.drawString(rect_x, y_cond, "CUENTAS BANCARIAS")
        y_cond -= 10

        left_x     = rect_x
        right_x    = rect_x + rect_w / 2 + 10

        for idx, cuenta in enumerate(cuentas):
            if idx % 2 == 0 and idx > 0:
                y_cond -= row_height
            y_cond = _check_page_space(c, y_cond, row_height)

            col_x  = left_x if idx % 2 == 0 else right_x
            y_base = y_cond

            # Resolver ruta del logo desde assets legacy
            logo_filename = cuenta.get("logo", "")
            logo_path_resolved = os.path.abspath(os.path.join(_ASSETS_DIR, logo_filename))
            if os.path.exists(logo_path_resolved):
                try:
                    c.drawImage(logo_path_resolved, col_x, y_base - 45, width=80, height=25, mask="auto")
                except Exception:
                    c.setFont("Helvetica-Bold", 6)
                    c.drawString(col_x, y_base - 20, f"[{cuenta.get('banco','')}]")
            else:
                c.setFont("Helvetica-Bold", 7)
                c.drawString(col_x, y_base - 20, cuenta.get('banco', ''))

            datos = cuenta.get("datos", {})
            dy = 20
            for label, valor in datos.items():
                c.setFont("Helvetica-Bold", 6)
                c.drawString(col_x + 90, y_base - dy, f"{label}:")
                c.setFont("Helvetica", 6)
                c.drawString(col_x + 135, y_base - dy, str(valor))
                dy += 10

        y_cond -= row_height


    _draw_footer(c)
    c.showPage()
    c.save()

    return buffer.getvalue()
