"""
router.py — Endpoints HTTP del módulo PLANNER.

APIRouter SIN prefix: el prefijo `/api/planner` se aplica en `app/main.py`.

E2 (core): KPIs, proyectos, personal, cuadrillas + miembros, actividades.
Asistencia, feriados, Curva S, fotos y reportes PDF se agregan en E3–E6.
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.ratelimit import RateLimiter
from app.modules.planner import service
from app.modules.planner.schemas import (
    ProyectoCreate, ProyectoUpdate, ProyectoResponse,
    PersonalCreate, PersonalUpdate, PersonalResponse,
    CuadrillaCreate, CuadrillaUpdate, CuadrillaResponse,
    AsignarMiembroRequest, CambiarCuadrillaRequest, MiembroEnCuadrillaResponse,
    ActividadCreate, ActividadUpdate, ActividadResponse,
    AsistenciaCreate, AsistenciaUpdate, AsistenciaBulkCreate, AsistenciaResponse,
    CurvaSSnapshotResponse,
    FeriadoCreate, FeriadoResponse,
    FotoUpdate, FotoResponse,
    PlannerKPIResponse, MessageResponse,
)

router = APIRouter()

# Capa extra contra saturación por subida masiva de imágenes (infra grin_web).
_subir_foto_limit = RateLimiter(max_requests=20, window_seconds=60)
# Generar PDFs es costoso → limitar.
_pdf_limit = RateLimiter(max_requests=10, window_seconds=60)


def _pdf_response(contenido: bytes, nombre: str) -> Response:
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@router.get("/health")
def health():
    return {"status": "ok", "module": "planner"}


# ───────────────── KPIs ─────────────────
@router.get("/kpis", response_model=PlannerKPIResponse)
def kpis(db: Session = Depends(get_db)):
    return service.get_kpis(db)


# ───────────────── PROYECTOS ─────────────────
@router.get("/proyectos", response_model=List[ProyectoResponse])
def list_proyectos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return service.get_proyectos(db, skip, limit, estado)


@router.get("/proyectos/{pid}", response_model=ProyectoResponse)
def get_proyecto(pid: int, db: Session = Depends(get_db)):
    obj = service.get_proyecto(db, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return obj


@router.post("/proyectos", response_model=ProyectoResponse, status_code=201)
def create_proyecto(data: ProyectoCreate, db: Session = Depends(get_db)):
    return service.create_proyecto(db, data)


@router.patch("/proyectos/{pid}", response_model=ProyectoResponse)
def update_proyecto(pid: int, data: ProyectoUpdate, db: Session = Depends(get_db)):
    obj = service.update_proyecto(db, pid, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return obj


@router.delete("/proyectos/{pid}", response_model=MessageResponse)
def delete_proyecto(pid: int, db: Session = Depends(get_db)):
    if not service.delete_proyecto(db, pid):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"message": "Eliminado", "success": True}


# ───────────────── PERSONAL ─────────────────
@router.get("/personal", response_model=List[PersonalResponse])
def list_personal(estado: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return service.get_personal(db, estado=estado)


@router.post("/personal", response_model=PersonalResponse, status_code=201)
def create_persona(data: PersonalCreate, db: Session = Depends(get_db)):
    return service.create_persona(db, data)


@router.patch("/personal/{pid}", response_model=PersonalResponse)
def update_persona(pid: int, data: PersonalUpdate, db: Session = Depends(get_db)):
    obj = service.update_persona(db, pid, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return obj


@router.delete("/personal/{pid}", response_model=MessageResponse)
def delete_persona(pid: int, db: Session = Depends(get_db)):
    if not service.delete_persona(db, pid):
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return {"message": "Eliminado", "success": True}


# ───────────────── CUADRILLAS ─────────────────
@router.get("/proyectos/{pid}/cuadrillas", response_model=List[CuadrillaResponse])
def list_cuadrillas(pid: int, db: Session = Depends(get_db)):
    return service.get_cuadrillas_proyecto(db, pid)


@router.post("/cuadrillas", response_model=CuadrillaResponse, status_code=201)
def create_cuadrilla(data: CuadrillaCreate, db: Session = Depends(get_db)):
    return service.create_cuadrilla(db, data)


@router.patch("/cuadrillas/{cid}", response_model=CuadrillaResponse)
def update_cuadrilla(cid: int, data: CuadrillaUpdate, db: Session = Depends(get_db)):
    obj = service.update_cuadrilla(db, cid, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Cuadrilla no encontrada")
    return obj


@router.delete("/cuadrillas/{cid}", response_model=MessageResponse)
def delete_cuadrilla(cid: int, db: Session = Depends(get_db)):
    if not service.delete_cuadrilla(db, cid):
        raise HTTPException(status_code=404, detail="Cuadrilla no encontrada")
    return {"message": "Eliminado", "success": True}


# ── Miembros de cuadrilla ──
@router.post("/cuadrillas/{cid}/miembros", response_model=MiembroEnCuadrillaResponse, status_code=201)
def asignar_miembro(cid: int, data: AsignarMiembroRequest, db: Session = Depends(get_db)):
    return service.asignar_miembro(db, cid, data)


@router.post("/miembros/{mid}/cambiar-cuadrilla", response_model=MiembroEnCuadrillaResponse)
def cambiar_cuadrilla_miembro(mid: int, data: CambiarCuadrillaRequest, db: Session = Depends(get_db)):
    obj = service.cambiar_cuadrilla(db, mid, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    return obj


@router.delete("/miembros/{mid}", response_model=MessageResponse)
def remover_miembro(mid: int, db: Session = Depends(get_db)):
    if not service.remover_miembro(db, mid):
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    return {"message": "Eliminado", "success": True}


# ───────────────── ACTIVIDADES ─────────────────
@router.get("/proyectos/{pid}/actividades", response_model=List[ActividadResponse])
def list_actividades(pid: int, solo_raiz: bool = Query(False), db: Session = Depends(get_db)):
    return service.get_actividades_proyecto(db, pid, solo_raiz)


@router.post("/actividades", response_model=ActividadResponse, status_code=201)
def create_actividad(data: ActividadCreate, db: Session = Depends(get_db)):
    return service.create_actividad(db, data)


@router.patch("/actividades/{aid}", response_model=ActividadResponse)
def update_actividad(aid: int, data: ActividadUpdate, db: Session = Depends(get_db)):
    obj = service.update_actividad(db, aid, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return obj


@router.delete("/actividades/{aid}", response_model=MessageResponse)
def delete_actividad(aid: int, db: Session = Depends(get_db)):
    if not service.delete_actividad(db, aid):
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return {"message": "Eliminada", "success": True}


# ───────────────── GANTT ─────────────────
@router.post("/proyectos/{pid}/recalcular-gantt", response_model=ProyectoResponse)
def recalcular_gantt(pid: int, db: Session = Depends(get_db)):
    obj = service.recalcular_gantt(db, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return obj


# ───────────────── FOTOS (EVIDENCIA) ─────────────────
@router.get("/proyectos/{pid}/fotos", response_model=List[FotoResponse])
def list_fotos(
    pid: int,
    etapa: Optional[str] = Query(None),
    solo_pdf: bool = Query(False),
    db: Session = Depends(get_db),
):
    return service.get_fotos(db, pid, etapa, solo_pdf)


@router.post(
    "/proyectos/{pid}/fotos",
    response_model=FotoResponse,
    status_code=201,
    dependencies=[Depends(_subir_foto_limit)],
)
async def upload_foto(
    pid: int,
    file: UploadFile = File(...),
    etapa: str = Form("General"),
    etapa_codigo: str = Form("general"),
    subido_por: str = Form(""),
    emoji: str = Form("📷"),
    fecha: date = Form(...),
    comentario_pdf: str = Form(""),
    actividad_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    # Validar/convertir/guardar la imagen (medidas anti-DoS de INSPECTOR) antes de
    # tocar la BD. La validación de existencia del proyecto y la limpieza del
    # archivo huérfano viven en service.crear_foto.
    guardada = await service.guardar_foto_archivo(file, pid)
    return service.crear_foto(db, pid, {
        **guardada, "etapa": etapa, "etapa_codigo": etapa_codigo,
        "subido_por": subido_por, "emoji": emoji, "fecha": fecha,
        "comentario_pdf": comentario_pdf, "actividad_id": actividad_id,
        "nombre_original": file.filename or "",
    })


@router.patch("/fotos/{fid}", response_model=FotoResponse)
def update_foto(fid: int, data: FotoUpdate, db: Session = Depends(get_db)):
    obj = service.update_foto(db, fid, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    return obj


@router.delete("/fotos/{fid}", response_model=MessageResponse)
def delete_foto(fid: int, db: Session = Depends(get_db)):
    if not service.delete_foto(db, fid):
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    return {"message": "Eliminada", "success": True}


# ───────────────── REPORTES PDF ─────────────────
def _nombre_pdf(prefijo: str, proyecto_nombre: str, semana_num: int) -> str:
    safe = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in (proyecto_nombre or "proyecto"))
    return f"Reporte_{prefijo}_{safe}_S{semana_num}.pdf"


@router.get("/proyectos/{pid}/pdf/cliente", dependencies=[Depends(_pdf_limit)])
def pdf_cliente(
    pid: int,
    tipo: str = Query("semanal", description="semanal | rango"),
    semana_num: int = Query(1, ge=1),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    observaciones: str = Query(""),
    db: Session = Depends(get_db),
):
    contenido = service.pdf_cliente_bytes(db, pid, tipo, semana_num, fecha_desde, fecha_hasta, observaciones)
    proyecto = service.get_proyecto(db, pid)
    return _pdf_response(contenido, _nombre_pdf("Cliente", proyecto.nombre, semana_num))


@router.get("/proyectos/{pid}/pdf/oficina", dependencies=[Depends(_pdf_limit)])
def pdf_oficina(
    pid: int,
    tipo: str = Query("semanal", description="semanal | rango"),
    semana_num: int = Query(1, ge=1),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    observaciones: str = Query(""),
    db: Session = Depends(get_db),
):
    contenido = service.pdf_oficina_bytes(db, pid, tipo, semana_num, fecha_desde, fecha_hasta, observaciones)
    proyecto = service.get_proyecto(db, pid)
    return _pdf_response(contenido, _nombre_pdf("Oficina", proyecto.nombre, semana_num))


# ───────────────── FERIADOS ─────────────────
@router.get("/feriados", response_model=List[FeriadoResponse])
def list_feriados(
    region: Optional[str] = Query(None),
    anio: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    return service.get_feriados(db, region, anio)


@router.post("/feriados", response_model=FeriadoResponse, status_code=201)
def create_feriado(data: FeriadoCreate, db: Session = Depends(get_db)):
    return service.create_feriado(db, data)


@router.delete("/feriados/{fid}", response_model=MessageResponse)
def delete_feriado(fid: int, db: Session = Depends(get_db)):
    if not service.delete_feriado(db, fid):
        raise HTTPException(status_code=404, detail="Feriado no encontrado")
    return {"message": "Eliminado", "success": True}


# ───────────────── ASISTENCIA ─────────────────
@router.get("/proyectos/{pid}/asistencia", response_model=List[AsistenciaResponse])
def list_asistencia(pid: int, fecha: Optional[date] = Query(None), db: Session = Depends(get_db)):
    return service.get_asistencia(db, pid, fecha)


@router.post("/asistencia", response_model=AsistenciaResponse, status_code=201)
def create_asistencia(data: AsistenciaCreate, db: Session = Depends(get_db)):
    return service.create_asistencia(db, data)


@router.post("/asistencia/bulk", response_model=List[AsistenciaResponse], status_code=201)
def bulk_asistencia(data: AsistenciaBulkCreate, db: Session = Depends(get_db)):
    return service.bulk_asistencia(db, data)


@router.patch("/asistencia/{aid}", response_model=AsistenciaResponse)
def update_asistencia(aid: int, data: AsistenciaUpdate, db: Session = Depends(get_db)):
    obj = service.update_asistencia(db, aid, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Registro de asistencia no encontrado")
    return obj


@router.delete("/asistencia/{aid}", response_model=MessageResponse)
def delete_asistencia(aid: int, db: Session = Depends(get_db)):
    if not service.delete_asistencia(db, aid):
        raise HTTPException(status_code=404, detail="Registro de asistencia no encontrado")
    return {"message": "Eliminado", "success": True}


# ───────────────── CURVA S ─────────────────
@router.get("/proyectos/{pid}/curva-s", response_model=List[CurvaSSnapshotResponse])
def get_curva_s(pid: int, db: Session = Depends(get_db)):
    return service.get_curva_s(db, pid)


@router.post("/proyectos/{pid}/curva-s/snapshot", response_model=CurvaSSnapshotResponse, status_code=201)
def snapshot_curva_s(pid: int, db: Session = Depends(get_db)):
    obj = service.auto_snapshot(db, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return obj
