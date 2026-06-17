from sqlalchemy import (
    Boolean, Column, ForeignKey, Index, Integer, Numeric,
    String, Text, DateTime, JSON, UniqueConstraint, text
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
    __table_args__ = (
        UniqueConstraint("correlativo_anio", "correlativo_num",
                         name="uq_cotizaciones_correlativo_anio_num"),
    )

    id                      = Column(Integer, primary_key=True, index=True)

    # Correlativo perezoso: el borrador NO tiene número. Se asigna (año + número)
    # al pasar a Enviada/Aprobada. El número reinicia por año. El correlativo
    # mostrado se arma con la versión actual -> CO{AA}-{NNNN}-{version}.
    correlativo_anio        = Column(Integer, nullable=True)
    correlativo_num         = Column(Integer, nullable=True)

    # Datos del vendedor
    vendedor_nombre         = Column(String(255), nullable=True)
    vendedor_correo         = Column(String(100), nullable=True)
    vendedor_tel            = Column(String(30), nullable=True)
    version                 = Column(String(10), default="A1")

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
    utilidad                = Column(Numeric(6, 4), nullable=False, default=1.18)
    # estados válidos: borrador, enviada, aprobada, rechazada
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

    @property
    def correlativo(self) -> str | None:
        """Correlativo completo CO{AA}-{NNNN}-{version}. None si aún es borrador."""
        if self.correlativo_anio is None or self.correlativo_num is None:
            return None
        base = f"CO{self.correlativo_anio % 100:02d}-{self.correlativo_num:04d}"
        ver = (self.version or "").strip()
        return f"{base}-{ver}" if ver else base


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
    __table_args__ = (
        # RUC/DNI único solo cuando tiene valor (los NULL no chocan entre sí)
        Index("uq_datos_cliente_documento", "documento", unique=True,
              postgresql_where=text("documento IS NOT NULL")),
    )

    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String(255), nullable=False, unique=True, index=True)
    documento   = Column(String(50), nullable=True) # RUC o DNI (único si tiene valor)
    direccion   = Column(Text, nullable=True)
    atencion    = Column(String(255), nullable=True)
    referencia  = Column(Text, nullable=True)
    correo      = Column(String(100), nullable=True)
    telefono    = Column(String(50), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())



class CorrelativoContador(Base):
    """Contador de correlativos por año. Solo avanza (nunca retrocede),
    por eso eliminar borradores no reutiliza ni saltea números."""
    __tablename__ = "correlativo_contador"

    anio          = Column(Integer, primary_key=True)   # año completo, ej. 2026
    ultimo_numero = Column(Integer, nullable=False, default=0)


class Usuario(Base):
    __tablename__ = "usuarios"

    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String(255), nullable=False)
    correo      = Column(String(100), nullable=False, unique=True, index=True)
    telefono    = Column(String(30), nullable=True)
    rol         = Column(String(50), nullable=False, server_default="vendedor")
    activo      = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
