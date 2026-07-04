from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.modules.shared.schemas import DatosClienteOut, UsuarioOut

# Conjuntos cerrados de valores válidos (validados en el borde de la API por Pydantic).
TipoCliente  = Literal["Persona", "Empresa"]
TipoSistema  = Literal["SFV Autoconsumo", "SFV Híbrido", "SFV Aislado", "Terma Solar", "BESS"]
ConexionRed  = Literal["Si", "No"]
TipoTecho    = Literal["Calamina", "Teja", "Concreto", "Suelo", "Eternit", "Otro"]
PasoActual   = Literal["inicio", "tipo_sistema", "conexion_red", "recibo_luz",
                       "cargas_criticas", "tipo_techo", "fotos_techo", "fotos_interior", "done"]
EstadoVisita = Literal["borrador", "completada"]

class GeoReverseOut(BaseModel):
    direccion: str = ""
    error:     Optional[str] = None
    manual:    bool = False
    cache:     Optional[bool] = None

class CargaItem(BaseModel):
    nombre:            str
    cantidad_unidades: int
    horas_dia:         float
    potencia_w:        float

class FotoItem(BaseModel):
    url:        str
    nombre:     str
    subida_en:  datetime

class VisitaCreate(BaseModel):
    cliente_id:     int
    tipo_cliente:   TipoCliente
    tecnico_id:     Optional[int] = None
    lat:            Optional[float] = None
    lng:            Optional[float] = None
    tipo_sistema:   Optional[TipoSistema] = None
    conexion_red:   Optional[ConexionRed] = None
    cargas_aislado: list[CargaItem] = []
    tipo_techo:     Optional[TipoTecho] = None
    obs_techo:      Optional[str] = None
    obs_interior:   Optional[str] = None
    notas:          Optional[str] = None
    paso_actual:    Optional[PasoActual] = "inicio"

class VisitaListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:             int
    tipo_cliente:   Optional[TipoCliente] = None
    tipo_sistema:   Optional[TipoSistema] = None
    tecnico_id:     Optional[int] = None
    paso_actual:    Optional[PasoActual] = None
    pdf_url:        Optional[str] = None
    estado:         Optional[EstadoVisita] = None
    fecha:          datetime
    cliente:        DatosClienteOut

class VisitaOut(VisitaCreate):
    model_config = ConfigDict(from_attributes=True)
    id:             int
    fotos_techo:    list[FotoItem] = []
    fotos_interior: list[FotoItem] = []
    recibo_ruta:    Optional[str] = None
    pdf_url:        Optional[str] = None
    estado:         EstadoVisita
    paso_actual:    Optional[PasoActual] = None
    fecha:          datetime
    cliente:        DatosClienteOut
    tecnico:        Optional[UsuarioOut] = None
