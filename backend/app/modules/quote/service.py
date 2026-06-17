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
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.quote.models import (
    Cotizacion, CorrelativoContador, EmpresaConfig, ItemCotizacion,
    Producto, Usuario, PlantillasGlobales
)
from app.modules.quote.schemas import (
    CotizacionCreate, CotizacionUpdate,
    ItemCreate, ItemUpdate,
    ProductoCreate, ProductoUpdate,
    TotalesCotizacion, PlantillasGlobalesUpdate
)


# ─── ESTADOS Y REGLAS DE NEGOCIO ─────────────────────────────────────────────

class QuoteError(Exception):
    """Error de regla de negocio (estado/transición/bloqueo de edición).
    El router lo mapea a un HTTPException con el código indicado."""
    def __init__(self, message: str, code: int = 409):
        super().__init__(message)
        self.message = message
        self.code = code


ESTADOS_VALIDOS   = {"borrador", "enviada", "aprobada", "rechazada"}
ESTADOS_EDITABLES = {"borrador", "enviada"}
ESTADOS_CON_NUMERO = {"enviada", "aprobada"}   # al entrar aquí se asigna correlativo

# Transiciones permitidas: estado_actual -> {estados_destino}
TRANSICIONES = {
    "borrador":  {"enviada", "aprobada"},
    "enviada":   {"aprobada", "rechazada"},
    "aprobada":  {"rechazada"},
    "rechazada": set(),
}


def _require_editable(cot: Cotizacion) -> None:
    """Bloquea cualquier escritura sobre cotizaciones aprobadas/rechazadas."""
    if cot.estado not in ESTADOS_EDITABLES:
        raise QuoteError(
            f"La cotización está en estado '{cot.estado}' y es de solo lectura.",
            code=423,
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

def assign_correlativo(db: Session, cot: Cotizacion) -> None:
    """
    Asigna año + número secuencial a la cotización (si aún no tiene), tomando
    el contador anual con bloqueo de fila. El contador solo avanza, por eso
    eliminar borradores nunca reutiliza ni saltea números. El número reinicia
    cada año. La versión (sufijo del correlativo) se exige no vacía.
    """
    if cot.correlativo_num is not None:
        return  # ya tiene número asignado: no se reasigna

    if not (cot.version or "").strip():
        raise QuoteError("Debe indicar una versión (ej. A1) antes de enviar la cotización.")

    anio = datetime.now().year
    contador = (
        db.query(CorrelativoContador)
        .filter(CorrelativoContador.anio == anio)
        .with_for_update()
        .first()
    )
    if contador is None:
        db.add(CorrelativoContador(anio=anio, ultimo_numero=0))
        db.flush()
        contador = (
            db.query(CorrelativoContador)
            .filter(CorrelativoContador.anio == anio)
            .with_for_update()
            .first()
        )

    contador.ultimo_numero += 1
    cot.correlativo_anio = anio
    cot.correlativo_num = contador.ultimo_numero


def change_estado(db: Session, cotizacion_id: int, nuevo: str) -> Optional[Cotizacion]:
    """Cambia el estado validando la transición. Asigna correlativo al pasar a
    enviada/aprobada. Devuelve None si la cotización no existe."""
    cot = get_cotizacion(db, cotizacion_id)
    if not cot:
        return None

    nuevo = (nuevo or "").strip().lower()
    if nuevo not in ESTADOS_VALIDOS:
        raise QuoteError(f"Estado inválido: '{nuevo}'.")

    actual = cot.estado
    if nuevo == actual:
        return cot
    if nuevo not in TRANSICIONES.get(actual, set()):
        raise QuoteError(f"Transición no permitida: '{actual}' → '{nuevo}'.")

    if nuevo in ESTADOS_CON_NUMERO:
        assign_correlativo(db, cot)

    cot.estado = nuevo
    db.commit()
    db.refresh(cot)
    return cot


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
    # Nace como borrador SIN correlativo (se asigna al enviar/aprobar).
    cot = Cotizacion(**data.model_dump())
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
    _require_editable(cot)
    payload = data.model_dump(exclude_unset=True)
    payload.pop("estado", None)   # el estado solo cambia vía change_estado()
    for field, value in payload.items():
        setattr(cot, field, value)
    db.commit()
    db.refresh(cot)
    return cot


def delete_cotizacion(db: Session, cotizacion_id: int) -> bool:
    """Borrado FÍSICO, permitido solo para borradores. Las cotizaciones con
    número asignado (enviada/aprobada/rechazada) se conservan como historial."""
    cot = get_cotizacion(db, cotizacion_id)
    if not cot:
        return False
    if cot.estado != "borrador":
        raise QuoteError(
            "Solo se pueden eliminar cotizaciones en borrador. Las enviadas, "
            "aprobadas o rechazadas se conservan como historial.",
            code=409,
        )
    db.delete(cot)   # los ítems caen por el cascade
    db.commit()
    return True


def duplicar_cotizacion(db: Session, cotizacion_id: int) -> Optional[Cotizacion]:
    """Clona una cotización como nuevo borrador (sin correlativo, fecha de hoy),
    copiando cabecera e ítems. No toca el original — funciona como plantilla."""
    orig = get_cotizacion(db, cotizacion_id)
    if not orig:
        return None

    skip = {"id", "correlativo_anio", "correlativo_num", "estado",
            "created_at", "updated_at"}
    cabecera = {
        c.name: getattr(orig, c.name)
        for c in Cotizacion.__table__.columns
        if c.name not in skip
    }
    nueva = Cotizacion(**cabecera, estado="borrador")
    db.add(nueva)
    db.flush()   # obtener nueva.id

    for it in orig.items:
        db.add(ItemCotizacion(
            cotizacion_id=nueva.id,
            producto_id=it.producto_id,
            nombre=it.nombre,
            descripcion=it.descripcion,
            marca=it.marca,
            unidad=it.unidad,
            cantidad=it.cantidad,
            precio_unit=it.precio_unit,
            moneda=it.moneda,
            particion=it.particion,
            subparticion=it.subparticion,
            orden=it.orden,
        ))

    db.commit()
    db.refresh(nueva)
    return nueva


# ─── ÍTEMS ───────────────────────────────────────────────────────────────────

def add_item(db: Session, cotizacion_id: int, data: ItemCreate) -> Optional[ItemCotizacion]:
    cot = get_cotizacion(db, cotizacion_id)
    if not cot:
        return None
    _require_editable(cot)
    item = ItemCotizacion(cotizacion_id=cotizacion_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(
    db: Session, cotizacion_id: int, item_id: int, data: ItemUpdate
) -> Optional[ItemCotizacion]:
    cot = get_cotizacion(db, cotizacion_id)
    if not cot:
        return None
    _require_editable(cot)
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
    cot = get_cotizacion(db, cotizacion_id)
    if not cot:
        return False
    _require_editable(cot)
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
    cot = get_cotizacion(db, cotizacion_id)
    if not cot:
        return
    _require_editable(cot)
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

def _match_cliente(db: Session, nombre: str, documento: Optional[str]) -> Optional[DatosCliente]:
    """Identifica un cliente por RUC/DNI (identificador fuerte) y, si no, por nombre.
    Permite corregir el nombre (lo ancla el RUC) o corregir el RUC (lo ancla el nombre)
    sin duplicar el registro."""
    if documento:
        c = db.query(DatosCliente).filter(DatosCliente.documento == documento).first()
        if c:
            return c
    if nombre:
        return db.query(DatosCliente).filter(DatosCliente.nombre == nombre).first()
    return None


def upsert_cliente(
    db: Session, *, nombre: str, documento: Optional[str] = None,
    direccion: Optional[str] = None, atencion: Optional[str] = None,
    referencia: Optional[str] = None, correo: Optional[str] = None,
    telefono: Optional[str] = None,
) -> Optional[DatosCliente]:
    """Crea o actualiza un cliente emparejando por RUC/DNI o nombre. Devuelve None
    si no hay ni nombre ni documento. Puede lanzar IntegrityError (lo maneja el caller)."""
    nombre = (nombre or "").strip()
    documento = (documento or "").strip() or None   # vacío -> NULL
    if not nombre and not documento:
        return None

    campos = dict(nombre=nombre, documento=documento, direccion=direccion,
                  atencion=atencion, referencia=referencia, correo=correo, telefono=telefono)
    cliente = _match_cliente(db, nombre, documento)
    if cliente:
        for field, value in campos.items():
            setattr(cliente, field, value)
    else:
        cliente = DatosCliente(**campos)
        db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def create_cliente(db: Session, data: DatosClienteCreate) -> DatosCliente:
    """Upsert de cliente desde la API. Mapea choques de unicidad a un error claro."""
    try:
        cliente = upsert_cliente(
            db, nombre=data.nombre, documento=data.documento, direccion=data.direccion,
            atencion=data.atencion, referencia=data.referencia, correo=data.correo,
            telefono=data.telefono,
        )
    except IntegrityError:
        db.rollback()
        raise QuoteError("Ya existe otro cliente con ese nombre o RUC/DNI.", code=409)
    if cliente is None:
        raise QuoteError("Debe indicar al menos el nombre o el RUC/DNI del cliente.", code=400)
    return cliente


def upsert_cliente_from_cotizacion(db: Session, cot: Cotizacion) -> None:
    """Guarda/actualiza el cliente al generar el PDF (cliente nuevo -> se crea;
    existente -> se actualiza). Best-effort: nunca interrumpe la generación del PDF."""
    try:
        upsert_cliente(
            db, nombre=cot.cliente_nombre, documento=cot.cliente_doc,
            direccion=cot.cliente_dir, atencion=cot.cliente_atencion,
            referencia=cot.cliente_referencia, correo=cot.cliente_correo,
            telefono=cot.cliente_tel,
        )
    except Exception:
        db.rollback()

# ─── PLANTILLAS GLOBALES ─────────────────────────────────────────────────────

def get_plantillas_globales(db: Session) -> PlantillasGlobales:
    """Obtiene la única fila de plantillas globales; si no existe la crea vacía.
    Los bancos arrancan SIN cards ni logos por defecto: el usuario los agrega y
    edita (nombre, logo y campos) desde la sección de Cuentas Bancarias."""
    plantillas = db.query(PlantillasGlobales).first()

    if not plantillas:
        plantillas = PlantillasGlobales(
            id=1,
            cond_tecnicas=[""],
            cond_comerciales=["", "", "", "", "", ""],
            cond_otras=[],
            cond_garantia=[],
            cond_garantia_servicio="",
            cuentas_bancarias=[],
        )
        db.add(plantillas)
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

