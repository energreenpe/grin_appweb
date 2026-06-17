from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.db import get_db
from app.modules.quote import schemas, service
from app.modules.quote.pdf import generar_pdf_cotizacion
from app import storage
from app.images import to_webp, ImageError, MAX_BYTES

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════
# PRODUCTOS
# ═══════════════════════════════════════════════════════════════════

@router.get("/products", response_model=list[schemas.ProductoOut])
def list_products(
    search:    Optional[str] = None,
    categoria: Optional[str] = None,
    skip:      int = 0,
    limit:     int = 100,
    db: Session = Depends(get_db),
):
    """Lista productos activos con filtros opcionales."""
    return service.get_productos(db, search=search, categoria=categoria, skip=skip, limit=limit)


@router.get("/products/{producto_id}", response_model=schemas.ProductoOut)
def get_product(producto_id: int, db: Session = Depends(get_db)):
    prod = service.get_producto(db, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return prod




@router.post("/products", response_model=schemas.ProductoOut, status_code=status.HTTP_201_CREATED)
def create_product(data: schemas.ProductoCreate, db: Session = Depends(get_db)):
    return service.create_producto(db, data)


@router.put("/products/{producto_id}", response_model=schemas.ProductoOut)
def update_product(producto_id: int, data: schemas.ProductoUpdate, db: Session = Depends(get_db)):
    prod = service.update_producto(db, producto_id, data)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return prod


@router.delete("/products/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(producto_id: int, db: Session = Depends(get_db)):
    ok = service.delete_producto(db, producto_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Producto no encontrado")



# ═══════════════════════════════════════════════════════════════════
# COTIZACIONES
# ═══════════════════════════════════════════════════════════════════

@router.get("/cotizaciones", response_model=list[schemas.CotizacionListItem])
def list_cotizaciones(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return service.get_cotizaciones(db, skip=skip, limit=limit)


@router.get("/cotizaciones/{cotizacion_id}", response_model=schemas.CotizacionOut)
def get_cotizacion(cotizacion_id: int, db: Session = Depends(get_db)):
    cot = service.get_cotizacion(db, cotizacion_id)
    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    totales = service.calcular_totales(cot.items, cot)
    # Construir response con totales
    out = schemas.CotizacionOut.model_validate(cot)
    out.totales = totales
    out.items = [schemas.ItemOut.from_orm_item(i) for i in cot.items]
    return out


@router.post("/cotizaciones", response_model=schemas.CotizacionOut, status_code=status.HTTP_201_CREATED)
def create_cotizacion(data: schemas.CotizacionCreate, db: Session = Depends(get_db)):
    cot = service.create_cotizacion(db, data)
    out = schemas.CotizacionOut.model_validate(cot)
    out.totales = service.calcular_totales([], cot)
    out.items = []
    return out


@router.put("/cotizaciones/{cotizacion_id}", response_model=schemas.CotizacionOut)
def update_cotizacion(
    cotizacion_id: int,
    data: schemas.CotizacionUpdate,
    db: Session = Depends(get_db),
):
    cot = service.update_cotizacion(db, cotizacion_id, data)
    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    out = schemas.CotizacionOut.model_validate(cot)
    out.totales = service.calcular_totales(cot.items, cot)
    out.items = [schemas.ItemOut.from_orm_item(i) for i in cot.items]
    return out


@router.delete("/cotizaciones/{cotizacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cotizacion(cotizacion_id: int, db: Session = Depends(get_db)):
    ok = service.delete_cotizacion(db, cotizacion_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")


@router.put("/cotizaciones/{cotizacion_id}/estado", response_model=schemas.CotizacionOut)
def change_estado(cotizacion_id: int, data: schemas.EstadoUpdate, db: Session = Depends(get_db)):
    """Cambia el estado validando la transición (borrador → enviada/aprobada,
    enviada → aprobada/rechazada, aprobada → rechazada)."""
    cot = service.change_estado(db, cotizacion_id, data.estado)
    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    out = schemas.CotizacionOut.model_validate(cot)
    out.totales = service.calcular_totales(cot.items, cot)
    out.items = [schemas.ItemOut.from_orm_item(i) for i in cot.items]
    return out


@router.post("/cotizaciones/{cotizacion_id}/duplicar",
             response_model=schemas.CotizacionOut, status_code=status.HTTP_201_CREATED)
def duplicar_cotizacion(cotizacion_id: int, db: Session = Depends(get_db)):
    """Clona la cotización como nuevo borrador (sin correlativo), usándola como plantilla."""
    nueva = service.duplicar_cotizacion(db, cotizacion_id)
    if not nueva:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    out = schemas.CotizacionOut.model_validate(nueva)
    out.totales = service.calcular_totales(nueva.items, nueva)
    out.items = [schemas.ItemOut.from_orm_item(i) for i in nueva.items]
    return out


# ── ÍTEMS ─────────────────────────────────────────────────────────────────────

@router.post(
    "/cotizaciones/{cotizacion_id}/items",
    response_model=schemas.ItemOut,
    status_code=status.HTTP_201_CREATED,
)
def add_item(cotizacion_id: int, data: schemas.ItemCreate, db: Session = Depends(get_db)):
    item = service.add_item(db, cotizacion_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    return schemas.ItemOut.from_orm_item(item)

@router.put("/cotizaciones/{cotizacion_id}/items/reorder", response_model=schemas.CotizacionOut)
def reorder_items(cotizacion_id: int, req: schemas.ReorderItemsReq, db: Session = Depends(get_db)):
    service.reorder_items(db, cotizacion_id, req.item_ids)
    cot = service.get_cotizacion(db, cotizacion_id)
    out = schemas.CotizacionOut.model_validate(cot)
    out.totales = service.calcular_totales(cot.items, cot)
    out.items = [schemas.ItemOut.from_orm_item(i) for i in cot.items]
    return out


@router.put(
    "/cotizaciones/{cotizacion_id}/items/{item_id}",
    response_model=schemas.CotizacionOut,
)
def update_item(
    cotizacion_id: int,
    item_id: int,
    data: schemas.ItemUpdate,
    db: Session = Depends(get_db),
):
    item = service.update_item(db, cotizacion_id, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    # Devuelve la cotización completa (con totales) para que el frontend no necesite
    # una recarga aparte tras cada edición.
    cot = service.get_cotizacion(db, cotizacion_id)
    out = schemas.CotizacionOut.model_validate(cot)
    out.totales = service.calcular_totales(cot.items, cot)
    out.items = [schemas.ItemOut.from_orm_item(i) for i in cot.items]
    return out


@router.delete(
    "/cotizaciones/{cotizacion_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item(cotizacion_id: int, item_id: int, db: Session = Depends(get_db)):
    ok = service.delete_item(db, cotizacion_id, item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")


# ── PDF ───────────────────────────────────────────────────────────────────────

@router.get("/cotizaciones/{cotizacion_id}/pdf")
def download_pdf(cotizacion_id: int, db: Session = Depends(get_db)):
    """Genera y descarga el PDF. Si está en borrador, lo marca como Enviada
    (asignando su correlativo) automáticamente antes de generar."""
    cot = service.get_cotizacion(db, cotizacion_id)
    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    # Al generar el PDF de un borrador, pasa a "enviada" y obtiene su número.
    if cot.estado == "borrador":
        cot = service.change_estado(db, cotizacion_id, "enviada")

    # Guardar/actualizar el cliente recién ahora (cliente nuevo -> se crea;
    # existente -> se actualiza por RUC/DNI o nombre). Best-effort.
    service.upsert_cliente_from_cotizacion(db, cot)

    empresa = service.get_empresa(db)
    pdf_bytes = generar_pdf_cotizacion(cot, cot.items, empresa)

    filename = f"{cot.correlativo}_{cot.cliente_nombre.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ═══════════════════════════════════════════════════════════════════
# EMPRESA
# ═══════════════════════════════════════════════════════════════════

@router.get("/empresa", response_model=schemas.EmpresaOut)
def get_empresa(db: Session = Depends(get_db)):
    return service.get_empresa(db)


@router.put("/empresa", response_model=schemas.EmpresaOut)
def update_empresa(data: schemas.EmpresaUpdate, db: Session = Depends(get_db)):
    return service.update_empresa(db, data.model_dump(exclude_unset=True))


@router.post("/empresa/logo")
def upload_logo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Sube el logo de la empresa: lo convierte a WEBP, lo guarda en uploads/ y
    REEMPLAZA el anterior (lo borra). Guarda la ruta relativa en la BD."""
    # Lectura acotada: nunca carga más de 2 MB en memoria (rechazo temprano).
    raw = file.file.read(MAX_BYTES + 1)
    try:
        webp = to_webp(raw)
    except ImageError as e:
        raise HTTPException(status_code=400, detail=str(e))

    empresa = service.get_empresa(db)
    storage.delete(empresa.logo_path)          # reemplazo: borra el anterior
    rel = storage.save_bytes(webp, "empresa", f"logo_{uuid.uuid4().hex}.webp")
    service.update_empresa(db, {"logo_path": rel})
    return {"status": "ok", "path": rel}


@router.post("/banks/logo")
def upload_bank_logo(file: UploadFile = File(...)):
    """Sube el logo de un banco: lo convierte a WEBP, lo guarda en uploads/banks/
    con nombre UUID y devuelve la URL relativa. No autoborra (los logos de banco
    son snapshot por cotización; borrarlos rompería PDFs históricos)."""
    # Lectura acotada: nunca carga más de 2 MB en memoria (rechazo temprano).
    raw = file.file.read(MAX_BYTES + 1)
    try:
        webp = to_webp(raw)
    except ImageError as e:
        raise HTTPException(status_code=400, detail=str(e))

    rel = storage.save_bytes(webp, "banks", f"{uuid.uuid4().hex}.webp")
    return {"url": rel}


# ═══════════════════════════════════════════════════════════════════
# USUARIOS / VENDEDORES
# ═══════════════════════════════════════════════════════════════════

@router.get("/vendedores", response_model=list[schemas.UsuarioOut])
def get_vendedores(db: Session = Depends(get_db)):
    return service.get_vendedores(db)


# ═══════════════════════════════════════════════════════════════════
# CLIENTES
# ═══════════════════════════════════════════════════════════════════

@router.get("/clientes", response_model=list[schemas.DatosClienteOut])
def get_clientes(search: Optional[str] = None, db: Session = Depends(get_db)):
    return service.get_clientes(db, search)

@router.post("/clientes", response_model=schemas.DatosClienteOut)
def create_cliente(data: schemas.DatosClienteCreate, db: Session = Depends(get_db)):
    return service.create_cliente(db, data)

# ═══════════════════════════════════════════════════════════════════
# PLANTILLAS GLOBALES
# ═══════════════════════════════════════════════════════════════════

@router.get("/plantillas", response_model=schemas.PlantillasGlobalesOut)
def get_plantillas(db: Session = Depends(get_db)):
    return service.get_plantillas_globales(db)

@router.put("/plantillas", response_model=schemas.PlantillasGlobalesOut)
def update_plantillas(data: schemas.PlantillasGlobalesUpdate, db: Session = Depends(get_db)):
    return service.update_plantillas_globales(db, data)
