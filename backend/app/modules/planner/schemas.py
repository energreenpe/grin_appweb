"""
schemas.py — Schemas Pydantic v2 del módulo PLANNER (subset core E2).

Convenciones grin_web:
- Los enums se reusan desde `models.py` (única fuente de verdad), no se redefinen.
- `ConfigDict(from_attributes=True)` para leer desde ORM.
- `nombre_persona`/`profesion` se derivan con un `model_validator(mode="before")`
  limpio (sin inyectar en `obj.__dict__` desde el service).

Asistencia, feriados, Curva S, fotos y reportes se agregan en E3–E6.
"""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.planner.models import (
    EstadoProyecto, EstadoActividad, PrioridadActividad,
    EstadoMiembro, RolCuadrilla, TipoDependencia, EstadoAsistencia, TipoFeriado,
)


# ── Subtarea (checklist de una actividad) ──
class SubtareaSchema(BaseModel):
    texto: str = Field(..., min_length=1, max_length=300)
    hecho: bool = False


# ───────────────── PROYECTO ─────────────────
class ProyectoCreate(BaseModel):
    nombre:              str                = Field(..., min_length=2, max_length=200)
    cliente:             Optional[str]      = None
    ubicacion:           Optional[str]      = None
    region:              Optional[str]      = None
    paneles:             Optional[int]      = Field(0, ge=0)
    estado:              EstadoProyecto     = EstadoProyecto.pendiente
    fecha_inicio:        Optional[date]     = None
    fecha_fin:           Optional[date]     = None
    alcance:             Optional[str]      = None
    quote_id:            Optional[int]      = None
    inspector_visita_id: Optional[int]      = None


class ProyectoUpdate(BaseModel):
    nombre:             Optional[str]            = Field(None, min_length=2, max_length=200)
    cliente:            Optional[str]            = None
    ubicacion:          Optional[str]            = None
    region:             Optional[str]            = None
    paneles:            Optional[int]            = Field(None, ge=0)
    avance_planificado: Optional[float]          = Field(None, ge=0, le=100)
    avance_real:        Optional[float]          = Field(None, ge=0, le=100)
    estado:             Optional[EstadoProyecto] = None
    fecha_inicio:       Optional[date]           = None
    fecha_fin:          Optional[date]           = None
    fecha_fin_real:     Optional[date]           = None
    alcance:            Optional[str]            = None


class ProyectoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:                  int
    nombre:              str
    cliente:             Optional[str]
    ubicacion:           Optional[str]
    region:              Optional[str]
    paneles:             Optional[int]
    avance_planificado:  Optional[float]
    avance_real:         Optional[float]
    estado:              EstadoProyecto
    fecha_inicio:        Optional[date]
    fecha_fin:           Optional[date]
    fecha_fin_real:      Optional[date]
    alcance:             Optional[str]
    quote_id:            Optional[int]
    inspector_visita_id: Optional[int]
    created_at:          Optional[datetime] = None


# ───────────────── PERSONAL ─────────────────
class PersonalCreate(BaseModel):
    nombre:    str               = Field(..., min_length=2, max_length=200)
    dni:       Optional[str]     = None
    celular:   Optional[str]     = None
    profesion: Optional[str]     = "Técnico Electricista"
    email:     Optional[str]     = None
    estado:    EstadoMiembro     = EstadoMiembro.activo


class PersonalUpdate(BaseModel):
    nombre:    Optional[str]           = Field(None, min_length=2, max_length=200)
    dni:       Optional[str]           = None
    celular:   Optional[str]           = None
    profesion: Optional[str]           = None
    email:     Optional[str]           = None
    estado:    Optional[EstadoMiembro] = None


class PersonalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:         int
    nombre:     str
    dni:        Optional[str]
    celular:    Optional[str]
    profesion:  Optional[str]
    email:      Optional[str]
    estado:     EstadoMiembro
    created_at: Optional[datetime] = None


# ───────────────── CUADRILLA ─────────────────
class CuadrillaCreate(BaseModel):
    proyecto_id: int
    nombre:      str           = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None


class CuadrillaUpdate(BaseModel):
    nombre:      Optional[str]  = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str]  = None
    activa:      Optional[bool] = None


class MiembroEnCuadrillaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:             int
    persona_id:     int
    nombre_persona: str            = ""
    profesion:      Optional[str]  = None
    rol_interno:    RolCuadrilla
    activo:         bool
    fecha_ingreso:  Optional[date] = None
    fecha_salida:   Optional[date] = None

    @model_validator(mode="before")
    @classmethod
    def _derivar_persona(cls, obj):
        """Deriva nombre_persona/profesion desde la relación ORM `persona`.

        Reemplaza el hack del fork (inyectar en obj.__dict__ desde el service).
        Acepta tanto el objeto ORM como un dict ya armado.
        """
        if isinstance(obj, dict):
            return obj
        persona = getattr(obj, "persona", None)
        return {
            "id":             obj.id,
            "persona_id":     obj.persona_id,
            "nombre_persona": persona.nombre if persona else f"Persona #{obj.persona_id}",
            "profesion":      persona.profesion if persona else None,
            "rol_interno":    obj.rol_interno,
            "activo":         obj.activo,
            "fecha_ingreso":  obj.fecha_ingreso,
            "fecha_salida":   obj.fecha_salida,
        }


class CuadrillaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:          int
    proyecto_id: int
    nombre:      str
    descripcion: Optional[str]
    activa:      bool
    miembros:    List[MiembroEnCuadrillaResponse] = []


# ── Miembros de cuadrilla ──
class AsignarMiembroRequest(BaseModel):
    persona_id:    int
    rol_interno:   RolCuadrilla   = RolCuadrilla.tecnico
    fecha_ingreso: Optional[date] = None


class CambiarCuadrillaRequest(BaseModel):
    nueva_cuadrilla_id: int
    rol_interno:        RolCuadrilla   = RolCuadrilla.tecnico
    fecha_cambio:       Optional[date] = None


# ───────────────── ACTIVIDAD ─────────────────
class DependenciaCreate(BaseModel):
    depende_de_id: int
    tipo:          TipoDependencia = TipoDependencia.fs
    lag_dias:      int = 0


class DependenciaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:            int
    actividad_id:  int
    depende_de_id: int
    tipo:          TipoDependencia
    lag_dias:      int


class ActividadCreate(BaseModel):
    proyecto_id:       int
    padre_id:          Optional[int]        = None
    cuadrilla_id:      Optional[int]        = None
    responsable_id:    Optional[int]        = None
    titulo:            str                  = Field(..., min_length=2, max_length=300)
    descripcion:       Optional[str]        = None
    nivel:             int                  = Field(0, ge=0, le=5)
    orden:             int                  = 0
    fecha_inicio_plan: Optional[date]       = None
    fecha_fin_plan:    Optional[date]       = None
    duracion_dias:     int                  = Field(1, ge=0)
    estado:            EstadoActividad      = EstadoActividad.pendiente
    prioridad:         PrioridadActividad   = PrioridadActividad.media
    subtareas:         List[SubtareaSchema] = []
    es_hito:           bool                 = False
    dependencias:      List[DependenciaCreate] = []


class ActividadUpdate(BaseModel):
    padre_id:          Optional[int]                  = None
    cuadrilla_id:      Optional[int]                  = None
    responsable_id:    Optional[int]                  = None
    titulo:            Optional[str]                  = Field(None, min_length=2, max_length=300)
    descripcion:       Optional[str]                  = None
    orden:             Optional[int]                  = None
    fecha_inicio_plan: Optional[date]                 = None
    fecha_fin_plan:    Optional[date]                 = None
    duracion_dias:     Optional[int]                  = Field(None, ge=0)
    fecha_inicio_real: Optional[date]                 = None
    fecha_fin_real:    Optional[date]                 = None
    avance:            Optional[float]                = Field(None, ge=0, le=100)
    estado:            Optional[EstadoActividad]      = None
    prioridad:         Optional[PrioridadActividad]   = None
    subtareas:         Optional[List[SubtareaSchema]] = None
    es_hito:           Optional[bool]                 = None


class ActividadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:                  int
    proyecto_id:         int
    padre_id:            Optional[int]
    cuadrilla_id:        Optional[int]
    responsable_id:      Optional[int]
    titulo:              str
    descripcion:         Optional[str]
    nivel:               int
    orden:               int
    es_hito:             bool
    fecha_inicio_plan:   Optional[date]
    fecha_fin_plan:      Optional[date]
    duracion_dias:       int
    fecha_inicio_real:   Optional[date]
    fecha_fin_real:      Optional[date]
    avance:              float
    estado:              EstadoActividad
    prioridad:           PrioridadActividad
    subtareas:           List[SubtareaSchema] = []
    dependencias_salida: List[DependenciaResponse] = []
    hijos:               List["ActividadResponse"] = []
    created_at:          Optional[datetime] = None

    @field_validator("subtareas", mode="before")
    @classmethod
    def _subtareas_no_none(cls, v):
        # La columna JSON puede venir None; normalizar a lista.
        return v if v is not None else []


ActividadResponse.model_rebuild()


# ───────────────── ASISTENCIA ─────────────────
class AsistenciaCreate(BaseModel):
    proyecto_id:    int
    persona_id:     Optional[int]    = None
    cuadrilla_id:   Optional[int]    = None
    estado:         EstadoAsistencia = EstadoAsistencia.presente
    hora:           Optional[str]    = None
    fecha:          date
    observacion:    Optional[str]    = None
    registrado_por: Optional[str]    = None


class AsistenciaUpdate(BaseModel):
    estado:      Optional[EstadoAsistencia] = None
    hora:        Optional[str] = None
    observacion: Optional[str] = None


class AsistenciaBulkItem(BaseModel):
    persona_id:  int
    estado:      EstadoAsistencia = EstadoAsistencia.presente
    hora:        Optional[str] = None
    observacion: Optional[str] = None


class AsistenciaBulkCreate(BaseModel):
    proyecto_id:    int
    fecha:          date
    registrado_por: Optional[str] = None
    registros:      List[AsistenciaBulkItem]


class AsistenciaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:             int
    proyecto_id:    int
    persona_id:     Optional[int]
    cuadrilla_id:   Optional[int]
    estado:         EstadoAsistencia
    hora:           Optional[str]
    fecha:          date
    observacion:    Optional[str]
    registrado_por: Optional[str]
    nombre_persona: str = ""
    created_at:     Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def _derivar_persona(cls, obj):
        if isinstance(obj, dict):
            return obj
        persona = getattr(obj, "persona", None)
        return {
            "id":             obj.id,
            "proyecto_id":    obj.proyecto_id,
            "persona_id":     obj.persona_id,
            "cuadrilla_id":   obj.cuadrilla_id,
            "estado":         obj.estado,
            "hora":           obj.hora,
            "fecha":          obj.fecha,
            "observacion":    obj.observacion,
            "registrado_por": obj.registrado_por,
            "nombre_persona": persona.nombre if persona else (f"Persona #{obj.persona_id}" if obj.persona_id else ""),
            "created_at":     obj.created_at,
        }


# ───────────────── CURVA S ─────────────────
class CurvaSSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:                 int
    proyecto_id:        int
    fecha:              date
    avance_planificado: float
    avance_real:        float
    actividades_total:  int
    actividades_hechas: int
    created_at:         Optional[datetime] = None


# ───────────────── FOTOS (EVIDENCIA) ─────────────────
class FotoUpdate(BaseModel):
    incluir_en_pdf: Optional[bool] = None
    comentario_pdf: Optional[str]  = None
    etapa:          Optional[str]  = None


class FotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:              int
    proyecto_id:     int
    actividad_id:    Optional[int]
    etapa:           Optional[str]
    etapa_codigo:    Optional[str]
    subido_por:      Optional[str]
    fecha:           date
    ruta:            Optional[str]     # ruta relativa en uploads/ (anti-traversal)
    url:             Optional[str] = None  # ruta servible por el mount /uploads
    nombre_original: Optional[str]
    mime_type:       Optional[str]
    emoji:           Optional[str]
    incluir_en_pdf:  bool
    comentario_pdf:  Optional[str]
    created_at:      Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def _derivar_url(cls, obj):
        if isinstance(obj, dict):
            data = dict(obj)
        else:
            data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        ruta = data.get("ruta")
        data["url"] = f"/{ruta}" if ruta else None
        return data


# ───────────────── FERIADOS ─────────────────
class FeriadoCreate(BaseModel):
    nombre:     str             = Field(..., min_length=2, max_length=200)
    fecha:      date
    tipo:       TipoFeriado     = TipoFeriado.nacional
    region:     Optional[str]   = None
    anio:       Optional[int]   = None  # si no se da, se deriva de fecha.year
    recurrente: bool            = True


class FeriadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:         int
    nombre:     str
    fecha:      date
    tipo:       TipoFeriado
    region:     Optional[str]
    anio:       int
    recurrente: bool


# ───────────────── KPIs ─────────────────
class PlannerKPIResponse(BaseModel):
    total_proyectos:             int
    proyectos_activos:           int
    proyectos_completados:       int
    total_paneles:               int
    promedio_avance_real:        float
    promedio_avance_planificado: float
    total_personal:              int
    personal_activo:             int
    total_cuadrillas:            int


# ───────────────── GENÉRICO ─────────────────
class MessageResponse(BaseModel):
    message: str
    success: bool = True
