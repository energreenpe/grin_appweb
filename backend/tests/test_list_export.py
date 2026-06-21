"""
Tests herméticos del módulo LIST — estampado/exportación (entregable #4).

No requieren Redis ni Gotenberg:
- pdf_stamp.stamp_pdf: estampa texto + overlay y se puede leer de vuelta.
- Conversión de coordenadas top-left → bottom-left preserva páginas y validez.
- /export: validaciones (pdf inexistente/ inválido) y encolado (cola mockeada).
- /output anti path-traversal y 404.
"""
import io

import pytest
from pypdf import PdfReader
from reportlab.pdfgen import canvas as rcanvas

from app import storage
from app.modules.list import pdf_stamp, service


def _blank_pdf(width: float = 595.0, height: float = 842.0, pages: int = 1) -> bytes:
    buf = io.BytesIO()
    c = rcanvas.Canvas(buf, pagesize=(width, height))
    for _ in range(pages):
        c.showPage()
    c.save()
    return buf.getvalue()


# ── pdf_stamp (lógica pura) ─────────────────────────────────────────────────────
def test_stamp_pdf_texto_y_overlay():
    source = _blank_pdf()
    fields = [{
        "page": 0, "x": 50, "y": 50, "width": 400, "height": 120,
        "text": "HOLALIST2026", "font_family": "Helvetica", "font_size": 24,
        "font_color": [0.0, 0.0, 0.0], "bg_color": None,
    }]
    overlays = [{"page": 0, "x": 0, "y": 0, "width": 120, "height": 40, "color": [0.9, 0.9, 0.9]}]

    out = pdf_stamp.stamp_pdf(source, fields, overlays)
    assert out[:4] == b"%PDF"

    reader = PdfReader(io.BytesIO(out))
    assert len(reader.pages) == 1
    text = (reader.pages[0].extract_text() or "").replace(" ", "")
    assert "HOLALIST2026" in text


def test_stamp_pdf_sin_elementos_preserva_paginas():
    source = _blank_pdf(pages=3)
    out = pdf_stamp.stamp_pdf(source, [], [])
    assert out[:4] == b"%PDF"
    assert len(PdfReader(io.BytesIO(out)).pages) == 3


def test_stamp_pdf_ignora_pagina_fuera_de_rango():
    source = _blank_pdf(pages=1)
    fields = [{
        "page": 5, "x": 10, "y": 10, "width": 100, "height": 20,
        "text": "fuera", "font_family": "Helvetica", "font_size": 12,
        "font_color": [0, 0, 0], "bg_color": None,
    }]
    out = pdf_stamp.stamp_pdf(source, fields, [])
    assert len(PdfReader(io.BytesIO(out)).pages) == 1


# ── /export ─────────────────────────────────────────────────────────────────────
def test_export_pdf_inexistente(client):
    r = client.post("/api/list/export", json={"pdf_name": "noexiste.pdf", "fields": [], "overlays": []})
    assert r.status_code == 404


def test_export_pdf_nombre_invalido(client):
    r = client.post("/api/list/export", json={"pdf_name": "../secret.pdf", "fields": [], "overlays": []})
    assert r.status_code == 400


def test_export_encola(client, monkeypatch):
    # PDF base "real" (dummy) presente en list/pdf.
    name = "base_test.pdf"
    storage.save_bytes(_blank_pdf(), service.PDF_SUBDIR, name)

    class _FakeJob:
        id = "export-fake-1"

    class _FakeQueue:
        def enqueue(self, *args, **kwargs):
            return _FakeJob()

    monkeypatch.setattr(service, "get_queue", lambda q: _FakeQueue())

    try:
        r = client.post("/api/list/export", json={
            "pdf_name": name,
            "fields": [{"page": 0, "x": 1, "y": 1, "width": 50, "height": 20, "text": "hi"}],
            "overlays": [],
        })
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "queued"
        assert body["job_id"] == "export-fake-1"
    finally:
        storage.delete(f"uploads/{service.PDF_SUBDIR}/{name}")


# ── /output seguridad ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("bad", ["no_es_pdf.txt", "a/b.pdf"])
def test_output_nombre_invalido(client, bad):
    r = client.get(f"/api/list/output/{bad}")
    assert r.status_code in (400, 404)


def test_output_inexistente(client):
    r = client.get("/api/list/output/noexiste.pdf")
    assert r.status_code == 404
