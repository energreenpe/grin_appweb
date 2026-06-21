"""
Tests del módulo LIST — CRUD de plantillas (entregable #5).

Integración contra la BD de desarrollo (igual que los tests de catálogos de MATH).
Requiere PostgreSQL levantado y migrado (tabla list_plantillas, migración del #2).
"""


def test_plantilla_crud(client):
    payload = {
        "nombre": "Plantilla Test #5",
        "pdf_name": "base_demo.pdf",
        "fields": [{
            "page": 0, "x": 10, "y": 20, "width": 100, "height": 30,
            "text": "Hola", "font_family": "Helvetica", "font_size": 12,
        }],
        "overlays": [{"page": 0, "x": 0, "y": 0, "width": 50, "height": 20, "color": [1, 1, 1]}],
    }

    r = client.post("/api/list/templates", json=payload)
    assert r.status_code == 200
    created = r.json()
    pid = created["id"]

    try:
        assert created["nombre"] == "Plantilla Test #5"
        assert created["pdf_name"] == "base_demo.pdf"
        assert len(created["fields"]) == 1 and created["fields"][0]["text"] == "Hola"
        assert len(created["overlays"]) == 1

        # listar — debe aparecer
        r = client.get("/api/list/templates")
        assert r.status_code == 200
        assert any(p["id"] == pid for p in r.json())

        # obtener — detalle completo
        r = client.get(f"/api/list/templates/{pid}")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == pid
        assert body["overlays"][0]["color"] == [1.0, 1.0, 1.0]
        assert body["fields"][0]["font_color"] == [0.0, 0.0, 0.0]  # default endurecido
    finally:
        r = client.delete(f"/api/list/templates/{pid}")
        assert r.status_code == 200

    # ya no existe
    r = client.get(f"/api/list/templates/{pid}")
    assert r.status_code == 404


def test_plantilla_inexistente(client):
    r = client.get("/api/list/templates/999999999")
    assert r.status_code == 404


def test_plantilla_validacion_nombre_vacio(client):
    r = client.post("/api/list/templates", json={"nombre": "", "pdf_name": "x.pdf"})
    assert r.status_code == 422  # min_length=1
