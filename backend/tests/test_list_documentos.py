"""
Tests del módulo LIST — CRUD de documentos (entregable #9).

Integración contra la BD de desarrollo (tabla list_documentos). Crea un PDF base
"real" (dummy) en list/pdf para que crear_documento lo valide.
"""
from app import storage
from app.modules.list import service


def _crear_pdf_base(name="doc_base_test.pdf"):
    storage.save_bytes(b"%PDF-1.4\n%mock\n%%EOF", service.PDF_SUBDIR, name)
    return name


def test_documento_crud_y_autoguardado(client):
    pdf_name = _crear_pdf_base()
    r = client.post("/api/list/documentos", json={"nombre": "Contrato.docx", "pdf_name": pdf_name})
    assert r.status_code == 200
    doc = r.json()
    did = doc["id"]
    try:
        assert doc["nombre"] == "Contrato.docx"
        assert doc["pdf_name"] == pdf_name
        assert doc["fields"] == [] and doc["overlays"] == []

        # Aparece en el listado
        r = client.get("/api/list/documentos")
        assert r.status_code == 200
        assert any(d["id"] == did for d in r.json())

        # Autoguardado: persistir fields/overlays
        upd = {
            "fields": [{"page": 0, "x": 10, "y": 20, "width": 100, "height": 30, "text": "Hola"}],
            "overlays": [{"page": 0, "x": 0, "y": 0, "width": 40, "height": 15, "color": [1, 1, 1]}],
        }
        r = client.put(f"/api/list/documentos/{did}", json=upd)
        assert r.status_code == 200

        # Reabrir → el avance está guardado
        r = client.get(f"/api/list/documentos/{did}")
        body = r.json()
        assert len(body["fields"]) == 1 and body["fields"][0]["text"] == "Hola"
        assert len(body["overlays"]) == 1
    finally:
        r = client.delete(f"/api/list/documentos/{did}")
        assert r.status_code == 200

    # Eliminado: ya no existe y su PDF base también se borró
    assert client.get(f"/api/list/documentos/{did}").status_code == 404
    assert storage.resolve(f"uploads/{service.PDF_SUBDIR}/{pdf_name}") is None


def test_documento_pdf_base_inexistente(client):
    r = client.post("/api/list/documentos", json={"nombre": "x.docx", "pdf_name": "no_existe.pdf"})
    assert r.status_code == 404


def test_documento_inexistente(client):
    assert client.get("/api/list/documentos/999999999").status_code == 404
