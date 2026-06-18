"""
Entidades transversales compartidas: Cliente, Usuario y Configuración de Empresa.
Su definición vive aquí (capa base). quote e inspector las consumen importándolas
desde este módulo; quote además las re-exporta por compatibilidad histórica.
"""
from sqlalchemy import (
    Boolean, Column, Integer, String, Text, DateTime, Index, text
)
from sqlalchemy.sql import func
from app.db import Base


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


class Usuario(Base):
    __tablename__ = "usuarios"

    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String(255), nullable=False)
    correo      = Column(String(100), nullable=False, unique=True, index=True)
    telefono    = Column(String(30), nullable=True)
    rol         = Column(String(50), nullable=False, server_default="vendedor")
    activo      = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
