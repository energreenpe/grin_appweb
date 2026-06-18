import os
from io import BytesIO
from hashlib import md5
from jinja2 import Template
from xhtml2pdf import pisa
from xhtml2pdf.xhtml2pdf_reportlab import PmlImageReader
from app.modules.inspector.models import Visita
from app.modules.shared.models import EmpresaConfig


# ── Workaround de un bug de xhtml2pdf/reportlab (imágenes intercambiadas) ──────
# reportlab deduplica/identifica las imágenes externas por `str(objeto)` cuando no
# son ImageReader nativos. PmlImageReader (xhtml2pdf) usa el repr por defecto,
# basado en la DIRECCIÓN DE MEMORIA; si CPython reutiliza una dirección liberada,
# dos imágenes DISTINTAS comparten clave de caché y se intercambian en el PDF
# (intermitente, más probable con muchas imágenes). Forzamos una identidad basada
# en el CONTENIDO para que la deduplicación sea estable y correcta.
def _pml_content_repr(self) -> str:
    try:
        return "PmlImageReader:" + md5(self.getRGBData()).hexdigest()
    except Exception:
        return f"PmlImageReader:{id(self)}"

if not getattr(PmlImageReader, "_grin_repr_patched", False):
    PmlImageReader.__repr__ = _pml_content_repr
    PmlImageReader._grin_repr_patched = True

def generar_pdf_visita(visita: Visita, empresa: EmpresaConfig) -> bytes:
    # 1. HTML Base con Jinja2 (diseño básico y limpio)
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8" />
        <title>Reporte de Inspección Técnica</title>
        <style>
            @page { size: a4 portrait; margin: 1.4cm; }
            body { font-family: Helvetica, Arial, sans-serif; font-size: 11px; color: #333; }

            .header { border-bottom: 2px solid #62B989; padding-bottom: 8px; margin-bottom: 16px; }
            .header h1 { margin: 0; color: #62B989; font-size: 22px; }
            .header p { margin: 2px 0; font-size: 11px; color: #666; }

            .section { margin-bottom: 16px; }
            .section h2 { background-color: #f4f4f4; padding: 5px 8px; font-size: 13px; border-left: 4px solid #62B989; margin-bottom: 8px; }

            /* Datos en dos columnas (estilo banda label : valor) */
            .datos { width: 100%; border-collapse: collapse; }
            .datos td { padding: 3px 6px; font-size: 11px; vertical-align: top; }
            .datos .lbl { font-weight: bold; color: #444; text-transform: uppercase; font-size: 8.5px; width: 80px; white-space: nowrap; }

            .table { width: 100%; border-collapse: collapse; margin-top: 8px; }
            .table th, .table td { border: 1px solid #ddd; padding: 6px; text-align: left; font-size: 10px; }
            .table th { background-color: #f9f9f9; }

            /* Observaciones: subtítulo arriba, texto debajo */
            .obs-block { margin-bottom: 10px; }
            .obs-block .obs-title { font-weight: bold; color: #444; margin-bottom: 3px; }
            .obs-block .obs-text { color: #333; }

            /* Cada bloque de fotos empieza en página nueva y cabe en una sola hoja */
            .foto-page { page-break-before: always; page-break-inside: avoid; text-align: center; }
            .foto-page h2 { background-color: #f4f4f4; padding: 5px 8px; font-size: 13px; border-left: 4px solid #62B989; margin-bottom: 10px; text-align: left; }
            .foto-item { text-align: center; margin-bottom: 10px; }
            .foto-item img { height: 10cm; border: 1px solid #ccc; }

            /* Recibo de luz: una hoja completa (título + imagen vertical) */
            .recibo-page { page-break-before: always; page-break-inside: avoid; text-align: center; }
            .recibo-page h2 { background-color: #f4f4f4; padding: 5px 8px; font-size: 13px; border-left: 4px solid #62B989; margin-bottom: 10px; text-align: left; }
            .recibo-page img { height: 23cm; border: 1px solid #ccc; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>REPORTE DE INSPECCIÓN TÉCNICA</h1>
            <p><strong>{{ empresa.nombre if empresa else '' }}</strong>{% if empresa and empresa.ruc %} - RUC: {{ empresa.ruc }}{% endif %}</p>
            <p>Fecha de Inspección: {{ visita.fecha.strftime('%d/%m/%Y %H:%M') }}</p>
        </div>

        <div class="section">
            <h2>Datos del Cliente</h2>
            <table class="datos">
                <tr>
                    <td class="lbl">Señor(es)</td><td>{{ visita.cliente.nombre or '—' }}</td>
                    <td class="lbl">RUC / DNI</td><td>{{ visita.cliente.documento or '—' }}</td>
                </tr>
                <tr>
                    <td class="lbl">Dirección</td><td>{{ visita.cliente.direccion or '—' }}</td>
                    <td class="lbl">Teléfono</td><td>{{ visita.cliente.telefono or '—' }}</td>
                </tr>
                <tr>
                    <td class="lbl">Atención</td><td>{{ visita.cliente.atencion or '—' }}</td>
                    <td class="lbl">Correo</td><td>{{ visita.cliente.correo or '—' }}</td>
                </tr>
                <tr>
                    <td class="lbl">Referencia</td><td>{{ visita.cliente.referencia or '—' }}</td>
                    <td class="lbl">Tipo Cliente</td><td>{{ visita.tipo_cliente or '—' }}</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h2>Detalles del Sistema</h2>
            <table class="datos">
                <tr>
                    <td class="lbl">Tipo de Sistema</td><td>{{ visita.tipo_sistema or '—' }}</td>
                    <td class="lbl">Conexión Red</td><td>{{ visita.conexion_red or 'N/A' }}</td>
                </tr>
                <tr>
                    <td class="lbl">Tipo de Techo</td><td>{{ visita.tipo_techo or '—' }}</td>
                    <td class="lbl">Técnico</td><td>{{ visita.tecnico.nombre if visita.tecnico else 'No asignado' }}</td>
                </tr>
            </table>
        </div>

        {% if visita.cargas_aislado %}
        <div class="section">
            <h2>Levantamiento de Cargas Críticas</h2>
            <table class="table" repeat="1">
                <thead>
                    <tr>
                        <th>Equipo</th>
                        <th>Cant.</th>
                        <th>Potencia (W)</th>
                        <th>Horas/Día</th>
                        <th>Energía Total (Wh/día)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for carga in visita.cargas_aislado %}
                    <tr>
                        <td>{{ carga.nombre }}</td>
                        <td>{{ carga.cantidad_unidades }}</td>
                        <td>{{ carga.potencia_w }} W</td>
                        <td>{{ carga.horas_dia }} h</td>
                        <td>{{ (carga.cantidad_unidades * carga.potencia_w * carga.horas_dia) | int }} Wh</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        {% if visita.obs_techo or visita.obs_interior %}
        <div class="section">
            <h2>Observaciones</h2>
            {% if visita.obs_techo %}
            <div class="obs-block">
                <div class="obs-title">Techo / Sombras:</div>
                <div class="obs-text">{{ visita.obs_techo | e | replace('\r\n', '\n') | replace('\r', '\n') | replace('\n', '<br/>') }}</div>
            </div>
            {% endif %}
            {% if visita.obs_interior %}
            <div class="obs-block">
                <div class="obs-title">Interior / Tablero:</div>
                <div class="obs-text">{{ visita.obs_interior | e | replace('\r\n', '\n') | replace('\r', '\n') | replace('\n', '<br/>') }}</div>
            </div>
            {% endif %}
        </div>
        {% endif %}

        {# ── Recibo de luz: primera imagen, hoja completa ── #}
        {% if visita.recibo_ruta %}
        <div class="recibo-page">
            <h2>Recibo de Luz</h2>
            <img src="{{ request_base_url }}{{ visita.recibo_ruta }}" alt="Recibo" />
        </div>
        {% endif %}

        {# ── Fotos de techo: título + 2 imágenes por hoja ── #}
        {% for grupo in visita.fotos_techo | batch(2) %}
        <div class="foto-page">
            <h2>Registro Fotográfico - Techo</h2>
            {% for foto in grupo %}
            <div class="foto-item">
                <img src="{{ request_base_url }}{{ foto.url }}" alt="Techo" />
            </div>
            {% endfor %}
        </div>
        {% endfor %}

        {# ── Fotos de interior: título + 2 imágenes por hoja ── #}
        {% for grupo in visita.fotos_interior | batch(2) %}
        <div class="foto-page">
            <h2>Registro Fotográfico - Interior</h2>
            {% for foto in grupo %}
            <div class="foto-item">
                <img src="{{ request_base_url }}{{ foto.url }}" alt="Interior" />
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </body>
    </html>
    """
    
    # IMPORTANTE: En Windows, weasyprint da problemas con GTK+3. 
    # Usamos xhtml2pdf que funciona nativamente y es más estable.
    cwd = os.getcwd()
    request_base_url = f"{cwd}"

    template = Template(html_template)
    html_content = template.render(
        visita=visita, 
        empresa=empresa,
        request_base_url=request_base_url
    )

    pdf_buffer = BytesIO()
    # Escribimos el PDF
    pisa_status = pisa.CreatePDF(
        html_content, dest=pdf_buffer
    )
    
    if pisa_status.err:
        print("Error al generar PDF con xhtml2pdf")
        
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()
    
    return pdf_bytes
