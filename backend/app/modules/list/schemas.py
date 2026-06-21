"""
Schemas Pydantic v2 del módulo LIST.

Portados y ENDURECIDOS desde LIST/backend/app/modules/list/schemas.py:
- `font_family` como Literal de las fuentes PDF realmente soportadas.
- Validación de colores RGB (exactamente 3 componentes en [0.0, 1.0]).
- Restricciones de geometría (página ≥ 0, ancho/alto > 0) y tamaño de fuente.

Las coordenadas SIEMPRE están en PDF points (no en píxeles de pantalla); la
traducción HTML↔points la hace el frontend (utils/coords.js).
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing_extensions import Literal

# Fuentes PDF estándar soportadas por el estampador (mapean a helv/times/cour).
FontFamily = Literal["Helvetica", "Times-Roman", "Courier"]


def _validate_rgb(v: Optional[List[float]]) -> Optional[List[float]]:
    if v is None:
        return v
    if len(v) != 3:
        raise ValueError("El color debe tener exactamente 3 componentes RGB")
    if any(not (0.0 <= c <= 1.0) for c in v):
        raise ValueError("Cada componente RGB debe estar entre 0.0 y 1.0")
    return v


class ListFieldSchema(BaseModel):
    """Campo de texto estampable sobre el PDF (en points)."""
    page: int = Field(..., ge=0, description="Índice de página (0-indexed)")
    x: float = Field(..., description="Coordenada X en PDF points")
    y: float = Field(..., description="Coordenada Y en PDF points")
    width: float = Field(..., gt=0, description="Ancho en PDF points")
    height: float = Field(..., gt=0, description="Alto en PDF points")
    text: str = Field("", max_length=10000)
    font_family: FontFamily = "Helvetica"
    font_size: int = Field(12, ge=1, le=400)
    font_color: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    bg_color: Optional[List[float]] = Field(default=None)

    @field_validator("font_color")
    @classmethod
    def _check_font_color(cls, v):
        return _validate_rgb(v)

    @field_validator("bg_color")
    @classmethod
    def _check_bg_color(cls, v):
        return _validate_rgb(v)


class ListOverlaySchema(BaseModel):
    """Rectángulo de cobertura para ocultar contenido del PDF (en points)."""
    page: int = Field(..., ge=0)
    x: float
    y: float
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)
    color: List[float] = Field(default_factory=lambda: [1.0, 1.0, 1.0])

    @field_validator("color")
    @classmethod
    def _check_color(cls, v):
        return _validate_rgb(v)


# ── Plantillas (persistencia en PostgreSQL; CRUD en el entregable #5) ───────────
class ListPlantillaCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    pdf_name: str = Field(..., min_length=1, max_length=255)
    fields: List[ListFieldSchema] = Field(default_factory=list)
    overlays: List[ListOverlaySchema] = Field(default_factory=list)


class ListPlantillaListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    pdf_name: str
    created_at: Optional[datetime] = None


class ListPlantillaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    pdf_name: str
    fields: List[ListFieldSchema] = Field(default_factory=list)
    overlays: List[ListOverlaySchema] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── Subida / estado de jobs de conversión ──────────────────────────────────────
class UploadResponse(BaseModel):
    """Respuesta de POST /upload. Para .pdf el atajo devuelve status=finished y la
    URL directamente; para DOCX/XLSX devuelve job_id con status=queued."""
    job_id: Optional[str] = None
    status: str
    pdf_name: Optional[str] = None
    pdf_url: Optional[str] = None


class JobStatusOut(BaseModel):
    """Estado de un job (conversión o estampado), para polling del frontend.

    `result` lleva el dict crudo del job: para conversión {pdf_name, pdf_url};
    para estampado {output_name, output_url}. `pdf_name`/`pdf_url` se mantienen por
    conveniencia cuando el job es de conversión."""
    job_id: str
    status: str  # queued | started | finished | failed | deferred | ...
    pdf_name: Optional[str] = None
    pdf_url: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


# ── Exportación / estampado ─────────────────────────────────────────────────────
class ExportPayload(BaseModel):
    """Campos y overlays a estampar sobre un PDF base (en PDF points)."""
    pdf_name: str = Field(..., min_length=1, max_length=255)
    fields: List[ListFieldSchema] = Field(default_factory=list)
    overlays: List[ListOverlaySchema] = Field(default_factory=list)


class ExportResponse(BaseModel):
    job_id: str
    status: str


# ── Documentos (persistencia + resume) ──────────────────────────────────────────
class ListDocumentoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    pdf_name: str = Field(..., min_length=1, max_length=255)
    fields: List[ListFieldSchema] = Field(default_factory=list)
    overlays: List[ListOverlaySchema] = Field(default_factory=list)


class ListDocumentoUpdate(BaseModel):
    """Actualización parcial (autoguardado): solo se aplican los campos presentes."""
    nombre: Optional[str] = Field(default=None, max_length=255)
    fields: Optional[List[ListFieldSchema]] = None
    overlays: Optional[List[ListOverlaySchema]] = None


class ListDocumentoListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    pdf_name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ListDocumentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    pdf_name: str
    fields: List[ListFieldSchema] = Field(default_factory=list)
    overlays: List[ListOverlaySchema] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
