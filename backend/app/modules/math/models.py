"""
Modelos SQLAlchemy del módulo MATH.

- Calculo: entidad principal persistida (mismo patrón que Visita en inspector).
- EquipoTecnico / Region / ElectrodomesticoCatalogo: catálogos sembrados desde
  los JSON legacy (ver scripts/seed_math.py).

Las FK apuntan únicamente a entidades de `shared` (datos_cliente, usuarios);
no hay relación con quote ni inspector.
"""
from sqlalchemy import (
    Boolean, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Numeric, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class Calculo(Base):
    __tablename__ = "calculos"

    id              = Column(Integer, primary_key=True, index=True)
    nombre_proyecto = Column(String(255), nullable=False)

    # ── Vínculo con cliente (requerido, desde shared.datos_cliente)
    cliente_id      = Column(Integer, ForeignKey("datos_cliente.id", ondelete="RESTRICT"), nullable=False, index=True)
    tipo_cliente    = Column(String(50), nullable=False)   # "Persona" | "Empresa"

    # ── Ingeniero responsable (FK a usuarios — rol="ingeniero")
    ingeniero_id    = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)

    # ── Región donde se realiza el cálculo (provee HSP al motor aislado)
    region          = Column(String(100), nullable=True)

    # ── Tipo de sistema: "SFV Aislado" | "SFV Autoconsumo" | "SFV Híbrido" | "Bombeo Solar"
    tipo_sistema    = Column(String(100), nullable=True)

    # ── Datos del cálculo (JSON, esquema según el tipo de sistema)
    entrada         = Column(JSON, nullable=False, default=dict)   # inputs del usuario
    resultado       = Column(JSON, nullable=True)                  # salida del motor (snapshot)

    # ── Metadatos
    estado          = Column(String(30), nullable=False, default="borrador")   # borrador | completado
    paso_actual     = Column(String(50), nullable=True, default="inicio")
    notas           = Column(Text, nullable=True)
    fecha           = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # ── Relaciones ORM (solo lectura desde MATH)
    cliente         = relationship("DatosCliente", foreign_keys=[cliente_id])
    ingeniero       = relationship("Usuario", foreign_keys=[ingeniero_id])


class EquipoTecnico(Base):
    """Catálogo técnico: paneles, baterías e inversores. Reemplaza data_tecnica/*.json."""
    __tablename__ = "equipos_tecnicos"
    __table_args__ = (
        Index("ix_equipos_tecnicos_tipo_activo", "tipo", "activo"),
    )

    id          = Column(Integer, primary_key=True, index=True)
    # 'panel' | 'bateria' | 'inversor_aislado' | 'inversor_autoconsumo'
    tipo        = Column(String(40), nullable=False, index=True)
    descripcion = Column(String(255), nullable=False)
    marca       = Column(String(120), nullable=True)
    activo      = Column(Boolean, nullable=False, default=True)
    # Campos variables por tipo (Potencia, Vmpp, Vbat, wout, ...). Mapea 1:1 con el JSON legacy.
    specs       = Column(JSON, nullable=False, default=dict)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class Region(Base):
    """Regiones del Perú con sus Horas Sol Pico (HSP). Reemplaza Regiones_peru.json."""
    __tablename__ = "regiones"

    id            = Column(Integer, primary_key=True, index=True)
    nombre        = Column(String(120), nullable=False, unique=True, index=True)
    hsp_minimo    = Column(Numeric(4, 2), nullable=True)
    hsp_promedio  = Column(Numeric(4, 2), nullable=True)
    hsp_mayor     = Column(Numeric(4, 2), nullable=True)


class ElectrodomesticoCatalogo(Base):
    """Catálogo de potencias de electrodomésticos. Reemplaza el dict POTENCIAS."""
    __tablename__ = "electrodomesticos_catalogo"

    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String(120), nullable=False, unique=True, index=True)
    potencia_w  = Column(Numeric(10, 2), nullable=False)
    categoria   = Column(String(80), nullable=True)
