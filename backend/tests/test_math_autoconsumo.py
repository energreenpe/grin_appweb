"""
Tests de INTEGRACIÓN del endpoint POST /api/math/autoconsumo/calcular.

Usa el catálogo sembrado. Según el par panel/inversor, el motor puede devolver
3 opciones (200) o indicar incompatibilidad (400): ambas son respuestas válidas.
"""
import pytest


@pytest.fixture(scope="module")
def panel_id(client):
    return client.get("/api/math/equipos", params={"tipo": "panel"}).json()[0]["id"]


@pytest.fixture(scope="module")
def inversor_id(client):
    return client.get("/api/math/equipos", params={"tipo": "inversor_autoconsumo"}).json()[0]["id"]


def _payload(panel_id, inversor_id, **over):
    base = {
        "panel_id": panel_id,
        "inversor_id": inversor_id,
        "consumo_mensual": 300,
        "potencia_contratada": 5,
        "autarquia": 40,
        "tipo_conexion": "Monofásico",
        "voltaje_red": "220",
    }
    base.update(over)
    return base


def test_calcular_autoconsumo_responde(client, panel_id, inversor_id):
    r = client.post("/api/math/autoconsumo/calcular", json=_payload(panel_id, inversor_id))
    assert r.status_code in (200, 400), r.text
    if r.status_code == 200:
        data = r.json()
        assert 1 <= len(data["opciones"]) <= 3
        for op in data["opciones"]:
            assert op["paneles_total"] >= 1
            assert op["target"] in ("min", "opt", "max")
            assert "excede_contratada" in op
        assert data["parametros"]["potencia_minima_kw"] > 0
        assert data["parametros"]["consumo_mensual"] == 300
    else:
        assert r.json()["detail"]


def test_consumo_cero_es_422(client, panel_id, inversor_id):
    r = client.post("/api/math/autoconsumo/calcular", json=_payload(panel_id, inversor_id, consumo_mensual=0))
    assert r.status_code == 422


def test_panel_inexistente_es_404(client, inversor_id):
    r = client.post("/api/math/autoconsumo/calcular", json=_payload(999999, inversor_id))
    assert r.status_code == 404


def test_inversor_inexistente_es_404(client, panel_id):
    r = client.post("/api/math/autoconsumo/calcular", json=_payload(panel_id, 999999))
    assert r.status_code == 404


def test_temperaturas_invalidas_es_422(client, panel_id, inversor_id):
    r = client.post("/api/math/autoconsumo/calcular", json=_payload(panel_id, inversor_id, temp_min=50, temp_max=10))
    assert r.status_code == 422
