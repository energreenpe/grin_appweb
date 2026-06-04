from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db import get_db
from app.modules.inspector import schemas, service
from app.modules.inspector.pdf import generar_pdf_visita
from app.modules.quote.models import DatosCliente, EmpresaConfig, Usuario
from app.modules.quote.schemas import DatosClienteOut, DatosClienteCreate, UsuarioOut
from app.modules.quote.service import create_cliente

router = APIRouter()

@router.get("/visitas", response_model=List[schemas.VisitaListItem])
def listar_visitas(
    tipo_cliente: Optional[str] = None,
    tipo_sistema: Optional[str] = None,
    estado: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return service.listar_visitas(db, tipo_cliente=tipo_cliente, tipo_sistema=tipo_sistema, estado=estado, skip=skip, limit=limit)

@router.post("/visitas", response_model=schemas.VisitaOut)
def crear_visita(visita: schemas.VisitaCreate, db: Session = Depends(get_db)):
    return service.crear_visita(db, visita)

@router.put("/visitas/{visita_id}", response_model=schemas.VisitaOut)
def actualizar_visita(visita_id: int, visita: schemas.VisitaCreate, db: Session = Depends(get_db)):
    return service.actualizar_visita(db, visita_id, visita)

@router.get("/visitas/{visita_id}", response_model=schemas.VisitaOut)
def obtener_visita(visita_id: int, db: Session = Depends(get_db)):
    return service.obtener_visita(db, visita_id)

@router.post("/visitas/{visita_id}/completar", response_model=schemas.VisitaOut)
def completar_visita(visita_id: int, db: Session = Depends(get_db)):
    return service.completar_visita(db, visita_id)

@router.delete("/visitas/{visita_id}")
def cancelar_visita(visita_id: int, db: Session = Depends(get_db)):
    return service.cancelar_visita(db, visita_id)

@router.post("/visitas/{visita_id}/fotos-techo", response_model=schemas.VisitaOut)
async def upload_foto_techo(visita_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    foto = await service.guardar_archivo(file, "fotos")
    return service.actualizar_fotos(db, visita_id, foto, "techo")

@router.post("/visitas/{visita_id}/fotos-interior", response_model=schemas.VisitaOut)
async def upload_foto_interior(visita_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    foto = await service.guardar_archivo(file, "fotos")
    return service.actualizar_fotos(db, visita_id, foto, "interior")

@router.post("/visitas/{visita_id}/recibo", response_model=schemas.VisitaOut)
async def upload_recibo(visita_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    foto = await service.guardar_archivo(file, "recibos")
    return service.actualizar_recibo(db, visita_id, foto.url)

@router.delete("/visitas/{visita_id}/fotos-techo/{index}", response_model=schemas.VisitaOut)
def delete_foto_techo(visita_id: int, index: int, db: Session = Depends(get_db)):
    return service.eliminar_foto(db, visita_id, "techo", index)

@router.delete("/visitas/{visita_id}/fotos-interior/{index}", response_model=schemas.VisitaOut)
def delete_foto_interior(visita_id: int, index: int, db: Session = Depends(get_db)):
    return service.eliminar_foto(db, visita_id, "interior", index)

@router.get("/tecnicos", response_model=List[UsuarioOut])
def get_tecnicos(db: Session = Depends(get_db)):
    return db.query(Usuario).filter(Usuario.rol == "tecnico", Usuario.activo == True).all()

@router.get("/clientes/search", response_model=List[DatosClienteOut])
def search_clientes(q: str, db: Session = Depends(get_db)):
    query = db.query(DatosCliente).filter(
        or_(
            DatosCliente.nombre.ilike(f"%{q}%"),
            DatosCliente.documento.ilike(f"%{q}%")
        )
    ).limit(10).all()
    return query

@router.post("/clientes", response_model=DatosClienteOut)
def crear_nuevo_cliente(cliente: DatosClienteCreate, db: Session = Depends(get_db)):
    return create_cliente(db, cliente)

@router.get("/visitas/{visita_id}/pdf")
def descargar_pdf(visita_id: int, db: Session = Depends(get_db)):
    visita = service.obtener_visita(db, visita_id)
    empresa = db.query(EmpresaConfig).first()
    
    pdf_bytes = generar_pdf_visita(visita, empresa)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Visita_{visita_id}.pdf"'}
    )



