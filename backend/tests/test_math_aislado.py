"""
Tests de INTEGRACIÓN del endpoint POST /api/math/aislado/calcular.

Usa la BD de desarrollo sembrada (panel/batería reales del catálogo).
"""
import pytest


@pytest.fixture(scope="module")
def panel_id(client):
    r = client.get("/api/math/equipos", params={"tipo": "panel"})
    assert r.status_code == 200 and r.json()
    return r.json()[0]["id"]


@pytest.fixture(scope="module")
def bateria_id(client):
    r = client.get("/api/math/equipos", params={"tipo": "bateria"})
    assert r.status_code == 200 and r.json()
    return r.json()[0]["id"]


def _payload(panel_id, bateria_id, **over):
    base = {
        "cargas": [
            {"nombre": "TV LED", "cantidad": 2, "horas": 5, "potencia_w": 120},
            {"nombre": "REFRIGERADORA", "cantidad": 1, "horas": 8, "potencia_w": 300},
        ],
        "region": "Piura",
        "tipo_hsp": "promedio",
        "dias_autonomia": 2,
        "tipo_bateria": "Lead acid",
        "panel_id": panel_id,
        "bateria_id": bateria_id,
    }
    base.update(over)
    return base


def test_calcular_aislado_ok(client, panel_id, bateria_id):
    r = client.post("/api/math/aislado/calcular", json=_payload(panel_id, bateria_id))
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["voltaje_sistema"] in (12, 24, 48)
    assert data["num_paneles"] >= 1
    assert data["num_baterias"] >= 1
    assert data["consumo"]["energia_diaria_wh"] > 0
    assert data["potencia_inversor_w"] > 0
    assert isinstance(data["inversores_sugeridos"], list)
    assert data["panel"]["descripcion"]


def test_calcular_aislado_hsp_directo(client, panel_id, bateria_id):
    payload = _payload(panel_id, bateria_id, region=None, hsp=5.5)
    r = client.post("/api/math/aislado/calcular", json=payload)
    assert r.status_code == 200, r.text
    assert r.json()["hsp"] == pytest.approx(5.5)


def test_calcular_aislado_sin_cargas_es_422(client, panel_id, bateria_id):
    payload = _payload(panel_id, bateria_id)
    payload["cargas"] = []
    r = client.post("/api/math/aislado/calcular", json=payload)
    assert r.status_code == 422


def test_calcular_aislado_panel_inexistente_es_404(client, bateria_id):
    payload = _payload(999999, bateria_id)
    r = client.post("/api/math/aislado/calcular", json=payload)
    assert r.status_code == 404


def test_calcular_aislado_region_desconocida_es_422(client, panel_id, bateria_id):
    payload = _payload(panel_id, bateria_id, region="Narnia")
    r = client.post("/api/math/aislado/calcular", json=payload)
    assert r.status_code == 422


def test_calcular_aislado_horas_invalidas_es_422(client, panel_id, bateria_id):
    payload = _payload(panel_id, bateria_id)
    payload["cargas"][0]["horas"] = 30   # > 24
    r = client.post("/api/math/aislado/calcular", json=payload)
    assert r.status_code == 422
