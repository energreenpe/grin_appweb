"""
Modelos SQLAlchemy del módulo LIST.

- ListPlantilla: configuración reutilizable de campos (fields) y coberturas (overlays)
  posicionados sobre un PDF base, en coordenadas PDF points. Reemplaza las plantillas
  que LIST guardaba como archivos JSON en disco (no aptas para multi-instancia).

Sin FK a otros módulos. Los documentos subidos/convertidos no se modelan como tabla:
son archivos efímeros gestionados por `app.storage` con TTL (ver entregables #3/#6).
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.db import Base


class ListPlantilla(Base):
    __tablename__ = "list_plantillas"

    id         = Column(Integer, primary_key=True, index=True)
    nombre     = Column(String(255), nullable=False)

    # Referencia al PDF base con el que se diseñó la plantilla (nombre de archivo).
    pdf_name   = Column(String(255), nullable=False)

    # Geometría de los elementos, en PDF points. Misma forma que los schemas
    # ListFieldSchema / ListOverlaySchema (lista de dicts).
    fields     = Column(JSON, nullable=False, default=list)
    overlays   = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ListDocumento(Base):
    """Documento subido/convertido y EN EDICIÓN, persistido para poder reabrirlo y
    continuar. Su PDF base (`pdf_name`, en uploads/list/pdf/) es permanente: queda
    fuera de la limpieza por TTL mientras exista el documento."""
    __tablename__ = "list_documentos"

    id         = Column(Integer, primary_key=True, index=True)
    nombre     = Column(String(255), nullable=False)        # nombre original del archivo
    pdf_name   = Column(String(255), nullable=False)        # PDF base (convertido/subido)

    # Avance de edición (autoguardado), en PDF points.
    fields     = Column(JSON, nullable=False, default=list)
    overlays   = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
