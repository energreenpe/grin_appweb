from __future__ import annotations
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

# Schemas de entidades transversales: definidos en shared, re-exportados aquí por
# compatibilidad con el código de quote que los referencia como schemas.<X>.
from app.modules.shared.schemas import (  # noqa: F401
    UsuarioBase, UsuarioCreate, UsuarioOut,
    DatosClienteBase, DatosClienteCreate, DatosClienteOut,
    EmpresaBase, EmpresaUpdate, EmpresaOut,
)


# ─── PRODUCTO ─────────────────────────────────────────────────────────────────

class ProductoBase(BaseModel):
    categoria:   str
    nombre:      str
    descripcion: Optional[str] = None
    marca:       Optional[str] = None
    unidad:      str = "und"
    precio:      Decimal
    moneda:      str = "PEN"


class ProductoCreate(ProductoBase):
    descripcion: str
    marca:       str

    @field_validator("nombre", "descripcion", "marca", "categoria")
    @classmethod
    def check_non_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"El campo {info.field_name} no puede estar vacío")
        return v.strip()

    @field_validator("precio")
    @classmethod
    def check_positive_price(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("El precio de venta debe ser mayor a 0")
        return v


class ProductoUpdate(BaseModel):
    categoria:   Optional[str] = None
    nombre:      Optional[str] = None
    descripcion: Optional[str] = None
    marca:       Optional[str] = None
    unidad:      Optional[str] = None
    precio:      Optional[Decimal] = None
    moneda:      Optional[str] = None
    activo:      Optional[bool] = None

    @field_validator("nombre", "descripcion", "marca", "categoria")
    @classmethod
    def check_non_empty_optional(cls, v: Optional[str], info) -> Optional[str]:
        if v is not None:
            if not v or not v.strip():
                raise ValueError(f"El campo {info.field_name} no puede estar vacío")
            return v.strip()
        return v

    @field_validator("precio")
    @classmethod
    def check_positive_price_optional(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v <= 0:
            raise ValueError("El precio de venta debe ser mayor a 0")
        return v


class ProductoOut(ProductoBase):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    activo:     bool
    created_at: datetime


# ─── ÍTEM DE COTIZACIÓN ───────────────────────────────────────────────────────

class ItemBase(BaseModel):
    nombre:       str
    descripcion:  Optional[str] = None
    marca:        Optional[str] = None
    unidad:       str = "und"
    cantidad:     Decimal = Decimal("1")
    precio_unit:  Decimal
    moneda:       str = "PEN"
    particion:    str = "Principal"
    subparticion: Optional[str] = None
    orden:        int = 0


class ItemCreate(ItemBase):
    producto_id: Optional[int] = None


class ItemUpdate(BaseModel):
    nombre:       Optional[str] = None
    descripcion:  Optional[str] = None
    unidad:       Optional[str] = None
    cantidad:     Optional[Decimal] = None
    precio_unit:  Optional[Decimal] = None
    moneda:       Optional[str] = None
    particion:    Optional[str] = None
    subparticion: Optional[str] = None
    orden:        Optional[int] = None


class ReorderItemsReq(BaseModel):
    item_ids: list[int]


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id:           int
    cotizacion_id: int
    producto_id:  Optional[int] = None
    subtotal:     Decimal = Decimal("0")  # calculado en el response

    @classmethod
    def from_orm_item(cls, item) -> "ItemOut":
        data = {c.name: getattr(item, c.name) for c in item.__table__.columns}
        cot = getattr(item, "cotizacion", None)
        if cot is not None:
            # Mismo cálculo (margen + conversión + redondeo) que calcular_totales,
            # para que la suma de subtotales por línea cuadre con el resumen y el PDF.
            from app.modules.quote.service import convertir_precio, _moneda_codigo
            bruto = convertir_precio(
                precio=float(item.precio_unit) * float(item.cantidad),
                moneda_origen=item.moneda,
                moneda_destino=_moneda_codigo(cot.moneda),
                tipo_cambio=float(cot.tipo_cambio),
                utilidad=float(cot.utilidad),
            )
            data["subtotal"] = Decimal(str(bruto)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            data["subtotal"] = (
                Decimal(str(item.cantidad)) * Decimal(str(item.precio_unit))
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return cls(**data)


# ─── COTIZACIÓN ───────────────────────────────────────────────────────────────

class CotizacionBase(BaseModel):
    vendedor_nombre:        Optional[str] = None
    vendedor_correo:        Optional[str] = None
    vendedor_tel:           Optional[str] = None
    version:                Optional[str] = "A1"
    cliente_nombre:         str
    cliente_doc:            Optional[str] = None
    tipo_doc:               Optional[str] = "RUC"
    cliente_dir:            Optional[str] = None
    cliente_atencion:       Optional[str] = None
    cliente_referencia:     Optional[str] = None
    cliente_correo:         Optional[str] = None
    cliente_tel:            Optional[str] = None
    moneda:                 str = "Soles (PEN)"
    tipo_cambio:            Decimal = Decimal("3.80")
    utilidad:               Decimal = Decimal("1.18")
    mostrar_precios:        bool = True
    cond_tecnicas:                   list[str] = []
    cond_comerciales:                list[str] = []
    cond_otras:                      list[str] = []
    cond_garantia:                   list[str] = []
    cond_garantia_servicio:          str = ""
    cuentas_bancarias:               list[dict] = []
    mostrar_cond_tecnicas:           bool = True
    mostrar_cond_comerciales:        bool = True
    mostrar_cond_otras:              bool = True
    mostrar_cond_garantia:           bool = True
    mostrar_cond_garantia_servicio:  bool = True
    mostrar_cuentas_bancarias:       bool = True
    notas:                           Optional[str] = None


class CotizacionCreate(CotizacionBase):
    pass


class CotizacionUpdate(BaseModel):
    vendedor_nombre:        Optional[str] = None
    vendedor_correo:        Optional[str] = None
    vendedor_tel:           Optional[str] = None
    version:                Optional[str] = None
    cliente_nombre:         Optional[str] = None
    cliente_doc:            Optional[str] = None
    tipo_doc:               Optional[str] = None
    cliente_dir:            Optional[str] = None
    cliente_atencion:       Optional[str] = None
    cliente_referencia:     Optional[str] = None
    cliente_correo:         Optional[str] = None
    cliente_tel:            Optional[str] = None
    moneda:                 Optional[str] = None
    tipo_cambio:                     Optional[Decimal] = None
    utilidad:                        Optional[Decimal] = None
    mostrar_precios:                 Optional[bool] = None
    cond_tecnicas:                   Optional[list[str]] = None
    cond_comerciales:                Optional[list[str]] = None
    cond_otras:                      Optional[list[str]] = None
    cond_garantia:                   Optional[list[str]] = None
    cond_garantia_servicio:          Optional[str] = None
    cuentas_bancarias:               Optional[list[dict]] = None
    mostrar_cond_tecnicas:           Optional[bool] = None
    mostrar_cond_comerciales:        Optional[bool] = None
    mostrar_cond_otras:              Optional[bool] = None
    mostrar_cond_garantia:           Optional[bool] = None
    mostrar_cond_garantia_servicio:  Optional[bool] = None
    mostrar_cuentas_bancarias:       Optional[bool] = None
    estado:                          Optional[str] = None
    notas:                           Optional[str] = None



class TotalesCotizacion(BaseModel):
    por_particion: dict[str, Decimal]
    subtotal:      Decimal
    igv:           Decimal
    total:         Decimal


class CotizacionOut(CotizacionBase):
    model_config = ConfigDict(from_attributes=True)

    id:          int
    correlativo: Optional[str] = None   # None mientras es borrador
    estado:      str
    created_at:  datetime
    updated_at:  datetime
    items:       list[ItemOut] = []
    totales:     Optional[TotalesCotizacion] = None


class CotizacionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:             int
    correlativo:    Optional[str] = None   # None mientras es borrador
    cliente_nombre: str
    moneda:         str
    estado:         str
    created_at:     datetime


class EstadoUpdate(BaseModel):
    estado: str


# ─── PLANTILLAS GLOBALES ──────────────────────────────────────────────────────

class PlantillasGlobalesBase(BaseModel):
    cond_tecnicas:          Optional[list[str]] = None
    cond_comerciales:       Optional[list[str]] = None
    cond_otras:             Optional[list[str]] = None
    cond_garantia:          Optional[list[str]] = None
    cond_garantia_servicio: Optional[str] = None
    cuentas_bancarias:      Optional[list[dict]] = None


class PlantillasGlobalesUpdate(PlantillasGlobalesBase):
    pass


class PlantillasGlobalesOut(PlantillasGlobalesBase):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    updated_at: datetime


# Los schemas de Usuario y Cliente viven en app.modules.shared.schemas
# (re-exportados al inicio de este archivo).
