from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


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
    pass


class ProductoUpdate(BaseModel):
    categoria:   Optional[str] = None
    nombre:      Optional[str] = None
    descripcion: Optional[str] = None
    marca:       Optional[str] = None
    unidad:      Optional[str] = None
    precio:      Optional[Decimal] = None
    moneda:      Optional[str] = None
    activo:      Optional[bool] = None


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
        data["subtotal"] = Decimal(str(item.cantidad)) * Decimal(str(item.precio_unit))
        return cls(**data)


# ─── COTIZACIÓN ───────────────────────────────────────────────────────────────

class CotizacionBase(BaseModel):
    vendedor_nombre:        Optional[str] = None
    vendedor_correo:        Optional[str] = None
    vendedor_tel:           Optional[str] = None
    version:                Optional[str] = "1.0"
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
    utilidad:               Decimal = Decimal("1.30")
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
    correlativo: str
    estado:      str
    created_at:  datetime
    updated_at:  datetime
    items:       list[ItemOut] = []
    totales:     Optional[TotalesCotizacion] = None


class CotizacionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:             int
    correlativo:    str
    cliente_nombre: str
    moneda:         str
    estado:         str
    created_at:     datetime


# ─── EMPRESA ──────────────────────────────────────────────────────────────────

class EmpresaBase(BaseModel):
    nombre:    str = "Energreen Perú E.I.R.L."
    ruc:       Optional[str] = "20604756821"
    direccion: Optional[str] = None
    telefono:  Optional[str] = None
    email:     Optional[str] = None
    logo_path: Optional[str] = None


class EmpresaUpdate(EmpresaBase):
    nombre: Optional[str] = None


class EmpresaOut(EmpresaBase):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    updated_at: datetime


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


# ─── USUARIO ──────────────────────────────────────────────────────────────────

class UsuarioBase(BaseModel):
    nombre:   str
    correo:   str
    telefono: Optional[str] = None
    rol:      Optional[str] = "vendedor"


class UsuarioCreate(UsuarioBase):
    pass


class UsuarioOut(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    activo:     bool
    created_at: datetime


# ─── CLIENTE ──────────────────────────────────────────────────────────────────

class DatosClienteBase(BaseModel):
    nombre:      str
    documento:   Optional[str] = None
    direccion:   Optional[str] = None
    atencion:    Optional[str] = None
    referencia:  Optional[str] = None
    correo:      Optional[str] = None
    telefono:    Optional[str] = None

class DatosClienteCreate(DatosClienteBase):
    pass

class DatosClienteOut(DatosClienteBase):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    created_at: datetime
