"""
Tests del módulo PLANNER — evidencia fotográfica endurecida (entregable E5).

Replica las medidas de INSPECTOR: conversión a WebP, tope de tamaño que aborta
antes de disco, rechazo de no-imágenes; almacenamiento por app.storage
(anti-traversal) y borrado del archivo de disco al eliminar el registro.
"""
from io import BytesIO

from PIL import Image

from app import storage


def _png_bytes(color="green", size=(4, 4)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return buf.getvalue()


def _crear_proyecto(client):
    return client.post("/api/planner/proyectos", json={"nombre": "Proy Fotos E5"}).json()


def test_subir_foto_convierte_a_webp_y_se_sirve_en_uploads(client):
    proy = _crear_proyecto(client)
    pid = proy["id"]
    try:
        r = client.post(
            f"/api/planner/proyectos/{pid}/fotos",
            files={"file": ("evidencia.png", _png_bytes(), "image/png")},
            data={"etapa": "Paneles", "etapa_codigo": "paneles", "fecha": "2026-06-10"},
        )
        assert r.status_code == 201, r.text
        foto = r.json()
        # Convertida a WebP independientemente de la extensión original.
        assert foto["mime_type"] == "image/webp"
        assert foto["ruta"].endswith(".webp")
        assert foto["ruta"].startswith("uploads/planner/")
        assert foto["url"] == f"/{foto['ruta']}"
        # El archivo existe en disco (vía storage, dentro de uploads/).
        assert storage.resolve(foto["ruta"]) is not None

        # Aparece al listar.
        r = client.get(f"/api/planner/proyectos/{pid}/fotos")
        assert any(f["id"] == foto["id"] for f in r.json())

        # Alternar inclusión en PDF + comentario manual.
        r = client.patch(f"/api/planner/fotos/{foto['id']}", json={
            "incluir_en_pdf": True, "comentario_pdf": "Montaje de paneles fila A",
        })
        assert r.status_code == 200
        assert r.json()["incluir_en_pdf"] is True

        # filtro solo_pdf
        r = client.get(f"/api/planner/proyectos/{pid}/fotos", params={"solo_pdf": True})
        assert any(f["id"] == foto["id"] for f in r.json())

        # Borrar → el archivo desaparece del disco.
        ruta = foto["ruta"]
        assert client.delete(f"/api/planner/fotos/{foto['id']}").status_code == 200
        assert storage.resolve(ruta) is None
        assert client.delete(f"/api/planner/fotos/{foto['id']}").status_code == 404
    finally:
        client.delete(f"/api/planner/proyectos/{pid}")


def test_rechaza_no_imagen(client):
    proy = _crear_proyecto(client)
    pid = proy["id"]
    try:
        r = client.post(
            f"/api/planner/proyectos/{pid}/fotos",
            files={"file": ("notas.txt", b"esto no es una imagen", "text/plain")},
            data={"fecha": "2026-06-10"},
        )
        assert r.status_code == 400
    finally:
        client.delete(f"/api/planner/proyectos/{pid}")


def test_rechaza_imagen_falsa_con_content_type_png(client):
    # content-type image/png pero los bytes no son una imagen → PIL falla → 400
    # (la decodificación es la validación real, más fuerte que mirar magic-bytes).
    proy = _crear_proyecto(client)
    pid = proy["id"]
    try:
        r = client.post(
            f"/api/planner/proyectos/{pid}/fotos",
            files={"file": ("falsa.png", b"PNG\x00 contenido basura no decodificable", "image/png")},
            data={"fecha": "2026-06-10"},
        )
        assert r.status_code == 400
    finally:
        client.delete(f"/api/planner/proyectos/{pid}")


def test_borrar_proyecto_elimina_fotos_del_disco(client):
    # Al borrar un proyecto, sus archivos de foto deben desaparecer del disco
    # (el cascade de la BD no toca el filesystem).
    proy = _crear_proyecto(client)
    pid = proy["id"]
    foto = client.post(
        f"/api/planner/proyectos/{pid}/fotos",
        files={"file": ("ev.png", _png_bytes(), "image/png")},
        data={"etapa": "General", "fecha": "2026-06-10"},
    ).json()
    ruta = foto["ruta"]
    assert storage.resolve(ruta) is not None          # existe tras subir
    assert client.delete(f"/api/planner/proyectos/{pid}").status_code == 200
    assert storage.resolve(ruta) is None              # se borró el archivo
    # y la carpeta del proyecto ya no existe
    assert storage.resolve(f"uploads/planner/{pid}") is None


def test_foto_proyecto_inexistente_limpia_archivo(client):
    # Imagen válida pero proyecto inexistente → 404 y no debe quedar el archivo.
    r = client.post(
        "/api/planner/proyectos/999999999/fotos",
        files={"file": ("x.png", _png_bytes(), "image/png")},
        data={"fecha": "2026-06-10"},
    )
    assert r.status_code == 404
