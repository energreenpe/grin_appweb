"""
Tests de INTEGRACIÓN del CRUD de Cálculos (Entregable #4).

Crea un cliente de prueba (upsert idempotente por nombre) y un cálculo aislado,
ejercita el ciclo completo y limpia el cálculo al final de cada test.
"""
import pytest

CLIENTE_TEST = "TEST MATH CLIENTE"


@pytest.fixture(scope="module")
def ctx(client):
    ingenieros = client.get("/api/math/ingenieros").json()
    cliente = client.post(
        "/api/math/clientes",
        json={"nombre": CLIENTE_TEST, "documento": None, "telefono": "999999999"},
    ).json()
    panel = client.get("/api/math/equipos", params={"tipo": "panel"}).json()[0]
    bateria = client.get("/api/math/equipos", params={"tipo": "bateria"}).json()[0]
    yield {
        "ingeniero_id": ingenieros[0]["id"] if ingenieros else None,
        "cliente_id": cliente["id"],
        "panel_id": panel["id"],
        "bateria_id": bateria["id"],
    }
    # Limpieza: borrar el cliente de prueba para no contaminar datos_cliente
    # (no hay endpoint de borrado de clientes en MATH; se hace directo por ORM).
    from app.db import SessionLocal
    from app.modules.shared.models import DatosCliente
    db = SessionLocal()
    try:
        c = db.query(DatosCliente).filter(DatosCliente.nombre == CLIENTE_TEST).first()
        if c:
            db.delete(c)
            db.commit()
    finally:
        db.close()


def _nuevo_payload(ctx, **over):
    payload = {
        "nombre_proyecto": "Proyecto Test Aislado",
        "cliente_id": ctx["cliente_id"],
        "tipo_cliente": "Persona",
        "ingeniero_id": ctx["ingeniero_id"],
        "region": "Piura",
        "tipo_sistema": "SFV Aislado",
        "entrada": {
            "cargas": [{"nombre": "TV LED", "cantidad": 2, "horas": 5, "potencia_w": 120}],
            "dias_autonomia": 2,
            "tipo_bateria": "Lead acid",
            "panel_id": ctx["panel_id"],
            "bateria_id": ctx["bateria_id"],
            "tipo_hsp": "promedio",
        },
    }
    payload.update(over)
    return payload


@pytest.fixture
def calculo(client, ctx):
    r = client.post("/api/math/calculos", json=_nuevo_payload(ctx))
    assert r.status_code == 200, r.text
    data = r.json()
    yield data
    client.delete(f"/api/math/calculos/{data['id']}")


def test_crear_calculo(calculo, ctx):
    assert calculo["id"] > 0
    assert calculo["estado"] == "borrador"
    assert calculo["tipo_sistema"] == "SFV Aislado"
    assert calculo["resultado"] is None
    assert calculo["cliente"]["id"] == ctx["cliente_id"]
    assert calculo["ingeniero"]["rol"] == "ingeniero"


def test_obtener_calculo(client, calculo):
    r = client.get(f"/api/math/calculos/{calculo['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == calculo["id"]


def test_obtener_calculo_inexistente_404(client):
    r = client.get("/api/math/calculos/999999")
    assert r.status_code == 404


def test_actualizar_calculo(client, calculo):
    r = client.put(f"/api/math/calculos/{calculo['id']}", json={"notas": "Revisado"})
    assert r.status_code == 200
    assert r.json()["notas"] == "Revisado"


def test_calcular_persiste_resultado(client, calculo):
    r = client.post(f"/api/math/calculos/{calculo['id']}/calcular")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["resultado"] is not None
    assert data["resultado"]["num_paneles"] >= 1
    assert data["paso_actual"] == "resultado"


def test_completar_sin_resultado_400(client, calculo):
    r = client.post(f"/api/math/calculos/{calculo['id']}/completar")
    assert r.status_code == 400


def test_completar_tras_calcular(client, calculo):
    assert client.post(f"/api/math/calculos/{calculo['id']}/calcular").status_code == 200
    r = client.post(f"/api/math/calculos/{calculo['id']}/completar")
    assert r.status_code == 200
    assert r.json()["estado"] == "completado"


def test_listar_filtra_por_tipo(client, calculo):
    r = client.get("/api/math/calculos", params={"tipo_sistema": "SFV Aislado"})
    assert r.status_code == 200
    ids = [c["id"] for c in r.json()]
    assert calculo["id"] in ids


def test_crear_calculo_cliente_invalido_400(client, ctx):
    payload = _nuevo_payload(ctx, cliente_id=999999)
    r = client.post("/api/math/calculos", json=payload)
    assert r.status_code == 400


def test_eliminar_calculo(client, ctx):
    creado = client.post("/api/math/calculos", json=_nuevo_payload(ctx)).json()
    r = client.delete(f"/api/math/calculos/{creado['id']}")
    assert r.status_code == 200
    assert client.get(f"/api/math/calculos/{creado['id']}").status_code == 404
