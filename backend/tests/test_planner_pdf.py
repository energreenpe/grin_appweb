"""
Tests del módulo PLANNER — reportes PDF Cliente/Oficina (entregable E6).

Verifican que ambos PDF se generan (200 + cuerpo %PDF), con proyecto que tiene
actividades, asistencia y una foto real (webp). Los PDF se generan a un BytesIO
en memoria → no quedan archivos temporales en disco.
"""
from io import BytesIO

from PIL import Image


def _png_bytes(color="green", size=(8, 8)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return buf.getvalue()


def _proyecto_completo(client):
    """Crea un proyecto con actividad, persona+asistencia y una foto."""
    proy = client.post("/api/planner/proyectos", json={
        "nombre": "Obra PDF E6", "cliente": "Cliente PDF", "region": "Piura",
        "ubicacion": "Av. Solar 123", "paneles": 24,
        "fecha_inicio": "2026-06-01", "fecha_fin": "2026-06-30",
        "alcance": "Instalación fotovoltaica de prueba.",
    }).json()
    pid = proy["id"]
    persona = client.post("/api/planner/personal", json={"nombre": "Operario PDF"}).json()
    act = client.post("/api/planner/actividades", json={
        "proyecto_id": pid, "titulo": "Montaje paneles", "nivel": 1, "duracion_dias": 3,
        "subtareas": [{"texto": "Anclaje", "hecho": True}],
    }).json()
    client.patch(f"/api/planner/actividades/{act['id']}", json={"estado": "Completado"})
    client.post("/api/planner/asistencia", json={
        "proyecto_id": pid, "persona_id": persona["id"], "estado": "Presente",
        "hora": "08:00", "fecha": "2026-06-10",
    })
    client.post(f"/api/planner/proyectos/{pid}/curva-s/snapshot")
    foto = client.post(
        f"/api/planner/proyectos/{pid}/fotos",
        files={"file": ("obra.png", _png_bytes(), "image/png")},
        data={"etapa": "Paneles", "fecha": "2026-06-10"},
    ).json()
    client.patch(f"/api/planner/fotos/{foto['id']}", json={
        "incluir_en_pdf": True, "comentario_pdf": "Avance fila A",
    })
    return pid, persona["id"]


def test_pdf_cliente_se_genera(client):
    pid, persona_id = _proyecto_completo(client)
    try:
        r = client.get(f"/api/planner/proyectos/{pid}/pdf/cliente", params={"semana_num": 2})
        assert r.status_code == 200, r.text
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:5] == b"%PDF-"
        assert "attachment" in r.headers.get("content-disposition", "")
        assert len(r.content) > 1000  # un PDF real pesa
    finally:
        client.delete(f"/api/planner/proyectos/{pid}")
        client.delete(f"/api/planner/personal/{persona_id}")


def test_pdf_oficina_se_genera(client):
    pid, persona_id = _proyecto_completo(client)
    try:
        r = client.get(f"/api/planner/proyectos/{pid}/pdf/oficina", params={
            "tipo": "rango", "fecha_desde": "2026-06-01", "fecha_hasta": "2026-06-30",
        })
        assert r.status_code == 200, r.text
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:5] == b"%PDF-"
    finally:
        client.delete(f"/api/planner/proyectos/{pid}")
        client.delete(f"/api/planner/personal/{persona_id}")


def test_pdf_proyecto_inexistente(client):
    assert client.get("/api/planner/proyectos/999999999/pdf/cliente").status_code == 404
    assert client.get("/api/planner/proyectos/999999999/pdf/oficina").status_code == 404
