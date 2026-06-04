from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, Numeric,
    String, Text, DateTime, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class Producto(Base):
    __tablename__ = "productos"

    id          = Column(Integer, primary_key=True, index=True)
    categoria   = Column(String(100), nullable=False)
    nombre      = Column(String(255), nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    marca       = Column(String(100), nullable=True)
    unidad      = Column(String(50), nullable=False, default="und")
    precio      = Column(Numeric(12, 2), nullable=False, default=0)
    moneda      = Column(String(3), nullable=False, default="PEN")
    activo      = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    # Relación inversa (opcional, para consultas)
    items = relationship("ItemCotizacion", back_populates="producto")


class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id                      = Column(Integer, primary_key=True, index=True)
    correlativo             = Column(String(20), nullable=False, unique=True, index=True)

    # Datos del vendedor
    vendedor_nombre         = Column(String(255), nullable=True)
    vendedor_correo         = Column(String(100), nullable=True)
    vendedor_tel            = Column(String(30), nullable=True)
    version                 = Column(String(10), default="1.0")

    # Datos del cliente
    cliente_nombre          = Column(String(255), nullable=False)
    cliente_doc             = Column(String(15), nullable=True)
    tipo_doc                = Column(String(5), default="RUC")
    cliente_dir             = Column(Text, nullable=True)
    cliente_atencion        = Column(String(255), nullable=True)
    cliente_referencia      = Column(String(255), nullable=True)
    cliente_correo          = Column(String(100), nullable=True)
    cliente_tel             = Column(String(30), nullable=True)

    # Configuración financiera
    moneda                  = Column(String(20), nullable=False, default="Soles (PEN)")
    tipo_cambio             = Column(Numeric(8, 4), nullable=False, default=3.80)
    utilidad                = Column(Numeric(6, 4), nullable=False, default=1.30)
    mostrar_precios         = Column(Boolean, nullable=False, default=True)

    # Condiciones (almacenadas como JSON arrays)
    cond_tecnicas                   = Column(JSON, default=list)
    cond_comerciales                = Column(JSON, default=list)
    cond_otras                      = Column(JSON, default=list)
    cond_garantia                   = Column(JSON, default=list)
    cond_garantia_servicio          = Column(Text, default="")
    cuentas_bancarias               = Column(JSON, default=list)

    # Visibilidad de secciones en PDF
    mostrar_cond_tecnicas           = Column(Boolean, nullable=False, default=True)
    mostrar_cond_comerciales        = Column(Boolean, nullable=False, default=True)
    mostrar_cond_otras              = Column(Boolean, nullable=False, default=True)
    mostrar_cond_garantia           = Column(Boolean, nullable=False, default=True)
    mostrar_cond_garantia_servicio  = Column(Boolean, nullable=False, default=True)
    mostrar_cuentas_bancarias       = Column(Boolean, nullable=False, default=True)

    # Estado
    estado                          = Column(String(20), nullable=False, default="borrador")
    notas                   = Column(Text, nullable=True)
    created_at              = Column(DateTime(timezone=True), server_default=func.now())
    updated_at              = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    items = relationship("ItemCotizacion", back_populates="cotizacion",
                         cascade="all, delete-orphan", order_by="ItemCotizacion.orden")


class ItemCotizacion(Base):
    __tablename__ = "items_cotizacion"

    id              = Column(Integer, primary_key=True, index=True)
    cotizacion_id   = Column(Integer, ForeignKey("cotizaciones.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id     = Column(Integer, ForeignKey("productos.id", ondelete="SET NULL"), nullable=True)

    # Snapshot editable del producto
    nombre          = Column(String(255), nullable=False)
    descripcion     = Column(Text, nullable=True)
    marca           = Column(String(100), nullable=True)
    unidad          = Column(String(50), nullable=False, default="und")
    cantidad        = Column(Numeric(10, 2), nullable=False, default=1)
    precio_unit     = Column(Numeric(12, 2), nullable=False)
    moneda          = Column(String(3), nullable=False, default="PEN")

    # Agrupación (partición / subpartición)
    particion       = Column(String(100), nullable=False, default="Principal")
    subparticion    = Column(String(100), nullable=True)
    orden           = Column(Integer, nullable=False, default=0)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    cotizacion  = relationship("Cotizacion", back_populates="items")
    producto    = relationship("Producto", back_populates="items")


class EmpresaConfig(Base):
    __tablename__ = "empresa_config"

    id          = Column(Integer, primary_key=True, default=1)
    nombre      = Column(String(255), nullable=False, default="Energreen Perú E.I.R.L.")
    ruc         = Column(String(11), nullable=True, default="20604756821")
    direccion   = Column(Text, nullable=True, default="Urb. Los Tallanes 1ra Etapa Mz. C-16, Piura")
    telefono    = Column(String(20), nullable=True)
    email       = Column(String(100), nullable=True)
    logo_path   = Column(String(255), nullable=True)
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PlantillasGlobales(Base):
    __tablename__ = "plantillas_globales"

    id = Column(Integer, primary_key=True, default=1)
    cond_tecnicas = Column(JSON, default=list)
    cond_comerciales = Column(JSON, default=list)
    cond_otras = Column(JSON, default=list)
    cond_garantia = Column(JSON, default=list)
    cond_garantia_servicio = Column(Text, default="")
    cuentas_bancarias = Column(JSON, default=list)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─── CLIENTE ─────────────────────────────────────────────────────────────────

class DatosCliente(Base):
    __tablename__ = "datos_cliente"

    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String(255), nullable=False, unique=True, index=True)
    documento   = Column(String(50), nullable=True) # RUC o DNI
    direccion   = Column(Text, nullable=True)
    atencion    = Column(String(255), nullable=True)
    referencia  = Column(Text, nullable=True)
    correo      = Column(String(100), nullable=True)
    telefono    = Column(String(50), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())



class Usuario(Base):
    __tablename__ = "usuarios"

    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String(255), nullable=False)
    correo      = Column(String(100), nullable=False, unique=True, index=True)
    telefono    = Column(String(30), nullable=True)
    rol         = Column(String(50), nullable=False, server_default="vendedor")
    activo      = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
