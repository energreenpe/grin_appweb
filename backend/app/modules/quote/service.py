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

from app import storage
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


# ─── LIMPIEZA DE LOGOS POR CONTEO DE REFERENCIAS ─────────────────────────────
# Los logos de banco son "snapshot": una imagen puede estar referenciada por la
# plantilla global Y/O por varias cotizaciones. Por eso una imagen solo se borra
# del disco cuando YA NO la referencia nadie (así no se rompe "Cargar Plantilla").

def gather_referenced_logos(db: Session) -> set[str]:
    """Todas las rutas de logo referenciadas hoy en la BD: empresa + plantilla
    global + todas las cotizaciones."""
    refs: set[str] = set()

    empresa = db.query(EmpresaConfig).first()
    if empresa and empresa.logo_path:
        refs.add(empresa.logo_path)

    def add_banks(cuentas):
        for b in (cuentas or []):
            if b.get("logo"):
                refs.add(b["logo"])

    plantilla = db.query(PlantillasGlobales).first()
    if plantilla:
        add_banks(plantilla.cuentas_bancarias)
    for cot in db.query(Cotizacion).all():
        add_banks(cot.cuentas_bancarias)

    return refs


def _bank_logos(cuentas) -> set[str]:
    """Logos presentes en una lista de cuentas bancarias."""
    return {b.get("logo") for b in (cuentas or []) if b.get("logo")}


def _delete_unreferenced_logos(db: Session, candidates: set[str]) -> None:
    """Borra del disco los logos candidatos que ya no referencia NADIE.
    Best-effort: nunca interrumpe el flujo principal."""
    if not candidates:
        return
    try:
        referenced = gather_referenced_logos(db)
        for logo in candidates:
            if logo and logo not in referenced and str(logo).startswith("uploads/"):
                storage.delete(logo)
    except Exception:
        pass


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


def _find_producto_duplicado(db: Session, nombre: str, marca: str) -> Optional[Producto]:
    """Busca un producto existente con el mismo nombre+marca (sin distinguir
    mayúsculas ni espacios), usado por la importación masiva para no duplicar
    productos que ya están en el catálogo."""
    return (
        db.query(Producto)
        .filter(func.lower(Producto.nombre) == nombre.strip().lower())
        .filter(func.lower(func.coalesce(Producto.marca, "")) == (marca or "").strip().lower())
        .first()
    )


def bulk_import_productos(db: Session, productos: list[ProductoCreate]) -> dict:
    """Inserta en bloque los productos que no dupliquen uno ya existente (mismo
    nombre+marca), en una única transacción. También deduplica entre sí las filas
    del propio archivo (si el Excel trae el mismo producto dos veces)."""
    creados: list[Producto] = []
    omitidos: list[dict] = []
    vistos: set[tuple[str, str]] = set()

    for data in productos:
        clave = (data.nombre.strip().lower(), (data.marca or "").strip().lower())
        if clave in vistos or _find_producto_duplicado(db, data.nombre, data.marca):
            omitidos.append({"nombre": data.nombre, "marca": data.marca})
            continue
        vistos.add(clave)
        prod = Producto(**data.model_dump())
        db.add(prod)
        creados.append(prod)

    db.commit()
    for p in creados:
        db.refresh(p)
    return {"creados": creados, "omitidos": omitidos}


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

    # Si cambian las cuentas bancarias, recordar los logos previos para limpiar
    # luego los que queden huérfanos (banco eliminado, Cargar Plantilla, reemplazo).
    old_bank_logos = _bank_logos(cot.cuentas_bancarias) if "cuentas_bancarias" in payload else None

    for field, value in payload.items():
        setattr(cot, field, value)
    db.commit()
    db.refresh(cot)

    if old_bank_logos is not None:
        removed = old_bank_logos - _bank_logos(cot.cuentas_bancarias)
        _delete_unreferenced_logos(db, removed)

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
    bank_logos = _bank_logos(cot.cuentas_bancarias)
    db.delete(cot)   # los ítems caen por el cascade
    db.commit()
    _delete_unreferenced_logos(db, bank_logos)   # limpiar logos que queden huérfanos
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
# La lógica de clientes (búsqueda + upsert con deduplicación por RUC/DNI o nombre)
# vive en el módulo shared. Se re-exporta aquí para que el resto de quote la siga
# usando igual (p. ej. upsert_cliente_from_cotizacion y el router).
from app.modules.shared.service import (  # noqa: F401
    get_clientes, upsert_cliente, create_cliente,
)


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
    payload = data.model_dump(exclude_unset=True)
    old_bank_logos = _bank_logos(plantillas.cuentas_bancarias) if "cuentas_bancarias" in payload else None

    for field, value in payload.items():
        setattr(plantillas, field, value)
    db.commit()
    db.refresh(plantillas)

    if old_bank_logos is not None:
        removed = old_bank_logos - _bank_logos(plantillas.cuentas_bancarias)
        _delete_unreferenced_logos(db, removed)

    return plantillas

