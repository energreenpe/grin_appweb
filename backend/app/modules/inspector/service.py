import os
import shutil
from datetime import datetime
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.modules.inspector.models import Visita
from app.modules.inspector.schemas import VisitaCreate, FotoItem
from sqlalchemy import desc

UPLOAD_DIR = "uploads/inspector"

def listar_visitas(db: Session, tipo_cliente: str = None, tipo_sistema: str = None, estado: str = None, skip: int = 0, limit: int = 50):
    query = db.query(Visita)
    if tipo_cliente:
        query = query.filter(Visita.tipo_cliente == tipo_cliente)
    if tipo_sistema:
        query = query.filter(Visita.tipo_sistema == tipo_sistema)
    if estado:
        query = query.filter(Visita.estado == estado)
    return query.order_by(desc(Visita.fecha)).offset(skip).limit(limit).all()

def obtener_visita(db: Session, visita_id: int):
    visita = db.query(Visita).filter(Visita.id == visita_id).first()
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    return visita

def crear_visita(db: Session, data: VisitaCreate):
    visita_dict = data.model_dump()
    # Convertir Pydantic BaseModel en dict para la base de datos
    cargas = visita_dict.pop("cargas_aislado", [])
    visita_dict["cargas_aislado"] = [c for c in cargas]
    
    db_visita = Visita(**visita_dict)
    db.add(db_visita)
    db.commit()
    db.refresh(db_visita)
    return db_visita

def actualizar_visita(db: Session, visita_id: int, data: VisitaCreate):
    visita = obtener_visita(db, visita_id)
    visita_dict = data.model_dump(exclude_unset=True)
    cargas = visita_dict.pop("cargas_aislado", None)
    if cargas is not None:
        visita.cargas_aislado = [c for c in cargas]
    
    for key, value in visita_dict.items():
        setattr(visita, key, value)
        
    db.commit()
    db.refresh(visita)
    return visita

async def guardar_archivo(file: UploadFile, subfolder: str) -> FotoItem:
    os.makedirs(f"{UPLOAD_DIR}/{subfolder}", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base_name = os.path.splitext(file.filename)[0]
    filename = f"{timestamp}_{base_name}.webp"
    filepath = f"{UPLOAD_DIR}/{subfolder}/{filename}"
    
    try:
        from PIL import Image
        image = Image.open(file.file)
        # WebP soporta RGBA, si tiene paleta lo convertimos
        if image.mode == 'P':
            image = image.convert('RGBA')
        image.save(filepath, "WEBP", quality=80)
    except Exception as e:
        print(f"Error convirtiendo a WebP: {e}")
        # Fallback si falla
        file.file.seek(0)
        filename = f"{timestamp}_{file.filename}"
        filepath = f"{UPLOAD_DIR}/{subfolder}/{filename}"
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
    return FotoItem(
        url=f"/{filepath}",
        nombre=filename,
        subida_en=datetime.now()
    )

def actualizar_fotos(db: Session, visita_id: int, foto: FotoItem, seccion: str):
    visita = obtener_visita(db, visita_id)
    # Clonamos la lista para que SQLAlchemy detecte el cambio en JSON
    if seccion == "techo":
        fotos = list(visita.fotos_techo)
        fotos.append(foto.model_dump(mode="json"))
        visita.fotos_techo = fotos
    elif seccion == "interior":
        fotos = list(visita.fotos_interior)
        fotos.append(foto.model_dump(mode="json"))
        visita.fotos_interior = fotos
    
    db.commit()
    db.refresh(visita)
    return visita

def actualizar_recibo(db: Session, visita_id: int, recibo_url: str):
    visita = obtener_visita(db, visita_id)
    
    # Eliminar archivo físico anterior si existe
    if visita.recibo_ruta and visita.recibo_ruta.startswith("/"):
        old_path = visita.recibo_ruta.lstrip("/")
        if os.path.exists(old_path):
            os.remove(old_path)
            
    visita.recibo_ruta = recibo_url
    db.commit()
    db.refresh(visita)
    return visita

def eliminar_foto(db: Session, visita_id: int, seccion: str, index: int):
    visita = obtener_visita(db, visita_id)
    foto_eliminada = None
    if seccion == "techo":
        fotos = list(visita.fotos_techo)
        if 0 <= index < len(fotos):
            foto_eliminada = fotos.pop(index)
            visita.fotos_techo = fotos
    elif seccion == "interior":
        fotos = list(visita.fotos_interior)
        if 0 <= index < len(fotos):
            foto_eliminada = fotos.pop(index)
            visita.fotos_interior = fotos
            
    if foto_eliminada and 'url' in foto_eliminada:
        path = foto_eliminada['url'].lstrip("/")
        if os.path.exists(path):
            os.remove(path)
            
            
    db.commit()
    db.refresh(visita)
    return visita

def completar_visita(db: Session, visita_id: int):
    visita = obtener_visita(db, visita_id)
    visita.estado = "completada"
    db.commit()
    db.refresh(visita)
    return visita

def cancelar_visita(db: Session, visita_id: int):
    visita = obtener_visita(db, visita_id)
    
    # 1. Eliminar recibo
    if visita.recibo_ruta and visita.recibo_ruta.startswith("/"):
        old_path = visita.recibo_ruta.lstrip("/")
        if os.path.exists(old_path):
            try: os.remove(old_path)
            except: pass
            
    # 2. Eliminar fotos techo
    for f in visita.fotos_techo:
        if isinstance(f, dict) and 'url' in f:
            path = f['url'].lstrip("/")
            if os.path.exists(path):
                try: os.remove(path)
                except: pass

    # 3. Eliminar fotos interior
    for f in visita.fotos_interior:
        if isinstance(f, dict) and 'url' in f:
            path = f['url'].lstrip("/")
            if os.path.exists(path):
                try: os.remove(path)
                except: pass

    # 4. Eliminar el registro
    db.delete(visita)
    db.commit()
    return {"message": "Visita cancelada y recursos liberados"}
