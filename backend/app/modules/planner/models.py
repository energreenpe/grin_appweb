"""
models.py — Tablas del módulo PLANNER (gestión de proyectos fotovoltaicos).

10 tablas planner_*: proyectos, cuadrillas, personal, miembros_cuadrilla,
actividades (jerárquicas con dependencias), feriados, asistencia, fotos y
snapshots de Curva S.

Convenciones grin_web:
- `from app.db import Base`.
- `subtareas` se guarda como `Column(JSON)` (como math/list), NO como Text con
  json.dumps manual.
- `quote_id` / `inspector_visita_id` son soft-references Integer SIN FK
  (cero imports cruzados entre módulos de feature).
"""

import enum

from sqlalchemy import (
    Column, Integer, String, Float, Date, Text, JSON,
    ForeignKey, Enum, Boolean, DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


# ─────────────────────────────────────────────
# ENUMS (nativos PostgreSQL)
# ─────────────────────────────────────────────

class EstadoProyecto(str, enum.Enum):
    pendiente   = "Pendiente"
    en_progreso = "En Progreso"
    completado  = "Completado"
    cancelado   = "Cancelado"

class EstadoActividad(str, enum.Enum):
    pendiente  = "Pendiente"
    en_curso   = "En curso"
    completado = "Completado"
    bloqueado  = "Bloqueado"

class PrioridadActividad(str, enum.Enum):
    alta  = "Alta"
    media = "Media"
    baja  = "Baja"

class EstadoMiembro(str, enum.Enum):
    activo   = "Activo"
    inactivo = "Inactivo"

class RolCuadrilla(str, enum.Enum):
    jefe_cuadrilla = "Jefe de Cuadrilla"
    capataz        = "Capataz"
    tecnico        = "Técnico"
    instalador     = "Instalador"
    operario       = "Operario"
    peon           = "Peón"
    supervisor     = "Supervisor"
    ingeniero      = "Ingeniero"
    otro           = "Otro"

class EstadoAsistencia(str, enum.Enum):
    presente = "Presente"
    tardanza = "Tardanza"
    ausente  = "Ausente"

class TipoFeriado(str, enum.Enum):
    nacional = "Nacional"
    regional = "Regional"

class TipoDependencia(str, enum.Enum):
    fs = "FS"  # Finish to Start (más común)
    ss = "SS"  # Start to Start
    ff = "FF"  # Finish to Finish
    sf = "SF"  # Start to Finish


# ─────────────────────────────────────────────
# TABLA: planner_proyectos
# ─────────────────────────────────────────────

class Proyecto(Base):
    __tablename__ = "planner_proyectos"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    nombre              = Column(String(200), nullable=False)
    cliente             = Column(String(200), nullable=True, default="")
    ubicacion           = Column(String(200), nullable=True, default="")
    region              = Column(String(100), nullable=True, default="")   # para feriados regionales
    paneles             = Column(Integer,     nullable=True, default=0)
    avance_planificado  = Column(Float,       nullable=True, default=0.0)  # % según Gantt
    avance_real         = Column(Float,       nullable=True, default=0.0)  # % según actividades
    estado              = Column(Enum(EstadoProyecto), nullable=False, default=EstadoProyecto.pendiente)
    fecha_inicio        = Column(Date, nullable=True)
    fecha_fin           = Column(Date, nullable=True)
    fecha_fin_real      = Column(Date, nullable=True)  # fin real (puede diferir del planificado)
    alcance             = Column(Text, nullable=True, default="")
    quote_id            = Column(Integer, nullable=True)  # soft-ref a quote (sin FK)
    inspector_visita_id = Column(Integer, nullable=True)  # soft-ref a inspector (sin FK)
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    updated_at          = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    cuadrillas  = relationship("Cuadrilla",      back_populates="proyecto", cascade="all, delete-orphan")
    actividades = relationship("Actividad",      back_populates="proyecto", cascade="all, delete-orphan")
    asistencias = relationship("Asistencia",     back_populates="proyecto", cascade="all, delete-orphan")
    fotos       = relationship("Foto",           back_populates="proyecto", cascade="all, delete-orphan")
    snapshots   = relationship("CurvaSSnapshot", back_populates="proyecto", cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# TABLA: planner_cuadrillas (grupos de trabajo, no personas)
# ─────────────────────────────────────────────

class Cuadrilla(Base):
    """Grupo de trabajo dentro de un proyecto (ej: Cuadrilla 1, Cuadrilla Eléctrica)."""
    __tablename__ = "planner_cuadrillas"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(Integer, ForeignKey("planner_proyectos.id", ondelete="CASCADE"), nullable=False)
    nombre      = Column(String(100), nullable=False)
    descripcion = Column(String(300), nullable=True, default="")
    activa      = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    proyecto = relationship("Proyecto",        back_populates="cuadrillas")
    miembros = relationship("MiembroCuadrilla", back_populates="cuadrilla", cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# TABLA: planner_personal (catálogo global de personas)
# ─────────────────────────────────────────────

class Personal(Base):
    """Catálogo global de personal. Una persona puede estar en múltiples cuadrillas/proyectos."""
    __tablename__ = "planner_personal"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    nombre     = Column(String(200), nullable=False)
    dni        = Column(String(20),  nullable=True, default="")
    celular    = Column(String(20),  nullable=True, default="")
    profesion  = Column(String(100), nullable=True, default="Técnico Electricista")
    estado     = Column(Enum(EstadoMiembro), nullable=False, default=EstadoMiembro.activo)
    email      = Column(String(150), nullable=True, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    asignaciones = relationship("MiembroCuadrilla", back_populates="persona")
    asistencias  = relationship("Asistencia",        back_populates="persona")


# ─────────────────────────────────────────────
# TABLA: planner_miembros_cuadrilla (Personal ↔ Cuadrilla)
# ─────────────────────────────────────────────

class MiembroCuadrilla(Base):
    """Asignación de una persona a una cuadrilla con un rol interno específico."""
    __tablename__ = "planner_miembros_cuadrilla"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    cuadrilla_id  = Column(Integer, ForeignKey("planner_cuadrillas.id", ondelete="CASCADE"), nullable=False)
    persona_id    = Column(Integer, ForeignKey("planner_personal.id",   ondelete="CASCADE"), nullable=False)
    rol_interno   = Column(Enum(RolCuadrilla), nullable=False, default=RolCuadrilla.tecnico)
    activo        = Column(Boolean, default=True)
    fecha_ingreso = Column(Date, nullable=True)
    fecha_salida  = Column(Date, nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    cuadrilla = relationship("Cuadrilla", back_populates="miembros")
    persona   = relationship("Personal",  back_populates="asignaciones")


# ─────────────────────────────────────────────
# TABLA: planner_actividades (soporte Gantt jerárquico)
# ─────────────────────────────────────────────

class Actividad(Base):
    """Actividad del proyecto con soporte Gantt. Jerarquía multinivel padre→hijos→nietos."""
    __tablename__ = "planner_actividades"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id    = Column(Integer, ForeignKey("planner_proyectos.id",  ondelete="CASCADE"), nullable=False)
    padre_id       = Column(Integer, ForeignKey("planner_actividades.id", ondelete="CASCADE"), nullable=True)
    cuadrilla_id   = Column(Integer, ForeignKey("planner_cuadrillas.id",  ondelete="SET NULL"), nullable=True)
    responsable_id = Column(Integer, ForeignKey("planner_personal.id",    ondelete="SET NULL"), nullable=True)

    titulo      = Column(String(300), nullable=False)
    descripcion = Column(Text, nullable=True, default="")
    nivel       = Column(Integer, default=0)   # 0=título, 1=actividad, 2=subactividad, 3=sub-sub...
    orden       = Column(Integer, default=0)

    # Campos Gantt
    fecha_inicio_plan = Column(Date, nullable=True)
    fecha_fin_plan    = Column(Date, nullable=True)
    duracion_dias     = Column(Integer, default=1)   # días laborables
    fecha_inicio_real = Column(Date, nullable=True)
    fecha_fin_real    = Column(Date, nullable=True)
    avance            = Column(Float, default=0.0)   # 0-100%

    estado    = Column(Enum(EstadoActividad),   nullable=False, default=EstadoActividad.pendiente)
    prioridad = Column(Enum(PrioridadActividad), nullable=False, default=PrioridadActividad.media)
    subtareas = Column(JSON, nullable=True, default=list)  # checklist [{texto, hecho}]
    es_hito   = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    proyecto = relationship("Proyecto",  back_populates="actividades")
    hijos    = relationship("Actividad", back_populates="padre", cascade="all, delete-orphan")
    padre    = relationship("Actividad", back_populates="hijos", remote_side="Actividad.id")
    dependencias_salida  = relationship(
        "DependenciaActividad", foreign_keys="DependenciaActividad.actividad_id",
        back_populates="actividad", cascade="all, delete-orphan",
    )
    dependencias_entrada = relationship(
        "DependenciaActividad", foreign_keys="DependenciaActividad.depende_de_id",
        back_populates="depende_de",
    )


# ─────────────────────────────────────────────
# TABLA: planner_dependencias (relaciones entre actividades, estilo MS Project)
# ─────────────────────────────────────────────

class DependenciaActividad(Base):
    """Dependencia entre actividades: FS/SS/FF/SF + lag (días de adelanto/retraso)."""
    __tablename__ = "planner_dependencias"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    actividad_id  = Column(Integer, ForeignKey("planner_actividades.id", ondelete="CASCADE"), nullable=False)
    depende_de_id = Column(Integer, ForeignKey("planner_actividades.id", ondelete="CASCADE"), nullable=False)
    tipo          = Column(Enum(TipoDependencia), nullable=False, default=TipoDependencia.fs)
    lag_dias      = Column(Integer, default=0)

    actividad  = relationship("Actividad", foreign_keys=[actividad_id],  back_populates="dependencias_salida")
    depende_de = relationship("Actividad", foreign_keys=[depende_de_id], back_populates="dependencias_entrada")


# ─────────────────────────────────────────────
# TABLA: planner_feriados
# ─────────────────────────────────────────────

class Feriado(Base):
    """Feriados nacionales y regionales del Perú. El Gantt los respeta en días laborables."""
    __tablename__ = "planner_feriados"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    nombre     = Column(String(200), nullable=False)
    fecha      = Column(Date, nullable=False)
    tipo       = Column(Enum(TipoFeriado), nullable=False, default=TipoFeriado.nacional)
    region     = Column(String(100), nullable=True)   # solo feriados regionales (ej: "Piura")
    anio       = Column(Integer, nullable=False)
    recurrente = Column(Boolean, default=True)


# ─────────────────────────────────────────────
# TABLA: planner_asistencia
# ─────────────────────────────────────────────

class Asistencia(Base):
    __tablename__ = "planner_asistencia"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id    = Column(Integer, ForeignKey("planner_proyectos.id",  ondelete="CASCADE"), nullable=False)
    persona_id     = Column(Integer, ForeignKey("planner_personal.id",   ondelete="SET NULL"), nullable=True)
    cuadrilla_id   = Column(Integer, ForeignKey("planner_cuadrillas.id", ondelete="SET NULL"), nullable=True)
    estado         = Column(Enum(EstadoAsistencia), nullable=False, default=EstadoAsistencia.presente)
    hora           = Column(String(10), nullable=True, default="")
    fecha          = Column(Date, nullable=False)
    observacion    = Column(String(300), nullable=True, default="")
    registrado_por = Column(String(100), nullable=True, default="")
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="asistencias")
    persona  = relationship("Personal", back_populates="asistencias")


# ─────────────────────────────────────────────
# TABLA: planner_fotos
# ─────────────────────────────────────────────

class Foto(Base):
    __tablename__ = "planner_fotos"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id     = Column(Integer, ForeignKey("planner_proyectos.id",  ondelete="CASCADE"), nullable=False)
    actividad_id    = Column(Integer, ForeignKey("planner_actividades.id", ondelete="SET NULL"), nullable=True)
    etapa           = Column(String(200), nullable=True, default="General")
    etapa_codigo    = Column(String(50),  nullable=True, default="general")
    subido_por      = Column(String(200), nullable=True, default="")
    fecha           = Column(Date, nullable=False)
    ruta            = Column(String(500), nullable=True, default="")
    nombre_original = Column(String(300), nullable=True, default="")
    mime_type       = Column(String(100), nullable=True, default="image/jpeg")
    emoji           = Column(String(10),  nullable=True, default="📷")
    # Campos para exportación PDF
    incluir_en_pdf  = Column(Boolean, default=True)
    comentario_pdf  = Column(Text, nullable=True, default="")  # comentario manual
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    proyecto  = relationship("Proyecto",  back_populates="fotos")
    actividad = relationship("Actividad")


# ─────────────────────────────────────────────
# TABLA: planner_curva_s_snapshots
# ─────────────────────────────────────────────

class CurvaSSnapshot(Base):
    """Registro diario/semanal del avance real vs planificado para construir la Curva S."""
    __tablename__ = "planner_curva_s_snapshots"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id        = Column(Integer, ForeignKey("planner_proyectos.id", ondelete="CASCADE"), nullable=False)
    fecha              = Column(Date, nullable=False)
    avance_planificado = Column(Float, default=0.0)
    avance_real        = Column(Float, default=0.0)
    actividades_total  = Column(Integer, default=0)
    actividades_hechas = Column(Integer, default=0)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="snapshots")
