"""
Router del módulo MATH — prefijo /api/math (montado en app/main.py).

Entregable #2: endpoints de catálogos (solo lectura) + soporte de clientes
(reutilizando app.modules.shared, sin tocar quote ni inspector). El CRUD de
cálculos y los motores se agregan en los siguientes entregables.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.modules.math import schemas, service
from app.modules.shared.schemas import DatosClienteOut, DatosClienteCreate, UsuarioOut
from app.modules.shared.service import get_clientes, create_cliente

router = APIRouter()


@router.get("/ping")
def ping():
    """Verifica que el módulo MATH esté correctamente cableado."""
    return {"module": "math", "status": "ok"}


# ── Catálogos (solo lectura) ──────────────────────────────────────────────────
@router.get("/regiones", response_model=List[schemas.RegionOut])
def listar_regiones(db: Session = Depends(get_db)):
    """Regiones del Perú con sus Horas Sol Pico (HSP)."""
    return service.list_regiones(db)


@router.get("/equipos", response_model=List[schemas.EquipoTecnicoOut])
def listar_equipos(tipo: Optional[schemas.TipoEquipo] = None, db: Session = Depends(get_db)):
    """Catálogo técnico. Filtra por `tipo` (panel | bateria | inversor_aislado |
    inversor_autoconsumo); sin `tipo` devuelve todos los equipos activos."""
    return service.list_equipos(db, tipo=tipo)


@router.get("/electrodomesticos", response_model=List[schemas.ElectrodomesticoOut])
def listar_electrodomesticos(db: Session = Depends(get_db)):
    """Catálogo de potencias de electrodomésticos (insumo del motor Aislado)."""
    return service.list_electrodomesticos(db)


@router.get("/ingenieros", response_model=List[UsuarioOut])
def listar_ingenieros(db: Session = Depends(get_db)):
    """Usuarios con rol='ingeniero' activos (responsables del cálculo)."""
    return service.list_ingenieros(db)


# ── Motor de cálculo: Aislado (stateless) ─────────────────────────────────────
@router.post("/aislado/calcular", response_model=schemas.AisladoResultado)
def calcular_aislado(req: schemas.AisladoCalcularRequest, db: Session = Depends(get_db)):
    """Dimensiona un sistema aislado a partir de las cargas, la región/HSP, el panel
    y la batería elegidos. No persiste (la persistencia entra con el CRUD de cálculos)."""
    return service.calcular_aislado(db, req)


# ── Motor de cálculo: Autoconsumo (stateless) ─────────────────────────────────
@router.post("/autoconsumo/calcular", response_model=schemas.AutoconsumoResultado)
def calcular_autoconsumo(req: schemas.AutoconsumoCalcularRequest, db: Session = Depends(get_db)):
    """Dado un panel y un inversor de autoconsumo, devuelve las 3 configuraciones
    (mínima/óptima/máxima) por ratio DC/AC. No persiste."""
    return service.calcular_autoconsumo(db, req)


# ── CRUD de Cálculos ──────────────────────────────────────────────────────────
@router.get("/calculos", response_model=List[schemas.CalculoListItem])
def listar_calculos(
    tipo_sistema: Optional[schemas.TipoSistema] = None,
    estado: Optional[schemas.EstadoCalculo] = None,
    cliente_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return service.listar_calculos(
        db, tipo_sistema=tipo_sistema, estado=estado, cliente_id=cliente_id, skip=skip, limit=limit
    )


@router.post("/calculos", response_model=schemas.CalculoOut)
def crear_calculo(data: schemas.CalculoCreate, db: Session = Depends(get_db)):
    return service.crear_calculo(db, data)


@router.get("/calculos/{calculo_id}", response_model=schemas.CalculoOut)
def obtener_calculo(calculo_id: int, db: Session = Depends(get_db)):
    return service.obtener_calculo(db, calculo_id)


@router.put("/calculos/{calculo_id}", response_model=schemas.CalculoOut)
def actualizar_calculo(calculo_id: int, data: schemas.CalculoUpdate, db: Session = Depends(get_db)):
    return service.actualizar_calculo(db, calculo_id, data)


@router.delete("/calculos/{calculo_id}")
def eliminar_calculo(calculo_id: int, db: Session = Depends(get_db)):
    return service.eliminar_calculo(db, calculo_id)


@router.post("/calculos/{calculo_id}/calcular", response_model=schemas.CalculoOut)
def calcular_calculo(calculo_id: int, db: Session = Depends(get_db)):
    """Ejecuta el motor del tipo de sistema del cálculo y persiste el resultado."""
    return service.calcular_y_guardar(db, calculo_id)


@router.post("/calculos/{calculo_id}/completar", response_model=schemas.CalculoOut)
def completar_calculo(calculo_id: int, db: Session = Depends(get_db)):
    return service.completar_calculo(db, calculo_id)


# ── Soporte de clientes (delegado a shared) ───────────────────────────────────
@router.get("/clientes/search", response_model=List[DatosClienteOut])
def buscar_clientes(q: str, db: Session = Depends(get_db)):
    return get_clientes(db, search=q)


@router.post("/clientes", response_model=DatosClienteOut)
def crear_cliente(cliente: DatosClienteCreate, db: Session = Depends(get_db)):
    return create_cliente(db, cliente)
