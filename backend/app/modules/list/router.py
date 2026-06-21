"""
router.py — Endpoints HTTP del módulo LIST.

APIRouter SIN prefix: el prefijo `/api/list` se aplica en `app/main.py`.

Endpoints (entregable #3):
- POST /upload         → valida y encola la conversión (o sirve .pdf directo). 202-style.
- GET  /jobs/{job_id}  → estado/resultado del job (polling del frontend).
- GET  /pdf/{filename} → sirve el PDF convertido (anti path-traversal vía storage).

La conversión pesada la ejecuta el worker; aquí solo se encola.
"""
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import storage
from app.db import get_db
from app.ratelimit import RateLimiter
from app.modules.list import service
from app.modules.list.schemas import (
    ExportPayload, ExportResponse, JobStatusOut, UploadResponse,
    ListPlantillaCreate, ListPlantillaListItem, ListPlantillaOut,
    ListDocumentoCreate, ListDocumentoUpdate, ListDocumentoListItem, ListDocumentoOut,
)

router = APIRouter()

# Anti-abuso por IP en endpoints costosos.
upload_limiter = RateLimiter(max_requests=20, window_seconds=60)
export_limiter = RateLimiter(max_requests=30, window_seconds=60)

PDF_SUBDIR = "list/pdf"
OUTPUT_SUBDIR = "list/output"


def _serve_pdf_seguro(subdir: str, filename: str):
    """Sirve un PDF de `uploads/<subdir>/` validando el nombre (anti path-traversal)."""
    if ("/" in filename) or ("\\" in filename) or (".." in filename) or not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido.")
    full = storage.resolve(f"uploads/{subdir}/{filename}")
    if not full:
        raise HTTPException(status_code=404, detail="PDF no encontrado.")
    return FileResponse(full, media_type="application/pdf", filename=filename)


@router.get("/health")
def health():
    """Salud del módulo LIST."""
    return {"status": "ok", "module": "list", "version": "1.0.0"}


@router.post("/upload", response_model=UploadResponse, dependencies=[Depends(upload_limiter)])
async def upload(file: UploadFile = File(...)):
    """Recibe un .pdf/.docx/.xlsx. Para Office encola la conversión (status=queued);
    para PDF lo sirve directo (status=finished)."""
    data = await file.read()
    return service.procesar_upload(data, file.filename or "documento")


@router.get("/jobs/{job_id}", response_model=JobStatusOut)
def job_status(job_id: str):
    """Estado de un job de conversión o estampado (polling)."""
    return service.estado_job(job_id)


@router.post("/export", response_model=ExportResponse, dependencies=[Depends(export_limiter)])
def export(payload: ExportPayload):
    """Encola el estampado de campos/overlays sobre el PDF base. Devuelve job_id."""
    return service.procesar_export(payload)


@router.get("/pdf/{filename}")
def serve_pdf(filename: str):
    """Sirve un PDF convertido (base del editor)."""
    return _serve_pdf_seguro(PDF_SUBDIR, filename)


@router.get("/output/{filename}")
def serve_output(filename: str):
    """Sirve un PDF estampado (resultado de exportar)."""
    return _serve_pdf_seguro(OUTPUT_SUBDIR, filename)


# ── Plantillas (PostgreSQL) ─────────────────────────────────────────────────────
@router.post("/templates", response_model=ListPlantillaOut)
def crear_plantilla(data: ListPlantillaCreate, db: Session = Depends(get_db)):
    """Guarda una configuración reutilizable de campos/overlays."""
    return service.crear_plantilla(db, data)


@router.get("/templates", response_model=List[ListPlantillaListItem])
def listar_plantillas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista las plantillas (sin el detalle de fields/overlays)."""
    return service.listar_plantillas(db, skip=skip, limit=limit)


@router.get("/templates/{plantilla_id}", response_model=ListPlantillaOut)
def obtener_plantilla(plantilla_id: int, db: Session = Depends(get_db)):
    """Devuelve una plantilla completa por id."""
    return service.obtener_plantilla(db, plantilla_id)


@router.delete("/templates/{plantilla_id}")
def eliminar_plantilla(plantilla_id: int, db: Session = Depends(get_db)):
    """Elimina una plantilla."""
    service.eliminar_plantilla(db, plantilla_id)
    return {"status": "deleted", "id": plantilla_id}


# ── Documentos (persistencia + resume) ──────────────────────────────────────────
@router.post("/documentos", response_model=ListDocumentoOut)
def crear_documento(data: ListDocumentoCreate, db: Session = Depends(get_db)):
    """Registra un documento convertido para poder reabrirlo y seguir editándolo."""
    return service.crear_documento(db, data)


@router.get("/documentos", response_model=List[ListDocumentoListItem])
def listar_documentos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista los documentos (más recientes primero), sin el detalle de fields/overlays."""
    return service.listar_documentos(db, skip=skip, limit=limit)


@router.get("/documentos/{documento_id}", response_model=ListDocumentoOut)
def obtener_documento(documento_id: int, db: Session = Depends(get_db)):
    """Devuelve un documento completo (incluye su avance de edición)."""
    return service.obtener_documento(db, documento_id)


@router.put("/documentos/{documento_id}", response_model=ListDocumentoOut)
def actualizar_documento(documento_id: int, data: ListDocumentoUpdate, db: Session = Depends(get_db)):
    """Autoguardado: persiste el avance (fields/overlays) del documento."""
    return service.actualizar_documento(db, documento_id, data)


@router.delete("/documentos/{documento_id}")
def eliminar_documento(documento_id: int, db: Session = Depends(get_db)):
    """Elimina el documento y su PDF base."""
    service.eliminar_documento(db, documento_id)
    return {"status": "deleted", "id": documento_id}
