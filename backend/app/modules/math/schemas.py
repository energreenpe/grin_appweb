"""
Schemas Pydantic del módulo MATH.

Entregable #2: schemas de lectura de catálogos. Las entradas/salidas de los
motores (Aislado / Autoconsumo) y el CRUD de Calculo se agregan después,
reutilizando DatosClienteOut / UsuarioOut desde app.modules.shared.schemas.
"""
from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.modules.shared.schemas import DatosClienteOut, UsuarioOut

# Conjunto cerrado de tipos de equipo técnico (validado en el borde por Pydantic).
TipoEquipo = Literal["panel", "bateria", "inversor_aislado", "inversor_autoconsumo"]
TipoBateria = Literal["Lead acid", "Lithium"]
TipoHSP = Literal["minimo", "promedio", "mayor"]
# Tipos de sistema: 2 activos + 2 en desarrollo (Híbrido, Bombeo Solar).
TipoSistema = Literal["SFV Aislado", "SFV Autoconsumo", "SFV Híbrido", "Bombeo Solar"]
TipoClienteLit = Literal["Persona", "Empresa"]
EstadoCalculo = Literal["borrador", "completado"]


class RegionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:           int
    nombre:       str
    hsp_minimo:   Optional[float] = None
    hsp_promedio: Optional[float] = None
    hsp_mayor:    Optional[float] = None


class EquipoTecnicoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:          int
    tipo:        str
    descripcion: str
    marca:       Optional[str] = None
    activo:      bool
    specs:       dict          # campos variables por tipo (Potencia, Vbat, wout, ...)


class ElectrodomesticoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:         int
    nombre:     str
    potencia_w: float
    categoria:  Optional[str] = None


# ── Motor Aislado: request ────────────────────────────────────────────────────
class CargaItemIn(BaseModel):
    nombre:     str
    cantidad:   int = Field(ge=1, le=1000)
    horas:      float = Field(ge=0, le=24)
    potencia_w: float = Field(ge=0, le=100_000)


class AisladoCalcularRequest(BaseModel):
    cargas:          list[CargaItemIn] = Field(min_length=1)
    # HSP: por región (se resuelve contra la tabla regiones) o un valor directo.
    region:          Optional[str] = None
    tipo_hsp:        TipoHSP = "promedio"
    hsp:             Optional[float] = Field(default=None, gt=0, le=12)
    dias_autonomia:  int = Field(ge=1, le=15)
    tipo_bateria:    TipoBateria = "Lead acid"
    panel_id:        int
    bateria_id:      int
    voltaje_sistema: Optional[Literal[12, 24, 48]] = None  # None = automático


# ── Motor Aislado: response ───────────────────────────────────────────────────
class ConsumoOut(BaseModel):
    potencia_maxima_w: float
    energia_diaria_wh: float
    potencia_ac_w:     float


class PanelResumen(BaseModel):
    descripcion: Optional[str] = None
    potencia_w:  float


class BateriaResumen(BaseModel):
    descripcion:  Optional[str] = None
    vbat:         float
    capacidad_ah: float


class InversorSugeridoOut(BaseModel):
    modelo:         str
    marca:          Optional[str] = ""
    wout:           float
    cantidad:       int
    potencia_total: float


class AisladoResultado(BaseModel):
    consumo:                    ConsumoOut
    voltaje_sistema:            int
    hsp:                        float
    potencia_pico_wp:           float
    num_paneles:                int
    potencia_solar_corregida_w: float
    panel:                      PanelResumen
    capacidad_ah:               float
    num_baterias:               int
    bateria:                    BateriaResumen
    potencia_inversor_w:        float
    inversores_sugeridos:       list[InversorSugeridoOut]


TipoConexion = Literal["Monofásico", "Trifásico"]

# ── Motor Autoconsumo (grid-tie) ──────────────────────────────────────────────
class AutoconsumoCalcularRequest(BaseModel):
    panel_id:            int
    inversor_id:         int                                  # EquipoTecnico tipo inversor_autoconsumo
    consumo_mensual:     float = Field(gt=0, le=100_000)      # kWh/mes
    potencia_contratada: float = Field(ge=0, le=10_000)       # kW
    autarquia:           float = Field(default=40, ge=0, le=100)   # %
    tipo_conexion:       Optional[TipoConexion] = None        # informativo / filtro en UI
    voltaje_red:         Optional[str] = None                 # informativo / filtro en UI ("220"/"380")
    temp_min:            float = Field(default=-10, ge=-40, le=40)
    temp_max:            float = Field(default=70, ge=0, le=90)


class OpcionAutoconsumo(BaseModel):
    target:              Literal["min", "opt", "max"]
    paneles_serie:       int
    mppt_trackers:       int
    entradas_por_mppt:   int
    paneles_total:       int
    potencia_sistema_kW: float
    ratio_dc_ac:         float
    excede_contratada:   bool = False


class ParametrosAutoconsumo(BaseModel):
    consumo_mensual:     float
    potencia_contratada: float
    autarquia:           float
    potencia_minima_kw:  float
    tipo_conexion:       Optional[str] = None
    voltaje_red:         Optional[str] = None


class PanelResumenAC(BaseModel):
    descripcion: Optional[str] = None
    potencia_w:  float


class InversorResumenAC(BaseModel):
    descripcion: Optional[str] = None
    wout_w:      float


class AutoconsumoResultado(BaseModel):
    panel:      PanelResumenAC
    inversor:   InversorResumenAC
    opciones:   list[OpcionAutoconsumo]
    parametros: ParametrosAutoconsumo


# ── Entidad Calculo (CRUD persistido) ─────────────────────────────────────────
class CalculoCreate(BaseModel):
    nombre_proyecto: str = Field(min_length=1, max_length=255)
    cliente_id:      int
    tipo_cliente:    TipoClienteLit
    ingeniero_id:    Optional[int] = None
    region:          Optional[str] = None
    tipo_sistema:    Optional[TipoSistema] = None
    entrada:         dict = {}                       # inputs según el tipo (libre, se valida al calcular)
    paso_actual:     Optional[str] = "inicio"
    notas:           Optional[str] = None


class CalculoUpdate(BaseModel):
    """Actualización parcial (se aplica con exclude_unset)."""
    nombre_proyecto: Optional[str] = Field(default=None, max_length=255)
    cliente_id:      Optional[int] = None
    tipo_cliente:    Optional[TipoClienteLit] = None
    ingeniero_id:    Optional[int] = None
    region:          Optional[str] = None
    tipo_sistema:    Optional[TipoSistema] = None
    entrada:         Optional[dict] = None
    paso_actual:     Optional[str] = None
    notas:           Optional[str] = None
    estado:          Optional[EstadoCalculo] = None


class CalculoListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:              int
    nombre_proyecto: str
    tipo_cliente:    Optional[str] = None
    tipo_sistema:    Optional[str] = None
    region:          Optional[str] = None
    estado:          str
    paso_actual:     Optional[str] = None
    fecha:           datetime
    cliente:         DatosClienteOut


class CalculoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:              int
    nombre_proyecto: str
    cliente_id:      int
    tipo_cliente:    str
    ingeniero_id:    Optional[int] = None
    region:          Optional[str] = None
    tipo_sistema:    Optional[str] = None
    entrada:         dict
    resultado:       Optional[dict] = None
    estado:          str
    paso_actual:     Optional[str] = None
    notas:           Optional[str] = None
    fecha:           datetime
    cliente:         DatosClienteOut
    ingeniero:       Optional[UsuarioOut] = None
