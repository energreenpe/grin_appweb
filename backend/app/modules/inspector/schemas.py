from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.modules.quote.schemas import DatosClienteOut

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
    tipo_cliente:   str
    tecnico_id:     Optional[int] = None
    lat:            Optional[float] = None
    lng:            Optional[float] = None
    tipo_sistema:   Optional[str] = None
    conexion_red:   Optional[str] = None
    cargas_aislado: list[CargaItem] = []
    tipo_techo:     Optional[str] = None
    obs_techo:      Optional[str] = None
    obs_interior:   Optional[str] = None
    notas:          Optional[str] = None
    paso_actual:    Optional[str] = "inicio"

class VisitaListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:             int
    tipo_cliente:   Optional[str] = None
    tipo_sistema:   Optional[str] = None
    tecnico_id:     Optional[int] = None
    paso_actual:    Optional[str] = None
    pdf_url:        Optional[str] = None
    estado:         Optional[str] = None
    fecha:          datetime
    cliente:        DatosClienteOut

class VisitaOut(VisitaCreate):
    model_config = ConfigDict(from_attributes=True)
    id:             int
    fotos_techo:    list[FotoItem] = []
    fotos_interior: list[FotoItem] = []
    recibo_ruta:    Optional[str] = None
    pdf_url:        Optional[str] = None
    estado:         str
    paso_actual:    Optional[str] = None
    fecha:          datetime
    cliente:        DatosClienteOut
