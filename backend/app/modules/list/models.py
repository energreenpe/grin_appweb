"""
Modelos SQLAlchemy del módulo LIST.

Sin FK a otros módulos. Los documentos subidos/convertidos no se modelan como tabla:
son archivos efímeros gestionados por `app.storage` con TTL (ver entregables #3/#6).
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.db import Base


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
