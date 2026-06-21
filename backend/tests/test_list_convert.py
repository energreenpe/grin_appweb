"""
Tests herméticos del módulo LIST — conversión (entregable #3).

No requieren Redis ni Gotenberg:
- Validaciones de /upload (extensión, vacío, tamaño).
- Atajo .pdf (guarda y sirve, sin job).
- /pdf anti path-traversal y 404.
- converter.convert_office_to_pdf con el HTTP de Gotenberg mockeado.
- /upload de DOCX con la cola mockeada (no encola de verdad).

La conversión real DOCX/XLSX→PDF se verifica en vivo con el stack levantado.
"""
import io

import httpx
import pytest

from app import storage
from app.modules.list import converter, service


# ── Validaciones de /upload ────────────────────────────────────────────────────
def test_upload_extension_invalida(client):
    r = client.post("/api/list/upload", files={"file": ("malo.txt", b"hola", "text/plain")})
    assert r.status_code == 400


def test_upload_vacio(client):
    r = client.post("/api/list/upload", files={"file": ("vacio.pdf", b"", "application/pdf")})
    assert r.status_code == 400


def test_upload_excede_tamano(client, monkeypatch):
    monkeypatch.setattr(service, "MAX_FILE_SIZE", 10)  # 10 bytes
    r = client.post(
        "/api/list/upload",
        files={"file": ("grande.pdf", b"x" * 50, "application/pdf")},
    )
    assert r.status_code == 413


# ── Atajo .pdf (sin conversión) ────────────────────────────────────────────────
def test_upload_pdf_atajo_y_servido(client):
    pdf_bytes = b"%PDF-1.4\n%mock\n"
    r = client.post(
        "/api/list/upload",
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "finished"
    assert body["job_id"] is None
    assert body["pdf_url"].startswith("/api/list/pdf/")

    name = body["pdf_name"]
    # El PDF queda servible por el endpoint.
    r2 = client.get(f"/api/list/pdf/{name}")
    assert r2.status_code == 200
    assert r2.headers["content-type"] == "application/pdf"

    # Limpieza del artefacto de test.
    storage.delete(f"uploads/{service.PDF_SUBDIR}/{name}")


# ── /pdf seguridad ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("bad", ["..%2f..%2fetc", "no_es_pdf.txt", "a/b.pdf"])
def test_serve_pdf_nombre_invalido(client, bad):
    r = client.get(f"/api/list/pdf/{bad}")
    assert r.status_code in (400, 404)  # 404 si el router de FastAPI no matchea la ruta


def test_serve_pdf_inexistente(client):
    r = client.get("/api/list/pdf/noexiste.pdf")
    assert r.status_code == 404


# ── converter con Gotenberg mockeado ───────────────────────────────────────────
def test_converter_ok(monkeypatch):
    def fake_post(url, files, timeout):
        assert url.endswith("/forms/libreoffice/convert")
        assert "files" in files
        return httpx.Response(200, content=b"%PDF-1.7 generado")

    monkeypatch.setattr(httpx, "post", fake_post)
    out = converter.convert_office_to_pdf(b"docx-bytes", "x.docx")
    assert out.startswith(b"%PDF")


def test_converter_error_http(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda url, files, timeout: httpx.Response(500, text="boom"))
    with pytest.raises(converter.ConversionError):
        converter.convert_office_to_pdf(b"docx-bytes", "x.docx")


def test_converter_gotenberg_inaccesible(monkeypatch):
    def boom(url, files, timeout):
        raise httpx.ConnectError("sin conexión")

    monkeypatch.setattr(httpx, "post", boom)
    with pytest.raises(converter.ConversionError):
        converter.convert_office_to_pdf(b"docx-bytes", "x.docx")


# ── /upload DOCX encola (cola mockeada) ────────────────────────────────────────
def test_upload_docx_encola(client, monkeypatch):
    class _FakeJob:
        id = "job-fake-123"

    class _FakeQueue:
        def enqueue(self, *args, **kwargs):
            return _FakeJob()

    monkeypatch.setattr(service, "get_queue", lambda name: _FakeQueue())

    r = client.post(
        "/api/list/upload",
        files={"file": ("contrato.docx", b"PK\x03\x04 docx mock", None)},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "queued"
    assert body["job_id"] == "job-fake-123"
