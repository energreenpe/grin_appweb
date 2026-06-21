"""
Tests del módulo LIST — seguridad y limpieza (entregable #6).

Herméticos (sin Redis ni Gotenberg):
- Magic-bytes: un archivo cuyo contenido no coincide con su extensión → 400.
- Limpieza por TTL: archivos viejos se borran, recientes se conservan.
"""
import os
import time

from app import storage
from app.modules.list import maintenance


# ── Magic-bytes en /upload ──────────────────────────────────────────────────────
def test_upload_pdf_con_contenido_falso(client):
    r = client.post("/api/list/upload", files={"file": ("fake.pdf", b"esto no es un pdf", "application/pdf")})
    assert r.status_code == 400


def test_upload_docx_con_contenido_falso(client):
    r = client.post("/api/list/upload", files={"file": ("fake.docx", b"esto no es un zip", None)})
    assert r.status_code == 400


def test_upload_pdf_real_pasa_magic(client):
    r = client.post("/api/list/upload", files={"file": ("ok.pdf", b"%PDF-1.4\n%mock\n", "application/pdf")})
    assert r.status_code == 200
    # limpieza del artefacto
    storage.delete(f"uploads/list/pdf/{r.json()['pdf_name']}")


# ── Limpieza por TTL ──────────────────────────────────────────────────────────--
def test_limpieza_ttl():
    old_rel = storage.save_bytes(b"old", "list/incoming", "ttl_old_test.bin")
    new_rel = storage.save_bytes(b"new", "list/incoming", "ttl_new_test.bin")

    # Envejecer el "old" 2 horas (incoming TTL = 1 h).
    old_full = storage.resolve(old_rel)
    dos_horas = time.time() - 2 * 3600
    os.utime(old_full, (dos_horas, dos_horas))

    borrados = maintenance.limpiar_temporales()

    assert storage.resolve(old_rel) is None          # viejo → borrado
    assert storage.resolve(new_rel) is not None       # reciente → conservado
    assert borrados["list/incoming"] >= 1

    storage.delete(new_rel)  # limpieza del artefacto
