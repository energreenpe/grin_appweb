"""
service.py — Lógica de negocio del módulo QUOTE.
Portada y adaptada desde QUOTE/interfaz.py y QUOTE/cotizaciones.py.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.quote.models import (
    Cotizacion, EmpresaConfig, ItemCotizacion, Producto, Usuario, PlantillasGlobales
)
from app.modules.quote.schemas import (
    CotizacionCreate, CotizacionUpdate,
    ItemCreate, ItemUpdate,
    ProductoCreate, ProductoUpdate,
    TotalesCotizacion, PlantillasGlobalesUpdate
)


# ─── UTILIDADES FINANCIERAS ──────────────────────────────────────────────────
# Réplica exacta de la función en QUOTE/interfaz.py (líneas 40-64)

def convertir_precio(
    precio: float,
    moneda_origen: str,
    moneda_destino: str,
    tipo_cambio: float,
    utilidad: float = 1.30,
) -> float:
    """
    Aplica margen de utilidad y convierte entre PEN/USD.
    Réplica fiel de la función original en interfaz.py.
    """
    try:
        precio_f = float(precio)
    except (ValueError, TypeError):
        precio_f = 0.0
    try:
        utilidad_f = float(utilidad)
    except (ValueError, TypeError):
        utilidad_f = 1.30
    try:
        tipo_cambio_f = float(tipo_cambio)
    except (ValueError, TypeError):
        tipo_cambio_f = 1.0

    precio_con_utilidad = precio_f * utilidad_f

    if moneda_origen == moneda_destino:
        return precio_con_utilidad
    if moneda_origen == "USD" and moneda_destino == "PEN":
        return precio_con_utilidad * tipo_cambio_f
    if moneda_origen == "PEN" and moneda_destino == "USD":
        return precio_con_utilidad / tipo_cambio_f
    return precio_con_utilidad


def _moneda_simbolo(moneda_str: str) -> str:
    """Devuelve el símbolo según la moneda — réplica de cotizaciones.py."""
    if "Soles" in moneda_str or "PEN" in moneda_str:
        return "S/"
    if "Dólar" in moneda_str or "USD" in moneda_str:
        return "$"
    return ""


def _moneda_codigo(moneda_str: str) -> str:
    """Extrae código ISO de la moneda display."""
    if "USD" in moneda_str or "Dólar" in moneda_str:
        return "USD"
    return "PEN"


def calcular_totales(
    items: list[ItemCotizacion],
    cotizacion: Cotizacion,
) -> TotalesCotizacion:
    """
    Agrupa por partición, calcula subtotales, IGV y total.
    Réplica de la lógica en cotizaciones.py líneas 410-415.
    """
    moneda_display = _moneda_codigo(cotizacion.moneda)
    tipo_cambio    = float(cotizacion.tipo_cambio)
    utilidad       = float(cotizacion.utilidad)

    por_particion: dict[str, Decimal] = defaultdict(Decimal)

    for item in items:
        subtotal = convertir_precio(
            precio=float(item.precio_unit) * float(item.cantidad),
            moneda_origen=item.moneda,
            moneda_destino=moneda_display,
            tipo_cambio=tipo_cambio,
            utilidad=utilidad,
        )
        por_particion[item.particion] += Decimal(str(subtotal)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    subtotal_general = sum(por_particion.values(), Decimal("0"))
    igv              = (subtotal_general * Decimal("0.18")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    total = subtotal_general + igv

    return TotalesCotizacion(
        por_particion=dict(por_particion),
        subtotal=subtotal_general,
        igv=igv,
        total=total,
    )


# ─── CORRELATIVO ─────────────────────────────────────────────────────────────

def generar_correlativo(db: Session) -> str:
    """
    Genera correlativo COT-YYYY-NNNN.
    Reemplaza el counter.txt del sistema legacy.
    """
    year   = datetime.now().year
    ultimo = db.query(func.max(Cotizacion.id)).scalar() or 0
    return f"COT-{year}-{str(ultimo + 1).zfill(4)}"


# ─── PRODUCTOS ───────────────────────────────────────────────────────────────

def get_productos(
    db: Session,
    search: Optional[str] = None,
    categoria: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Producto]:
    q = db.query(Producto).filter(Producto.activo == True)
    if search:
        s = f"%{search.lower()}%"
        q = q.filter(
            Producto.nombre.ilike(s)
            | Producto.descripcion.ilike(s)
            | Producto.categoria.ilike(s)
            | Producto.marca.ilike(s)
        )
    if categoria:
        q = q.filter(Producto.categoria.ilike(f"%{categoria}%"))
    return q.offset(skip).limit(limit).all()


def get_producto(db: Session, producto_id: int) -> Optional[Producto]:
    return db.query(Producto).filter(Producto.id == producto_id).first()




def create_producto(db: Session, data: ProductoCreate) -> Producto:
    prod = Producto(**data.model_dump())
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


def update_producto(db: Session, producto_id: int, data: ProductoUpdate) -> Optional[Producto]:
    prod = get_producto(db, producto_id)
    if not prod:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(prod, field, value)
    db.commit()
    db.refresh(prod)
    return prod


def delete_producto(db: Session, producto_id: int) -> bool:
    prod = get_producto(db, producto_id)
    if not prod:
        return False
    prod.activo = False  # soft delete
    db.commit()
    return True


# ─── COTIZACIONES ────────────────────────────────────────────────────────────

def get_cotizaciones(db: Session, skip: int = 0, limit: int = 50) -> list[Cotizacion]:
    return (
        db.query(Cotizacion)
        .order_by(Cotizacion.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_cotizacion(db: Session, cotizacion_id: int) -> Optional[Cotizacion]:
    return db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()


def create_cotizacion(db: Session, data: CotizacionCreate) -> Cotizacion:
    correlativo = generar_correlativo(db)
    cot = Cotizacion(correlativo=correlativo, **data.model_dump())
    db.add(cot)
    db.commit()
    db.refresh(cot)
    return cot


def update_cotizacion(
    db: Session, cotizacion_id: int, data: CotizacionUpdate
) -> Optional[Cotizacion]:
    cot = get_cotizacion(db, cotizacion_id)
    if not cot:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cot, field, value)
    db.commit()
    db.refresh(cot)
    return cot


def delete_cotizacion(db: Session, cotizacion_id: int) -> bool:
    cot = get_cotizacion(db, cotizacion_id)
    if not cot:
        return False
    cot.estado = "cancelada"
    db.commit()
    return True


# ─── ÍTEMS ───────────────────────────────────────────────────────────────────

def add_item(db: Session, cotizacion_id: int, data: ItemCreate) -> Optional[ItemCotizacion]:
    cot = get_cotizacion(db, cotizacion_id)
    if not cot:
        return None
    item = ItemCotizacion(cotizacion_id=cotizacion_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(
    db: Session, cotizacion_id: int, item_id: int, data: ItemUpdate
) -> Optional[ItemCotizacion]:
    item = (
        db.query(ItemCotizacion)
        .filter(ItemCotizacion.id == item_id, ItemCotizacion.cotizacion_id == cotizacion_id)
        .first()
    )
    if not item:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, cotizacion_id: int, item_id: int) -> bool:
    item = (
        db.query(ItemCotizacion)
        .filter(ItemCotizacion.id == item_id, ItemCotizacion.cotizacion_id == cotizacion_id)
        .first()
    )
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True

def reorder_items(db: Session, cotizacion_id: int, item_ids: list[int]):
    for index, item_id in enumerate(item_ids):
        item = db.query(ItemCotizacion).filter(
            ItemCotizacion.id == item_id,
            ItemCotizacion.cotizacion_id == cotizacion_id
        ).first()
        if item:
            item.orden = index
    db.commit()


# ─── EMPRESA ─────────────────────────────────────────────────────────────────

def get_empresa(db: Session) -> EmpresaConfig:
    empresa = db.query(EmpresaConfig).first()
    if not empresa:
        # Crear fila única con defaults si no existe
        empresa = EmpresaConfig(id=1)
        db.add(empresa)
        db.commit()
        db.refresh(empresa)
    return empresa


def update_empresa(db: Session, data: dict) -> EmpresaConfig:
    empresa = get_empresa(db)
    for field, value in data.items():
        if hasattr(empresa, field):
            setattr(empresa, field, value)
    db.commit()
    db.refresh(empresa)
    return empresa


# ─── USUARIOS ────────────────────────────────────────────────────────────────

def get_vendedores(db: Session) -> list[Usuario]:
    return db.query(Usuario).filter(Usuario.activo == True, Usuario.rol == "vendedor").all()


# ─── CLIENTES ────────────────────────────────────────────────────────────────

from app.modules.quote.models import DatosCliente
from app.modules.quote.schemas import DatosClienteCreate

def get_clientes(db: Session, search: Optional[str] = None) -> list[DatosCliente]:
    q = db.query(DatosCliente)
    if search:
        s = f"%{search.lower()}%"
        q = q.filter(DatosCliente.nombre.ilike(s) | DatosCliente.documento.ilike(s))
    return q.limit(50).all()

def create_cliente(db: Session, data: DatosClienteCreate) -> DatosCliente:
    # Si existe, lo actualiza, si no, lo crea (upsert basado en el nombre)
    cliente = db.query(DatosCliente).filter(DatosCliente.nombre == data.nombre).first()
    if cliente:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(cliente, field, value)
    else:
        cliente = DatosCliente(**data.model_dump())
        db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

# ─── PLANTILLAS GLOBALES ─────────────────────────────────────────────────────

# Estructura fija de los 5 bancos (sin números — el usuario los completa)
_ESTRUCTURA_BANCOS = [
    {"banco": "Interbank",         "logo": "Interbank.png", "tipo": "full",          "datos": {"Soles": "", "CCI Soles": "", "Dólares": "", "CCI Dólares": ""}},
    {"banco": "Banco de la Nación","logo": "bn.png",        "tipo": "detracciones",  "datos": {"Detracciones": ""}},
    {"banco": "BCP",               "logo": "bcp.png",       "tipo": "full",          "datos": {"Soles": "", "CCI Soles": "", "Dólares": "", "CCI Dólares": ""}},
    {"banco": "BBVA",              "logo": "bbva.png",       "tipo": "full",          "datos": {"Soles": "", "CCI Soles": "", "Dólares": "", "CCI Dólares": ""}},
    {"banco": "Scotiabank",        "logo": "sb.png",         "tipo": "full",          "datos": {"Soles": "", "CCI Soles": "", "Dólares": "", "CCI Dólares": ""}},
]


def get_plantillas_globales(db: Session) -> PlantillasGlobales:
    """Obtiene la única fila de plantillas globales. Si no existe la crea vacía.
    Si ya existe pero cuentas_bancarias está vacío, inicializa la estructura de bancos."""
    plantillas = db.query(PlantillasGlobales).first()
    needs_save = False

    if not plantillas:
        # Primera vez en un sistema recién instalado
        plantillas = PlantillasGlobales(
            id=1,
            cond_tecnicas=[""],
            cond_comerciales=["", "", "", "", "", ""],
            cond_otras=[],
            cond_garantia=[],
            cond_garantia_servicio="",
            cuentas_bancarias=_ESTRUCTURA_BANCOS,
        )
        db.add(plantillas)
        needs_save = True
    elif not plantillas.cuentas_bancarias:
        # El registro existe pero aún no tiene bancos (instalación previa)
        plantillas.cuentas_bancarias = _ESTRUCTURA_BANCOS
        needs_save = True

    if needs_save:
        db.commit()
        db.refresh(plantillas)

    return plantillas


def update_plantillas_globales(db: Session, data: PlantillasGlobalesUpdate) -> PlantillasGlobales:
    plantillas = get_plantillas_globales(db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(plantillas, field, value)
    db.commit()
    db.refresh(plantillas)
    return plantillas

