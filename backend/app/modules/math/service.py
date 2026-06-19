"""
Capa de servicio del módulo MATH.

Entregable #2: lectura de catálogos (regiones, equipos técnicos, electrodomésticos,
ingenieros). El CRUD de Calculo y la orquestación de los motores se agregan después.

Las búsquedas/creación de clientes se delegan a app.modules.shared.service
(get_clientes / create_cliente); MATH no importa de quote ni inspector.
"""
from typing import Optional
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from app.modules.math import engine_aislado
from app.modules.math.models import Calculo, EquipoTecnico, Region, ElectrodomesticoCatalogo
from app.modules.math.schemas import AisladoCalcularRequest, CalculoCreate, CalculoUpdate
from app.modules.shared.models import Usuario


def list_regiones(db: Session):
    return db.query(Region).order_by(Region.nombre).all()


def list_equipos(db: Session, tipo: Optional[str] = None, solo_activos: bool = True):
    q = db.query(EquipoTecnico)
    if tipo:
        q = q.filter(EquipoTecnico.tipo == tipo)
    if solo_activos:
        q = q.filter(EquipoTecnico.activo.is_(True))
    return q.order_by(EquipoTecnico.tipo, EquipoTecnico.descripcion).all()


def list_electrodomesticos(db: Session):
    return db.query(ElectrodomesticoCatalogo).order_by(ElectrodomesticoCatalogo.nombre).all()


def list_ingenieros(db: Session):
    return (
        db.query(Usuario)
        .filter(Usuario.rol == "ingeniero", Usuario.activo.is_(True))
        .order_by(Usuario.nombre)
        .all()
    )


# ── Soporte del motor Aislado ─────────────────────────────────────────────────
def get_equipo(db: Session, equipo_id: int, tipo: str) -> Optional[EquipoTecnico]:
    return (
        db.query(EquipoTecnico)
        .filter(EquipoTecnico.id == equipo_id, EquipoTecnico.tipo == tipo)
        .first()
    )


def resolve_hsp(db: Session, region_nombre: str, tipo_hsp: str) -> Optional[float]:
    """HSP de la región según el tipo elegido (minimo/promedio/mayor)."""
    region = (
        db.query(Region)
        .filter(Region.nombre.ilike(region_nombre.strip()))
        .first()
    )
    if not region:
        return None
    valor = {
        "minimo": region.hsp_minimo,
        "promedio": region.hsp_promedio,
        "mayor": region.hsp_mayor,
    }.get(tipo_hsp)
    return float(valor) if valor is not None else None


def calcular_aislado(db: Session, req: AisladoCalcularRequest) -> dict:
    """Resuelve catálogos y HSP desde la BD y ejecuta el motor (puro).
    Mapea entradas inválidas a HTTP 4xx; el motor permanece sin estado."""
    panel = get_equipo(db, req.panel_id, "panel")
    if not panel:
        raise HTTPException(status_code=404, detail="Panel no encontrado en el catálogo.")
    bateria = get_equipo(db, req.bateria_id, "bateria")
    if not bateria:
        raise HTTPException(status_code=404, detail="Batería no encontrada en el catálogo.")

    # HSP: valor directo o resuelto por región.
    if req.hsp is not None:
        hsp = req.hsp
    elif req.region:
        hsp = resolve_hsp(db, req.region, req.tipo_hsp)
        if hsp is None:
            raise HTTPException(
                status_code=422,
                detail=f"No se encontró HSP para la región '{req.region}'.",
            )
    else:
        raise HTTPException(status_code=422, detail="Debe indicar 'region' o un valor de 'hsp'.")

    inversores = [e.specs for e in list_equipos(db, tipo="inversor_aislado")]
    cargas = [c.model_dump() for c in req.cargas]

    try:
        return engine_aislado.calcular_aislado(
            cargas=cargas,
            hsp=hsp,
            dias_autonomia=req.dias_autonomia,
            tipo_bateria=req.tipo_bateria,
            panel=panel.specs,
            bateria=bateria.specs,
            inversores=inversores,
            voltaje_sistema=req.voltaje_sistema,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ── CRUD de Calculo ───────────────────────────────────────────────────────────
_FK_ERROR = "Cliente o ingeniero inválido: el registro referenciado no existe."


def listar_calculos(
    db: Session,
    tipo_sistema: Optional[str] = None,
    estado: Optional[str] = None,
    cliente_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
):
    # joinedload evita el N+1: CalculoListItem serializa `cliente` por fila.
    q = db.query(Calculo).options(joinedload(Calculo.cliente))
    if tipo_sistema:
        q = q.filter(Calculo.tipo_sistema == tipo_sistema)
    if estado:
        q = q.filter(Calculo.estado == estado)
    if cliente_id:
        q = q.filter(Calculo.cliente_id == cliente_id)
    return q.order_by(desc(Calculo.fecha)).offset(skip).limit(limit).all()


def obtener_calculo(db: Session, calculo_id: int) -> Calculo:
    calculo = db.query(Calculo).filter(Calculo.id == calculo_id).first()
    if not calculo:
        raise HTTPException(status_code=404, detail="Cálculo no encontrado.")
    return calculo


def crear_calculo(db: Session, data: CalculoCreate) -> Calculo:
    calculo = Calculo(**data.model_dump())
    db.add(calculo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=_FK_ERROR)
    db.refresh(calculo)
    return calculo


def actualizar_calculo(db: Session, calculo_id: int, data: CalculoUpdate) -> Calculo:
    calculo = obtener_calculo(db, calculo_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(calculo, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=_FK_ERROR)
    db.refresh(calculo)
    return calculo


def eliminar_calculo(db: Session, calculo_id: int) -> dict:
    calculo = obtener_calculo(db, calculo_id)
    db.delete(calculo)
    db.commit()
    return {"message": "Cálculo eliminado."}


def calcular_y_guardar(db: Session, calculo_id: int) -> Calculo:
    """Ejecuta el motor correspondiente al tipo de sistema del cálculo y persiste
    el resultado en Calculo.resultado. La entrada (JSON) se valida al vuelo."""
    calculo = obtener_calculo(db, calculo_id)

    if calculo.tipo_sistema == "SFV Aislado":
        data = dict(calculo.entrada or {})
        data.setdefault("region", calculo.region)
        try:
            req = AisladoCalcularRequest(**data)
        except ValidationError:
            raise HTTPException(
                status_code=422,
                detail="La entrada del cálculo aislado está incompleta o es inválida "
                       "(revise cargas, días de autonomía, panel y batería).",
            )
        calculo.resultado = calcular_aislado(db, req)
        calculo.paso_actual = "resultado"
        db.commit()
        db.refresh(calculo)
        return calculo

    raise HTTPException(
        status_code=422,
        detail=f"El tipo de sistema '{calculo.tipo_sistema}' aún no está disponible para cálculo.",
    )


def completar_calculo(db: Session, calculo_id: int) -> Calculo:
    calculo = obtener_calculo(db, calculo_id)
    if not calculo.resultado:
        raise HTTPException(
            status_code=400,
            detail="No se puede completar un cálculo sin resultado. Ejecute el cálculo primero.",
        )
    calculo.estado = "completado"
    db.commit()
    db.refresh(calculo)
    return calculo
