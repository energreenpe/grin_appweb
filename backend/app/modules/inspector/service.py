import os
from io import BytesIO
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from PIL import Image
from PIL.Image import DecompressionBombError
from app.modules.inspector.models import Visita
from app.modules.inspector.schemas import VisitaCreate, FotoItem
from app.modules.inspector.pdf import generar_pdf_visita
from app.modules.shared.models import EmpresaConfig

UPLOAD_DIR = "uploads/inspector"
MAX_FILE_BYTES = 10 * 1024 * 1024          # 10 MB por archivo
MAX_FOTOS_POR_SECCION = 6                  # tope de fotos para techo e interior
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic", ".heif"}
Image.MAX_IMAGE_PIXELS = 64_000_000        # ~64 MP: descarta imágenes "decompression bomb"

def listar_visitas(db: Session, tipo_cliente: str = None, tipo_sistema: str = None, estado: str = None, skip: int = 0, limit: int = 50):
    # joinedload evita el N+1: VisitaListItem serializa `cliente` por cada fila
    query = db.query(Visita).options(joinedload(Visita.cliente))
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
    try:
        db.commit()
    except IntegrityError:
        # FK inválida: cliente_id inexistente o técnico inexistente
        db.rollback()
        raise HTTPException(status_code=400, detail="Cliente o técnico inválido: el registro referenciado no existe.")
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

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cliente o técnico inválido: el registro referenciado no existe.")
    db.refresh(visita)
    return visita

def _sanitizar_stem(filename: str | None) -> str:
    """Devuelve un nombre base seguro (sin rutas ni caracteres raros) para evitar path traversal."""
    stem = Path(filename or "foto").stem          # Path().stem descarta cualquier componente de directorio
    limpio = "".join(c for c in stem if c.isalnum() or c in ("-", "_"))
    return limpio or "foto"


async def guardar_archivo(file: UploadFile, subfolder: str) -> FotoItem:
    # 1. Validar que realmente sea una imagen
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen.")

    # 2. Leer en chunks acotando memoria y rechazando si supera el máximo
    contents = bytearray()
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        contents.extend(chunk)
        if len(contents) > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"La imagen supera el tamaño máximo de {MAX_FILE_BYTES // (1024 * 1024)} MB.",
            )
    contents = bytes(contents)
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")

    # 3. Nombre saneado (cierra el path traversal del filename del cliente)
    os.makedirs(f"{UPLOAD_DIR}/{subfolder}", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_stem = _sanitizar_stem(file.filename)
    filename = f"{timestamp}_{safe_stem}.webp"
    filepath = f"{UPLOAD_DIR}/{subfolder}/{filename}"

    # 4. Convertir a WebP con guardia anti decompression bomb
    try:
        image = Image.open(BytesIO(contents))
        # WebP soporta RGBA, si tiene paleta lo convertimos
        if image.mode == 'P':
            image = image.convert('RGBA')
        image.save(filepath, "WEBP", quality=80)
    except DecompressionBombError:
        raise HTTPException(status_code=400, detail="La imagen es demasiado grande para procesarla.")
    except Exception as e:
        # Fallback: guardar el original solo si la extensión es de imagen conocida (p. ej. HEIC sin plugin)
        print(f"Error convirtiendo a WebP: {e}")
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Formato de imagen no soportado.")
        filename = f"{timestamp}_{safe_stem}{suffix}"
        filepath = f"{UPLOAD_DIR}/{subfolder}/{filename}"
        with open(filepath, "wb") as buffer:
            buffer.write(contents)

    return FotoItem(
        url=f"/{filepath}",
        nombre=filename,
        subida_en=datetime.now()
    )

def verificar_limite_fotos(db: Session, visita_id: int, seccion: str):
    """Rechaza la subida si la sección ya alcanzó el máximo. Se llama ANTES de
    guardar el archivo para no dejar archivos huérfanos en disco."""
    visita = obtener_visita(db, visita_id)
    actuales = visita.fotos_techo if seccion == "techo" else visita.fotos_interior
    if len(actuales or []) >= MAX_FOTOS_POR_SECCION:
        raise HTTPException(
            status_code=409,
            detail=f"Solo se permiten hasta {MAX_FOTOS_POR_SECCION} fotos en esta sección.",
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

def _borrar_archivo_fisico(url: str | None) -> None:
    """Elimina el archivo físico asociado a una URL '/uploads/...'. Tolera ausencia o errores de IO."""
    if not url or not url.startswith("/"):
        return
    path = url.lstrip("/")
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as e:
        print(f"No se pudo eliminar el archivo {path}: {e}")

def actualizar_recibo(db: Session, visita_id: int, recibo_url: str):
    visita = obtener_visita(db, visita_id)

    # Eliminar archivo físico anterior si existe
    _borrar_archivo_fisico(visita.recibo_ruta)

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
        _borrar_archivo_fisico(foto_eliminada['url'])

    db.commit()
    db.refresh(visita)
    return visita

def _generar_y_guardar_pdf(db: Session, visita: Visita) -> None:
    """Genera el PDF de la visita y lo guarda en disco, poblando pdf_url.
    Best-effort: si la generación falla, no interrumpe el completado (el endpoint
    de descarga puede regenerarlo al vuelo)."""
    try:
        empresa = db.query(EmpresaConfig).first()
        pdf_bytes = generar_pdf_visita(visita, empresa)
        os.makedirs(f"{UPLOAD_DIR}/pdfs", exist_ok=True)
        filepath = f"{UPLOAD_DIR}/pdfs/Visita_{visita.id}.pdf"
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)
        visita.pdf_url = f"/{filepath}"
    except Exception as e:
        print(f"No se pudo generar/guardar el PDF de la visita {visita.id}: {e}")

def completar_visita(db: Session, visita_id: int):
    visita = obtener_visita(db, visita_id)
    visita.estado = "completada"
    _generar_y_guardar_pdf(db, visita)   # best-effort: setea pdf_url si tiene éxito
    db.commit()
    db.refresh(visita)
    return visita

def cancelar_visita(db: Session, visita_id: int):
    visita = obtener_visita(db, visita_id)

    # 1. Eliminar archivos físicos asociados (recibo + fotos)
    _borrar_archivo_fisico(visita.recibo_ruta)
    for f in [*visita.fotos_techo, *visita.fotos_interior]:
        if isinstance(f, dict):
            _borrar_archivo_fisico(f.get('url'))

    # 2. Eliminar el registro
    db.delete(visita)
    db.commit()
    return {"message": "Visita cancelada y recursos liberados"}
