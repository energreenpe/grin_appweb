"""
Tests de integración de los endpoints de catálogo del módulo MATH (Entregable #2).

Solo lectura. Asume la BD de desarrollo migrada y sembrada con scripts/seed_math.py.
Las aserciones son resilientes (presencia/estructura, no conteos exactos que puedan
variar con el tiempo).
"""

TIPOS_EQUIPO = ["panel", "bateria", "inversor_aislado", "inversor_autoconsumo"]


def test_ping(client):
    r = client.get("/api/math/ping")
    assert r.status_code == 200
    assert r.json() == {"module": "math", "status": "ok"}


def test_listar_regiones(client):
    r = client.get("/api/math/regiones")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    piura = next((x for x in data if x["nombre"] == "Piura"), None)
    assert piura is not None, "Se esperaba la región Piura en el seed"
    assert piura["hsp_promedio"] is not None


def test_listar_equipos_por_tipo(client):
    for tipo in TIPOS_EQUIPO:
        r = client.get("/api/math/equipos", params={"tipo": tipo})
        assert r.status_code == 200, f"tipo={tipo}"
        data = r.json()
        assert len(data) >= 1, f"sin equipos para tipo={tipo}"
        assert all(e["tipo"] == tipo for e in data)
        assert all(e["activo"] for e in data)
        assert isinstance(data[0]["specs"], dict) and data[0]["specs"]


def test_listar_equipos_sin_tipo_devuelve_todos(client):
    r = client.get("/api/math/equipos")
    assert r.status_code == 200
    tipos = {e["tipo"] for e in r.json()}
    assert tipos == set(TIPOS_EQUIPO)


def test_listar_equipos_tipo_invalido_es_422(client):
    r = client.get("/api/math/equipos", params={"tipo": "no_existe"})
    assert r.status_code == 422


def test_listar_electrodomesticos(client):
    r = client.get("/api/math/electrodomesticos")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert all("potencia_w" in e for e in data)
    assert all(isinstance(e["potencia_w"], (int, float)) for e in data)


def test_listar_ingenieros(client):
    r = client.get("/api/math/ingenieros")
    assert r.status_code == 200
    data = r.json()
    assert all(u["rol"] == "ingeniero" for u in data)
    assert any(u["correo"] == "luis@gmail.com" for u in data), "Se esperaba el ingeniero sembrado"


def test_buscar_clientes_devuelve_lista(client):
    r = client.get("/api/math/clientes/search", params={"q": ""})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
