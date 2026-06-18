"""
Schemas Pydantic de las entidades transversales (Cliente, Usuario, Empresa).
quote los re-exporta desde su propio schemas.py por compatibilidad.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ─── USUARIO ──────────────────────────────────────────────────────────────────

class UsuarioBase(BaseModel):
    nombre:   str
    correo:   str
    telefono: Optional[str] = None
    rol:      Optional[str] = "vendedor"


class UsuarioCreate(UsuarioBase):
    pass


class UsuarioOut(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    activo:     bool
    created_at: datetime


# ─── CLIENTE ──────────────────────────────────────────────────────────────────

class DatosClienteBase(BaseModel):
    nombre:      str
    documento:   Optional[str] = None
    direccion:   Optional[str] = None
    atencion:    Optional[str] = None
    referencia:  Optional[str] = None
    correo:      Optional[str] = None
    telefono:    Optional[str] = None


class DatosClienteCreate(DatosClienteBase):
    pass


class DatosClienteOut(DatosClienteBase):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    created_at: datetime


# ─── EMPRESA ──────────────────────────────────────────────────────────────────

class EmpresaBase(BaseModel):
    nombre:    str = "Energreen Perú E.I.R.L."
    ruc:       Optional[str] = "20604756821"
    direccion: Optional[str] = None
    telefono:  Optional[str] = None
    email:     Optional[str] = None
    logo_path: Optional[str] = None


class EmpresaUpdate(EmpresaBase):
    nombre: Optional[str] = None


class EmpresaOut(EmpresaBase):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    updated_at: datetime
