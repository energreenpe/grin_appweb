"""
Lógica transversal de Clientes (búsqueda y upsert con deduplicación por RUC/DNI
o nombre). Compartida por quote (que la re-exporta) e inspector.
"""
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.modules.shared.models import DatosCliente
from app.modules.shared.schemas import DatosClienteCreate


def get_clientes(db: Session, search: Optional[str] = None) -> list[DatosCliente]:
    q = db.query(DatosCliente)
    if search:
        s = f"%{search.lower()}%"
        q = q.filter(DatosCliente.nombre.ilike(s) | DatosCliente.documento.ilike(s))
    return q.limit(50).all()


def _match_cliente(db: Session, nombre: str, documento: Optional[str]) -> Optional[DatosCliente]:
    """Identifica un cliente por RUC/DNI (identificador fuerte) y, si no, por nombre.
    Permite corregir el nombre (lo ancla el RUC) o corregir el RUC (lo ancla el nombre)
    sin duplicar el registro."""
    if documento:
        c = db.query(DatosCliente).filter(DatosCliente.documento == documento).first()
        if c:
            return c
    if nombre:
        return db.query(DatosCliente).filter(DatosCliente.nombre == nombre).first()
    return None


def upsert_cliente(
    db: Session, *, nombre: str, documento: Optional[str] = None,
    direccion: Optional[str] = None, atencion: Optional[str] = None,
    referencia: Optional[str] = None, correo: Optional[str] = None,
    telefono: Optional[str] = None,
) -> Optional[DatosCliente]:
    """Crea o actualiza un cliente emparejando por RUC/DNI o nombre. Devuelve None
    si no hay ni nombre ni documento. Puede lanzar IntegrityError (lo maneja el caller)."""
    nombre = (nombre or "").strip()
    documento = (documento or "").strip() or None   # vacío -> NULL
    if not nombre and not documento:
        return None

    campos = dict(nombre=nombre, documento=documento, direccion=direccion,
                  atencion=atencion, referencia=referencia, correo=correo, telefono=telefono)
    cliente = _match_cliente(db, nombre, documento)
    if cliente:
        for field, value in campos.items():
            setattr(cliente, field, value)
    else:
        cliente = DatosCliente(**campos)
        db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def create_cliente(db: Session, data: DatosClienteCreate) -> DatosCliente:
    """Upsert de cliente desde la API. Mapea choques de unicidad a un error claro."""
    try:
        cliente = upsert_cliente(
            db, nombre=data.nombre, documento=data.documento, direccion=data.direccion,
            atencion=data.atencion, referencia=data.referencia, correo=data.correo,
            telefono=data.telefono,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe otro cliente con ese nombre o RUC/DNI.")
    if cliente is None:
        raise HTTPException(status_code=400, detail="Debe indicar al menos el nombre o el RUC/DNI del cliente.")
    return cliente
