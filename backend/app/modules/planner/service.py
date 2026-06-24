"""
service.py — Lógica del módulo PLANNER (subset core E2).

Patrón grin_web: lanza `HTTPException` directo; `IntegrityError` → 400.
El cálculo de avance es por ahora lineal (portado del fork); en E4 se reemplaza
por el motor real (días laborables + feriados + dependencias).
"""
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile
from PIL import Image
from PIL.Image import DecompressionBombError
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app import storage
from app.modules.planner.models import (
    Proyecto, Personal, Cuadrilla, MiembroCuadrilla,
    Actividad, DependenciaActividad, Asistencia, CurvaSSnapshot, Feriado, Foto,
)
from app.modules.planner import schemas, scheduler

# ── Subida de imágenes (mismas medidas que INSPECTOR + storage anti-traversal) ──
MAX_FILE_BYTES = 10 * 1024 * 1024                 # 10 MB por archivo
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic", ".heif"}
Image.MAX_IMAGE_PIXELS = 64_000_000               # ~64 MP: corta "decompression bombs"


def _commit(db: Session):
    """Commit con traducción de IntegrityError (FK/constraint) a 400."""
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Violación de integridad de datos") from exc


# ───────────────── KPIs ─────────────────
def get_kpis(db: Session) -> dict:
    total       = db.query(Proyecto).count()
    activos     = db.query(Proyecto).filter(Proyecto.estado == "En Progreso").count()
    completados = db.query(Proyecto).filter(Proyecto.estado == "Completado").count()
    total_personal   = db.query(Personal).count()
    personal_activo  = db.query(Personal).filter(Personal.estado == "Activo").count()
    total_cuadrillas = db.query(Cuadrilla).count()
    proyectos = db.query(Proyecto).all()
    total_paneles    = sum(p.paneles or 0 for p in proyectos)
    avance_real_prom = round(sum(p.avance_real or 0 for p in proyectos) / total, 1) if total else 0.0
    avance_plan_prom = round(sum(p.avance_planificado or 0 for p in proyectos) / total, 1) if total else 0.0
    return {
        "total_proyectos": total, "proyectos_activos": activos,
        "proyectos_completados": completados, "total_paneles": total_paneles,
        "promedio_avance_real": avance_real_prom,
        "promedio_avance_planificado": avance_plan_prom,
        "total_personal": total_personal, "personal_activo": personal_activo,
        "total_cuadrillas": total_cuadrillas,
    }


# ───────────────── PROYECTOS ─────────────────
def get_proyectos(db: Session, skip: int = 0, limit: int = 100, estado: Optional[str] = None):
    q = db.query(Proyecto)
    if estado:
        q = q.filter(Proyecto.estado == estado)
    return q.order_by(Proyecto.created_at.desc()).offset(skip).limit(limit).all()


def get_proyecto(db: Session, pid: int):
    return db.query(Proyecto).filter(Proyecto.id == pid).first()


def create_proyecto(db: Session, data: schemas.ProyectoCreate):
    obj = Proyecto(**data.model_dump())
    db.add(obj)
    _commit(db)
    db.refresh(obj)
    return obj


def update_proyecto(db: Session, pid: int, data: schemas.ProyectoUpdate):
    obj = get_proyecto(db, pid)
    if not obj:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    _commit(db)
    db.refresh(obj)
    return obj


def delete_proyecto(db: Session, pid: int) -> bool:
    obj = get_proyecto(db, pid)
    if not obj:
        return False
    # El cascade de la BD borra las filas de fotos, pero NO los archivos del disco.
    # Limpiar los archivos y la carpeta del proyecto antes de eliminarlo.
    for foto in obj.fotos:
        storage.delete(foto.ruta)
    db.delete(obj)
    _commit(db)
    storage.delete_dir(f"planner/{pid}")
    return True


# ───────────────── PERSONAL ─────────────────
def get_personal(db: Session, estado: Optional[str] = None):
    q = db.query(Personal)
    if estado:
        q = q.filter(Personal.estado == estado)
    return q.order_by(Personal.nombre).all()


def create_persona(db: Session, data: schemas.PersonalCreate):
    obj = Personal(**data.model_dump())
    db.add(obj)
    _commit(db)
    db.refresh(obj)
    return obj


def update_persona(db: Session, pid: int, data: schemas.PersonalUpdate):
    obj = db.query(Personal).filter(Personal.id == pid).first()
    if not obj:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    _commit(db)
    db.refresh(obj)
    return obj


def delete_persona(db: Session, pid: int) -> bool:
    obj = db.query(Personal).filter(Personal.id == pid).first()
    if not obj:
        return False
    db.delete(obj)
    _commit(db)
    return True


# ───────────────── CUADRILLAS ─────────────────
def get_cuadrillas_proyecto(db: Session, proyecto_id: int):
    # joinedload de miembros→persona; el schema deriva nombre_persona (sin hacks).
    return (
        db.query(Cuadrilla)
        .filter(Cuadrilla.proyecto_id == proyecto_id)
        .options(joinedload(Cuadrilla.miembros).joinedload(MiembroCuadrilla.persona))
        .order_by(Cuadrilla.created_at)
        .all()
    )


def create_cuadrilla(db: Session, data: schemas.CuadrillaCreate):
    obj = Cuadrilla(**data.model_dump())
    db.add(obj)
    _commit(db)
    db.refresh(obj)
    return obj


def update_cuadrilla(db: Session, cid: int, data: schemas.CuadrillaUpdate):
    obj = db.query(Cuadrilla).filter(Cuadrilla.id == cid).first()
    if not obj:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    _commit(db)
    db.refresh(obj)
    return obj


def delete_cuadrilla(db: Session, cid: int) -> bool:
    obj = db.query(Cuadrilla).filter(Cuadrilla.id == cid).first()
    if not obj:
        return False
    db.delete(obj)
    _commit(db)
    return True


def asignar_miembro(db: Session, cuadrilla_id: int, data: schemas.AsignarMiembroRequest):
    # Idempotente: si ya está en la cuadrilla, devolver la asignación existente.
    existente = db.query(MiembroCuadrilla).filter(
        MiembroCuadrilla.cuadrilla_id == cuadrilla_id,
        MiembroCuadrilla.persona_id   == data.persona_id,
    ).first()
    if existente:
        return existente
    obj = MiembroCuadrilla(
        cuadrilla_id  = cuadrilla_id,
        persona_id    = data.persona_id,
        rol_interno   = data.rol_interno,
        fecha_ingreso = data.fecha_ingreso or date.today(),
        activo        = True,
    )
    db.add(obj)
    _commit(db)
    db.refresh(obj)
    return obj


def cambiar_cuadrilla(db: Session, miembro_id: int, data: schemas.CambiarCuadrillaRequest):
    obj = db.query(MiembroCuadrilla).filter(MiembroCuadrilla.id == miembro_id).first()
    if not obj:
        return None
    obj.cuadrilla_id = data.nueva_cuadrilla_id
    obj.rol_interno  = data.rol_interno
    _commit(db)
    db.refresh(obj)
    return obj


def remover_miembro(db: Session, miembro_id: int) -> bool:
    obj = db.query(MiembroCuadrilla).filter(MiembroCuadrilla.id == miembro_id).first()
    if not obj:
        return False
    db.delete(obj)
    _commit(db)
    return True


# ───────────────── ACTIVIDADES ─────────────────
def get_actividades_proyecto(db: Session, proyecto_id: int, solo_raiz: bool = False):
    q = db.query(Actividad).filter(Actividad.proyecto_id == proyecto_id)
    if solo_raiz:
        q = q.filter(Actividad.padre_id.is_(None))
    return q.order_by(Actividad.orden).all()


def create_actividad(db: Session, data: schemas.ActividadCreate):
    deps = data.dependencias
    d = data.model_dump(exclude={"dependencias"})
    # subtareas: columna JSON → guardar lista de dicts directamente (sin json.dumps).
    d["subtareas"] = [s.model_dump() for s in (data.subtareas or [])]
    obj = Actividad(**d)
    db.add(obj)
    _commit(db)
    db.refresh(obj)
    for dep in deps:
        db.add(DependenciaActividad(
            actividad_id=obj.id, depende_de_id=dep.depende_de_id,
            tipo=dep.tipo, lag_dias=dep.lag_dias,
        ))
    if deps:
        _commit(db)
        db.refresh(obj)
    recalcular_gantt(db, obj.proyecto_id)
    db.refresh(obj)
    return obj


def update_actividad(db: Session, aid: int, data: schemas.ActividadUpdate):
    obj = db.query(Actividad).filter(Actividad.id == aid).first()
    if not obj:
        return None
    upd = data.model_dump(exclude_unset=True)
    if upd.get("subtareas") is not None:
        upd["subtareas"] = [s for s in upd["subtareas"]]  # ya son dicts (model_dump)
    for k, v in upd.items():
        setattr(obj, k, v)
    _commit(db)
    db.refresh(obj)
    recalcular_gantt(db, obj.proyecto_id)
    db.refresh(obj)
    return obj


def delete_actividad(db: Session, aid: int) -> bool:
    obj = db.query(Actividad).filter(Actividad.id == aid).first()
    if not obj:
        return False
    pid = obj.proyecto_id
    db.delete(obj)
    _commit(db)
    recalcular_gantt(db, pid)
    return True


# ───────────────── MOTOR DE CRONOGRAMA (E4) ─────────────────
def _feriados_proyecto(db: Session, proyecto: Proyecto) -> set:
    """Feriados aplicables a un proyecto: todos los nacionales + los regionales
    de su región."""
    q = db.query(Feriado).filter(
        or_(
            Feriado.tipo == "Nacional",
            (Feriado.tipo == "Regional") & (Feriado.region == (proyecto.region or "")),
        )
    )
    return {f.fecha for f in q.all()}


def _avance_planificado(proyecto: Proyecto, feriados: set, hoy: Optional[date] = None) -> float:
    """% de días laborables transcurridos del proyecto (0–100)."""
    if not (proyecto.fecha_inicio and proyecto.fecha_fin):
        return 0.0
    hoy = hoy or date.today()
    total = scheduler.contar_laborables(proyecto.fecha_inicio, proyecto.fecha_fin, feriados)
    if total <= 0:
        return 0.0
    fin_efectivo = min(hoy, proyecto.fecha_fin)
    trans = scheduler.contar_laborables(proyecto.fecha_inicio, fin_efectivo, feriados) if fin_efectivo >= proyecto.fecha_inicio else 0
    return round(min(max(trans / total * 100, 0), 100), 1)


def recalcular_gantt(db: Session, proyecto_id: int):
    """Recalcula el cronograma (fechas plan por días laborables + dependencias FS)
    y el avance del proyecto. Reemplaza el cálculo lineal del fork."""
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not p:
        return None
    acts = db.query(Actividad).filter(Actividad.proyecto_id == proyecto_id).all()
    feriados = _feriados_proyecto(db, p)

    # Propagación de fechas según dependencias FS+lag (motor puro).
    act_ids = {a.id for a in acts}
    deps = (
        db.query(DependenciaActividad)
        .filter(DependenciaActividad.actividad_id.in_(act_ids or {0}))
        .all()
    )
    sched = scheduler.recalcular_cronograma(
        [{"id": a.id, "fecha_inicio_plan": a.fecha_inicio_plan,
          "duracion_dias": a.duracion_dias, "es_hito": a.es_hito} for a in acts],
        [{"actividad_id": d.actividad_id, "depende_de_id": d.depende_de_id,
          "tipo": d.tipo, "lag_dias": d.lag_dias} for d in deps],
        feriados,
    )
    for a in acts:
        s = sched.get(a.id)
        if s and s["fecha_inicio_plan"] is not None:
            a.fecha_inicio_plan = s["fecha_inicio_plan"]
            a.fecha_fin_plan = s["fecha_fin_plan"]

    # Avance REAL: actividades raíz (nivel>0) completadas.
    raiz = [a for a in acts if a.padre_id is None and a.nivel > 0]
    p.avance_real = round(sum(1 for a in raiz if a.estado == "Completado") / len(raiz) * 100, 1) if raiz else 0.0
    # Avance PLANIFICADO: por días laborables.
    p.avance_planificado = _avance_planificado(p, feriados)
    db.commit()
    return p


# ───────────────── FERIADOS ─────────────────
def get_feriados(db: Session, region: Optional[str] = None, anio: Optional[int] = None):
    q = db.query(Feriado)
    if region:
        q = q.filter(or_(Feriado.tipo == "Nacional", Feriado.region == region))
    if anio:
        q = q.filter(Feriado.anio == anio)
    return q.order_by(Feriado.fecha).all()


def create_feriado(db: Session, data: schemas.FeriadoCreate):
    payload = data.model_dump()
    if payload.get("anio") is None:
        payload["anio"] = payload["fecha"].year
    obj = Feriado(**payload)
    db.add(obj)
    _commit(db)
    db.refresh(obj)
    return obj


def delete_feriado(db: Session, fid: int) -> bool:
    obj = db.query(Feriado).filter(Feriado.id == fid).first()
    if not obj:
        return False
    db.delete(obj)
    _commit(db)
    return True


# ───────────────── ASISTENCIA ─────────────────
def get_asistencia(db: Session, proyecto_id: int, fecha: Optional[date] = None):
    q = (
        db.query(Asistencia)
        .filter(Asistencia.proyecto_id == proyecto_id)
        .options(joinedload(Asistencia.persona))
    )
    if fecha:
        q = q.filter(Asistencia.fecha == fecha)
    return q.order_by(Asistencia.fecha.desc(), Asistencia.id).all()


def create_asistencia(db: Session, data: schemas.AsistenciaCreate):
    obj = Asistencia(**data.model_dump())
    db.add(obj)
    _commit(db)
    db.refresh(obj)
    return obj


def bulk_asistencia(db: Session, data: schemas.AsistenciaBulkCreate):
    """Upsert por (proyecto_id, persona_id, fecha): si ya hay registro ese día,
    actualiza estado/hora/observacion; si no, lo crea."""
    resultado = []
    for item in data.registros:
        ex = db.query(Asistencia).filter(
            Asistencia.proyecto_id == data.proyecto_id,
            Asistencia.persona_id  == item.persona_id,
            Asistencia.fecha       == data.fecha,
        ).first()
        if ex:
            ex.estado      = item.estado
            ex.hora        = item.hora
            ex.observacion = item.observacion
            if data.registrado_por:
                ex.registrado_por = data.registrado_por
            resultado.append(ex)
        else:
            nuevo = Asistencia(
                proyecto_id=data.proyecto_id, persona_id=item.persona_id,
                fecha=data.fecha, estado=item.estado, hora=item.hora,
                observacion=item.observacion, registrado_por=data.registrado_por,
            )
            db.add(nuevo)
            resultado.append(nuevo)
    _commit(db)
    for r in resultado:
        db.refresh(r)
    return resultado


def update_asistencia(db: Session, aid: int, data: schemas.AsistenciaUpdate):
    obj = db.query(Asistencia).filter(Asistencia.id == aid).first()
    if not obj:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    _commit(db)
    db.refresh(obj)
    return obj


def delete_asistencia(db: Session, aid: int) -> bool:
    obj = db.query(Asistencia).filter(Asistencia.id == aid).first()
    if not obj:
        return False
    db.delete(obj)
    _commit(db)
    return True


# ───────────────── CURVA S ─────────────────
def get_curva_s(db: Session, proyecto_id: int):
    return (
        db.query(CurvaSSnapshot)
        .filter(CurvaSSnapshot.proyecto_id == proyecto_id)
        .order_by(CurvaSSnapshot.fecha)
        .all()
    )


def auto_snapshot(db: Session, proyecto_id: int):
    """Registra un punto de control de la Curva S con el avance del día.

    El avance planificado usa el motor de días laborables (mismo que el Gantt).
    """
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not p:
        return None
    hoy = date.today()
    avance_plan = _avance_planificado(p, _feriados_proyecto(db, p), hoy)
    acts = db.query(Actividad).filter(Actividad.proyecto_id == proyecto_id).all()
    obj = CurvaSSnapshot(
        proyecto_id=proyecto_id, fecha=hoy,
        avance_planificado=avance_plan, avance_real=p.avance_real or 0.0,
        actividades_total=len(acts),
        actividades_hechas=sum(1 for a in acts if a.estado == "Completado"),
    )
    db.add(obj)
    _commit(db)
    db.refresh(obj)
    return obj


# ───────────────── FOTOS (EVIDENCIA) ─────────────────
def _sanitizar_stem(filename: Optional[str]) -> str:
    """Nombre base seguro (sin rutas ni caracteres raros) — cierra path traversal."""
    stem = Path(filename or "foto").stem
    limpio = "".join(c for c in stem if c.isalnum() or c in ("-", "_"))
    return limpio or "foto"


async def guardar_foto_archivo(file: UploadFile, proyecto_id: int) -> dict:
    """Valida y persiste una imagen replicando las medidas de INSPECTOR:
    content-type imagen, tope de tamaño que aborta ANTES de tocar disco (413),
    guardia anti decompression-bomb, nombre saneado y conversión a WebP. El
    guardado va por `app.storage` (ruta relativa anti-traversal, S3-ready).
    Devuelve {ruta, nombre, mime_type}.
    """
    # 1. Debe ser imagen.
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen.")

    # 2. Leer por chunks acotando memoria; rechazar ANTES de escribir a disco.
    contents = bytearray()
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        contents.extend(chunk)
        if len(contents) > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"La imagen supera el tamaño máximo de {MAX_FILE_BYTES // (1024 * 1024)} MB.",
            )
    contents = bytes(contents)
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    safe_stem = _sanitizar_stem(file.filename)
    subdir = f"planner/{proyecto_id}"

    # 3. Convertir a WebP con guardia anti decompression-bomb. La decodificación de
    # PIL ES la validación real (más fuerte que mirar magic-bytes): si no es una
    # imagen genuina, falla y se rechaza (salvo HEIC/HEIF, que se guardan tal cual).
    try:
        image = Image.open(BytesIO(contents))
        if image.mode == "P":
            image = image.convert("RGBA")
        buf = BytesIO()
        image.save(buf, "WEBP", quality=80)
        ruta = storage.save_bytes(buf.getvalue(), subdir, f"{timestamp}_{safe_stem}.webp")
        return {"ruta": ruta, "nombre": Path(ruta).name, "mime_type": "image/webp"}
    except DecompressionBombError:
        raise HTTPException(status_code=400, detail="La imagen es demasiado grande para procesarla.")
    except HTTPException:
        raise
    except Exception:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".heic", ".heif"}:
            raise HTTPException(status_code=400, detail="Formato de imagen no soportado o archivo corrupto.")
        ruta = storage.save_bytes(contents, subdir, f"{timestamp}_{safe_stem}{suffix}")
        return {"ruta": ruta, "nombre": Path(ruta).name, "mime_type": file.content_type}


def get_fotos(db: Session, proyecto_id: int, etapa: Optional[str] = None, solo_pdf: bool = False):
    q = db.query(Foto).filter(Foto.proyecto_id == proyecto_id)
    if etapa:
        q = q.filter(Foto.etapa_codigo == etapa)
    if solo_pdf:
        q = q.filter(Foto.incluir_en_pdf.is_(True))
    return q.order_by(Foto.fecha.desc(), Foto.id.desc()).all()


def crear_foto(db: Session, proyecto_id: int, data: dict):
    """Crea el registro de una foto ya guardada en disco. `data` trae ruta/nombre/
    mime + metadatos (etapa, fecha, etc.)."""
    if not get_proyecto(db, proyecto_id):
        # No persistir huérfanas: borrar el archivo recién guardado.
        storage.delete(data.get("ruta"))
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    obj = Foto(
        proyecto_id=proyecto_id,
        etapa=data.get("etapa", "General"),
        etapa_codigo=data.get("etapa_codigo", "general"),
        subido_por=data.get("subido_por", ""),
        fecha=data["fecha"],
        emoji=data.get("emoji", "📷"),
        actividad_id=data.get("actividad_id"),
        ruta=data["ruta"],
        nombre_original=data.get("nombre_original", ""),
        mime_type=data.get("mime_type", "image/webp"),
        comentario_pdf=data.get("comentario_pdf", ""),
        incluir_en_pdf=False,
    )
    db.add(obj)
    _commit(db)
    db.refresh(obj)
    return obj


def update_foto(db: Session, fid: int, data: schemas.FotoUpdate):
    obj = db.query(Foto).filter(Foto.id == fid).first()
    if not obj:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    _commit(db)
    db.refresh(obj)
    return obj


def delete_foto(db: Session, fid: int) -> bool:
    obj = db.query(Foto).filter(Foto.id == fid).first()
    if not obj:
        return False
    storage.delete(obj.ruta)   # borra el archivo de disco (anti-traversal)
    db.delete(obj)
    _commit(db)
    return True


# ───────────────── REPORTES PDF (Cliente / Oficina) ─────────────────
def _enum_val(v) -> str:
    return v.value if hasattr(v, "value") else (str(v) if v is not None else "")


def _proyecto_dict(p) -> dict:
    return {
        "nombre": p.nombre, "cliente": p.cliente, "ubicacion": p.ubicacion,
        "region": p.region, "paneles": p.paneles or 0,
        "avance_real": p.avance_real or 0, "avance_planificado": p.avance_planificado or 0,
        "estado": _enum_val(p.estado),
        "fecha_inicio": str(p.fecha_inicio) if p.fecha_inicio else None,
        "fecha_fin": str(p.fecha_fin) if p.fecha_fin else None,
        "alcance": p.alcance or "",
    }


def _act_dict(a) -> dict:
    return {
        "id": a.id, "titulo": a.titulo, "nivel": a.nivel,
        "estado": _enum_val(a.estado), "prioridad": _enum_val(a.prioridad),
        "avance": a.avance or 0,
        "fecha_inicio_plan": str(a.fecha_inicio_plan) if a.fecha_inicio_plan else None,
        "fecha_fin_plan": str(a.fecha_fin_plan) if a.fecha_fin_plan else None,
        "duracion_dias": a.duracion_dias or 0,
        "subtareas": a.subtareas or [],   # columna JSON → ya es lista
    }


def _snap_dict(s) -> dict:
    return {
        "fecha": str(s.fecha),
        "avance_planificado": s.avance_planificado or 0,
        "avance_real": s.avance_real or 0,
        "actividades_total": s.actividades_total or 0,
        "actividades_hechas": s.actividades_hechas or 0,
    }


def _foto_dict(f) -> dict:
    # Resolver la ruta relativa a ABSOLUTA para que reportlab pueda leer la imagen.
    return {
        "id": f.id, "etapa": f.etapa, "emoji": f.emoji,
        "subido_por": f.subido_por, "fecha": str(f.fecha),
        "ruta": storage.resolve(f.ruta) or "",
        "nombre_original": f.nombre_original,
        "incluir_en_pdf": f.incluir_en_pdf,
        "comentario_pdf": f.comentario_pdf or "",
    }


def _asistencia_dict(a) -> dict:
    return {
        "nombre_persona": a.persona.nombre if a.persona else f"Persona #{a.persona_id}",
        "persona_id": a.persona_id,
        "fecha": str(a.fecha), "estado": _enum_val(a.estado),
        "hora": a.hora or "", "observacion": a.observacion or "",
    }


def _cuadrilla_dict(c) -> dict:
    miembros = [{
        "nombre_persona": m.persona.nombre if m.persona else "",
        "profesion": m.persona.profesion if m.persona else "",
        "rol_interno": _enum_val(m.rol_interno),
        "fecha_ingreso": str(m.fecha_ingreso) if m.fecha_ingreso else None,
        "activo": m.activo,
    } for m in (c.miembros or []) if m.activo]
    return {"nombre": c.nombre, "descripcion": c.descripcion or "", "miembros": miembros}


def pdf_cliente_bytes(db: Session, pid: int, tipo="semanal", semana_num=1,
                      fecha_desde=None, fecha_hasta=None, observaciones="") -> bytes:
    from io import BytesIO
    from app.modules.planner.pdf_cliente import generar_pdf_cliente

    p = get_proyecto(db, pid)
    if not p:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    buf = BytesIO()
    generar_pdf_cliente(
        proyecto=_proyecto_dict(p),
        actividades=[_act_dict(a) for a in get_actividades_proyecto(db, pid)],
        snapshots=[_snap_dict(s) for s in get_curva_s(db, pid)],
        fotos=[_foto_dict(f) for f in get_fotos(db, pid)],
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
        tipo=tipo, semana_num=semana_num, observaciones=observaciones,
        output_path=buf,   # buffer en memoria → sin archivo temporal
    )
    return buf.getvalue()


def pdf_oficina_bytes(db: Session, pid: int, tipo="semanal", semana_num=1,
                      fecha_desde=None, fecha_hasta=None, observaciones="") -> bytes:
    from io import BytesIO
    from app.modules.planner.pdf_oficina import generar_pdf_oficina

    p = get_proyecto(db, pid)
    if not p:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    buf = BytesIO()
    generar_pdf_oficina(
        proyecto=_proyecto_dict(p),
        actividades=[_act_dict(a) for a in get_actividades_proyecto(db, pid)],
        cuadrillas=[_cuadrilla_dict(c) for c in get_cuadrillas_proyecto(db, pid)],
        asistencia=[_asistencia_dict(a) for a in get_asistencia(
            db, pid, fecha=fecha_desde if tipo != "semanal" else None)],
        snapshots=[_snap_dict(s) for s in get_curva_s(db, pid)],
        fotos=[_foto_dict(f) for f in get_fotos(db, pid)],
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
        tipo=tipo, semana_num=semana_num, observaciones=observaciones,
        output_path=buf,
    )
    return buf.getvalue()
