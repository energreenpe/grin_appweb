"""
service.py — Lógica de negocio del módulo LIST.

Orquesta la conversión SIN ejecutar nada pesado en el proceso web:
- `procesar_upload`: valida, guarda el archivo vía `storage` y ENCOLA la conversión
  en la cola `conversion` (la ejecuta el worker). Atajo síncrono para .pdf.
- `estado_job`: consulta el estado/resultado de un job en RQ (polling del frontend).

La tarea se encola por RUTA de string para que `app/` no importe `workers/`.

Convención (como MATH): se lanza `HTTPException` directo ante errores de negocio.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException
from rq.exceptions import NoSuchJobError
from rq.job import Job
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import storage
from app.queue import QUEUE_CONVERSION, QUEUE_EXPORT, get_queue, get_redis
from app.modules.list.models import ListDocumento
from app.modules.list.schemas import (
    ExportPayload, ListDocumentoCreate, ListDocumentoUpdate,
)

# Tareas encolables (rutas de import resueltas por el worker).
_CONVERT_TASK = "workers.tasks.convert.convert_document"
_EXPORT_TASK = "workers.tasks.export.stamp_document"

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
INCOMING_SUBDIR = "list/incoming"
PDF_SUBDIR = "list/pdf"


def _es_nombre_pdf_seguro(name: str) -> bool:
    return not (("/" in name) or ("\\" in name) or (".." in name)) and name.lower().endswith(".pdf")


def _contenido_coincide_extension(ext: str, data: bytes) -> bool:
    """Validación ligera de magic-bytes: el contenido real debe coincidir con la
    extensión declarada (no confiar solo en el nombre). PDF empieza con '%PDF';
    DOCX/XLSX son contenedores ZIP (cabecera 'PK\\x03\\x04')."""
    if ext == ".pdf":
        return data[:4] == b"%PDF"
    if ext in (".docx", ".xlsx"):
        return data[:4] == b"PK\x03\x04"
    return False


def procesar_upload(data: bytes, filename: str) -> dict:
    """Valida el archivo subido y, según el tipo, lo sirve directo (.pdf) o encola
    su conversión a PDF (DOCX/XLSX)."""
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado. Válidos: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    if not data:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo excede el límite de {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )
    if not _contenido_coincide_extension(ext, data):
        raise HTTPException(
            status_code=400,
            detail="El contenido del archivo no coincide con su extensión.",
        )

    # Atajo: un PDF no necesita conversión, se guarda y se sirve directo.
    if ext == ".pdf":
        pdf_name = f"{uuid.uuid4().hex}.pdf"
        storage.save_bytes(data, PDF_SUBDIR, pdf_name)
        return {
            "job_id": None,
            "status": "finished",
            "pdf_name": pdf_name,
            "pdf_url": f"/api/list/pdf/{pdf_name}",
        }

    # DOCX/XLSX → guardar entrada y encolar conversión en el worker.
    rel_in = storage.save_bytes(data, INCOMING_SUBDIR, f"{uuid.uuid4().hex}{ext}")
    job = get_queue(QUEUE_CONVERSION).enqueue(_CONVERT_TASK, rel_in, filename)
    return {"job_id": job.id, "status": "queued", "pdf_name": None, "pdf_url": None}


def estado_job(job_id: str) -> dict:
    """Estado actual de un job de conversión; incluye pdf_url si terminó."""
    try:
        job = Job.fetch(job_id, connection=get_redis())
    except NoSuchJobError:
        raise HTTPException(status_code=404, detail="Job no encontrado o expirado.")

    status = job.get_status()
    out = {
        "job_id": job_id, "status": status,
        "pdf_name": None, "pdf_url": None, "result": None, "error": None,
    }

    if status == "finished" and isinstance(job.result, dict):
        out["result"] = job.result
        # Conveniencia para jobs de conversión.
        out["pdf_name"] = job.result.get("pdf_name")
        out["pdf_url"] = job.result.get("pdf_url")
    elif status == "failed":
        info = (job.exc_info or "").strip()
        out["error"] = info.splitlines()[-1] if info else "Error desconocido en la tarea."

    return out


def procesar_export(payload: ExportPayload) -> dict:
    """Valida que el PDF base exista y encola el estampado en la cola `export`."""
    if not _es_nombre_pdf_seguro(payload.pdf_name):
        raise HTTPException(status_code=400, detail="Nombre de PDF inválido.")
    if not storage.resolve(f"uploads/{PDF_SUBDIR}/{payload.pdf_name}"):
        raise HTTPException(status_code=404, detail="El PDF base no existe o expiró.")

    fields = [f.model_dump() for f in payload.fields]
    overlays = [o.model_dump() for o in payload.overlays]

    job = get_queue(QUEUE_EXPORT).enqueue(_EXPORT_TASK, payload.pdf_name, fields, overlays)
    return {"job_id": job.id, "status": "queued"}


# ── CRUD de documentos (persistencia + resume) ──────────────────────────────────
def crear_documento(db: Session, data: ListDocumentoCreate) -> ListDocumento:
    if not _es_nombre_pdf_seguro(data.pdf_name):
        raise HTTPException(status_code=400, detail="Nombre de PDF inválido.")
    if not storage.resolve(f"uploads/{PDF_SUBDIR}/{data.pdf_name}"):
        raise HTTPException(status_code=404, detail="El PDF base no existe o expiró.")

    doc = ListDocumento(
        nombre=data.nombre,
        pdf_name=data.pdf_name,
        fields=[f.model_dump() for f in data.fields],
        overlays=[o.model_dump() for o in data.overlays],
    )
    db.add(doc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear el documento.")
    db.refresh(doc)
    return doc


def listar_documentos(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(ListDocumento)
        .order_by(ListDocumento.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def obtener_documento(db: Session, documento_id: int) -> ListDocumento:
    doc = db.query(ListDocumento).filter(ListDocumento.id == documento_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    return doc


def actualizar_documento(db: Session, documento_id: int, data: ListDocumentoUpdate) -> ListDocumento:
    doc = obtener_documento(db, documento_id)
    if data.nombre is not None:
        doc.nombre = data.nombre
    if data.fields is not None:
        doc.fields = [f.model_dump() for f in data.fields]
    if data.overlays is not None:
        doc.overlays = [o.model_dump() for o in data.overlays]
    db.commit()
    db.refresh(doc)
    return doc


def eliminar_documento(db: Session, documento_id: int) -> None:
    doc = obtener_documento(db, documento_id)
    # Borra el PDF base permanente del documento.
    storage.delete(f"uploads/{PDF_SUBDIR}/{doc.pdf_name}")
    db.delete(doc)
    db.commit()
