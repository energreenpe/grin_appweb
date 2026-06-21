"""
Módulo LIST — editor visual de documentos: subir DOCX/XLSX/PDF, estampar campos y
overlays sobre el PDF y exportar el resultado.

Aislado como el resto de módulos (cero imports cruzados con quote/math/inspector).
La conversión pesada (LibreOffice) y el estampado se ejecutan en el worker
(`workers/`), no dentro de FastAPI; el módulo solo encola vía `app.queue`.
"""
