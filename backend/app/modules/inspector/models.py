from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

class Visita(Base):
    __tablename__ = "visitas"

    id           = Column(Integer, primary_key=True, index=True)

    # ── Vínculo con cliente (requerido, desde datos_cliente)
    cliente_id   = Column(Integer, ForeignKey("datos_cliente.id", ondelete="RESTRICT"), nullable=False, index=True)
    tipo_cliente = Column(String(50), nullable=False)   # "Persona" | "Empresa"

    # ── Técnico que realizó la visita (FK a usuarios — rol="tecnico")
    tecnico_id   = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)

    # ── Geolocalización del lugar visitado
    lat          = Column(Numeric(10, 6), nullable=True)
    lng          = Column(Numeric(10, 6), nullable=True)

    # ── Datos técnicos del sistema
    tipo_sistema = Column(String(100), nullable=True)
    conexion_red = Column(String(20), nullable=True)    # "Si" | "No" | null

    # ── Cargas críticas (Aislado e Híbrido)
    cargas_aislado = Column(JSON, nullable=False, default=list)

    # ── Información del techo
    tipo_techo   = Column(String(100), nullable=True)
    obs_techo    = Column(Text, nullable=True)
    obs_interior = Column(Text, nullable=True)

    # ── Archivos subidos al backend
    recibo_ruta    = Column(String(500), nullable=True)
    fotos_techo    = Column(JSON, nullable=False, default=list)
    fotos_interior = Column(JSON, nullable=False, default=list)

    # ── PDF generado
    pdf_url      = Column(String(500), nullable=True)

    # ── Metadatos
    estado       = Column(String(30), nullable=False, default="borrador")
    paso_actual  = Column(String(50), nullable=True, default="inicio")
    notas        = Column(Text, nullable=True)
    fecha        = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    # ── Relaciones ORM (solo lectura desde Inspector)
    cliente      = relationship("DatosCliente", foreign_keys=[cliente_id])
    tecnico      = relationship("Usuario", foreign_keys=[tecnico_id])


class GeoCache(Base):
    """Caché de reverse geocoding (coordenadas → nombre de dirección) para no
    repetir llamadas a Nominatim. La clave es lat/lng redondeados a 4 decimales
    (~11 m de grilla): dos lecturas del mismo sitio caen en la misma celda."""
    __tablename__ = "geo_cache"
    __table_args__ = (
        UniqueConstraint("lat_key", "lng_key", name="uq_geo_cache_grid"),
    )

    id         = Column(Integer, primary_key=True, index=True)
    lat_key    = Column(Numeric(9, 4), nullable=False)
    lng_key    = Column(Numeric(9, 4), nullable=False)
    direccion  = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
