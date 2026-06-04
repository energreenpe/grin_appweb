import os
from io import BytesIO
from jinja2 import Template
from xhtml2pdf import pisa
from app.modules.inspector.models import Visita
from app.modules.quote.models import EmpresaConfig

def generar_pdf_visita(visita: Visita, empresa: EmpresaConfig) -> bytes:
    # 1. HTML Base con Jinja2 (diseño básico y limpio)
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8" />
        <title>Reporte de Inspección Técnica</title>
        <style>
            body { font-family: Helvetica, Arial, sans-serif; font-size: 12px; color: #333; }
            .header { border-bottom: 2px solid #62B989; padding-bottom: 10px; margin-bottom: 20px; }
            .header h1 { margin: 0; color: #62B989; font-size: 24px; }
            .header p { margin: 2px 0; font-size: 11px; color: #666; }
            
            .section { margin-bottom: 20px; }
            .section h2 { background-color: #f4f4f4; padding: 5px; font-size: 14px; border-left: 4px solid #62B989; margin-bottom: 10px; }
            
            .grid { width: 100%; }
            .row { width: 100%; margin-bottom: 5px; }
            .col { display: inline-block; width: 48%; vertical-align: top; }
            .label { font-weight: bold; color: #555; }
            
            .table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            .table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .table th { background-color: #f9f9f9; }
            
            .photo-grid { width: 100%; margin-top: 10px; }
            .photo-box { display: inline-block; width: 48%; margin: 1%; text-align: center; }
            .photo-box img { max-width: 100%; max-height: 200px; border: 1px solid #ccc; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>REPORTE DE INSPECCIÓN TÉCNICA</h1>
            <p><strong>{{ empresa.razon_social }}</strong> - RUC: {{ empresa.ruc }}</p>
            <p>Fecha de Inspección: {{ visita.fecha.strftime('%d/%m/%Y %H:%M') }}</p>
        </div>

        <div class="section">
            <h2>Datos del Cliente</h2>
            <div class="grid">
                <div class="row">
                    <div class="col"><span class="label">Cliente:</span> {{ visita.cliente.nombre }}</div>
                    <div class="col"><span class="label">Documento:</span> {{ visita.cliente.documento }}</div>
                </div>
                <div class="row">
                    <div class="col"><span class="label">Dirección:</span> {{ visita.cliente.direccion }}</div>
                    <div class="col"><span class="label">Teléfono:</span> {{ visita.cliente.telefono }}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Detalles del Sistema</h2>
            <div class="grid">
                <div class="row">
                    <div class="col"><span class="label">Tipo de Sistema:</span> {{ visita.tipo_sistema }}</div>
                    <div class="col"><span class="label">Conexión a Red:</span> {{ visita.conexion_red or 'N/A' }}</div>
                </div>
                <div class="row">
                    <div class="col"><span class="label">Tipo de Techo:</span> {{ visita.tipo_techo or 'N/A' }}</div>
                    <div class="col"><span class="label">Técnico:</span> {{ visita.tecnico.nombre if visita.tecnico else 'No asignado' }}</div>
                </div>
            </div>
        </div>

        {% if visita.cargas_aislado %}
        <div class="section">
            <h2>Levantamiento de Cargas Críticas</h2>
            <table class="table">
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
                <p><span class="label">Techo/Sombras:</span> {{ visita.obs_techo }}</p>
            {% endif %}
            {% if visita.obs_interior %}
                <p><span class="label">Interior/Tablero:</span> {{ visita.obs_interior }}</p>
            {% endif %}
        </div>
        {% endif %}

        <div style="page-break-after: always;"></div>

        <div class="section">
            <h2>Registro Fotográfico - Techo</h2>
            <div class="photo-grid">
                {% for foto in visita.fotos_techo %}
                <div class="photo-box">
                    <img src="{{ request_base_url }}{{ foto.url }}" alt="Techo" />
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="section">
            <h2>Registro Fotográfico - Interior</h2>
            <div class="photo-grid">
                {% for foto in visita.fotos_interior %}
                <div class="photo-box">
                    <img src="{{ request_base_url }}{{ foto.url }}" alt="Interior" />
                </div>
                {% endfor %}
            </div>
        </div>
        
        {% if visita.recibo_ruta %}
        <div class="section">
            <h2>Recibo de Luz</h2>
            <div class="photo-box">
                <img src="{{ request_base_url }}{{ visita.recibo_ruta }}" alt="Recibo" />
            </div>
        </div>
        {% endif %}
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
