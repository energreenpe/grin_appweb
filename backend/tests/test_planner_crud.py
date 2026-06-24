"""
Tests del módulo PLANNER — CRUD core (entregable E2).

Integración contra la BD de desarrollo ya migrada (tablas planner_*, migración
fb59ae7fba2b). Requiere PostgreSQL levantado. Cada test limpia lo que crea.
"""


def test_proyecto_crud(client):
    r = client.post("/api/planner/proyectos", json={
        "nombre": "Proyecto Test E2",
        "cliente": "Cliente Demo",
        "region": "Piura",
        "paneles": 12,
        "estado": "En Progreso",
        "fecha_inicio": "2026-06-01",
        "fecha_fin": "2026-06-30",
    })
    assert r.status_code == 201, r.text
    proy = r.json()
    pid = proy["id"]
    try:
        assert proy["nombre"] == "Proyecto Test E2"
        assert proy["estado"] == "En Progreso"
        assert proy["paneles"] == 12

        # listar
        r = client.get("/api/planner/proyectos")
        assert r.status_code == 200
        assert any(p["id"] == pid for p in r.json())

        # obtener
        r = client.get(f"/api/planner/proyectos/{pid}")
        assert r.status_code == 200

        # actualizar (patch parcial)
        r = client.patch(f"/api/planner/proyectos/{pid}", json={"estado": "Completado", "paneles": 20})
        assert r.status_code == 200
        assert r.json()["estado"] == "Completado"
        assert r.json()["paneles"] == 20
    finally:
        r = client.delete(f"/api/planner/proyectos/{pid}")
        assert r.status_code == 200

    # ya no existe
    assert client.get(f"/api/planner/proyectos/{pid}").status_code == 404


def test_proyecto_inexistente(client):
    assert client.get("/api/planner/proyectos/999999999").status_code == 404


def test_proyecto_nombre_invalido(client):
    # min_length=2
    r = client.post("/api/planner/proyectos", json={"nombre": "X"})
    assert r.status_code == 422


def test_personal_crud(client):
    r = client.post("/api/planner/personal", json={
        "nombre": "Juan Pérez", "dni": "12345678", "profesion": "Técnico en Energía Solar",
    })
    assert r.status_code == 201, r.text
    persona = r.json()
    pid = persona["id"]
    try:
        assert persona["nombre"] == "Juan Pérez"
        assert persona["estado"] == "Activo"  # default

        r = client.get("/api/planner/personal")
        assert any(p["id"] == pid for p in r.json())

        r = client.patch(f"/api/planner/personal/{pid}", json={"estado": "Inactivo"})
        assert r.status_code == 200
        assert r.json()["estado"] == "Inactivo"
    finally:
        assert client.delete(f"/api/planner/personal/{pid}").status_code == 200
    assert client.patch(f"/api/planner/personal/{pid}", json={"celular": "999"}).status_code == 404


def test_cuadrilla_y_miembro(client):
    # proyecto contenedor
    proy = client.post("/api/planner/proyectos", json={"nombre": "Proy Cuadrillas E2"}).json()
    pid = proy["id"]
    persona = client.post("/api/planner/personal", json={"nombre": "Ana Torres"}).json()
    persona_id = persona["id"]
    try:
        # crear cuadrilla
        r = client.post("/api/planner/cuadrillas", json={"proyecto_id": pid, "nombre": "Cuadrilla 1"})
        assert r.status_code == 201, r.text
        cid = r.json()["id"]

        # asignar miembro
        r = client.post(f"/api/planner/cuadrillas/{cid}/miembros", json={
            "persona_id": persona_id, "rol_interno": "Jefe de Cuadrilla",
        })
        assert r.status_code == 201, r.text
        miembro = r.json()
        mid = miembro["id"]
        # nombre_persona derivado limpio (sin hack __dict__)
        assert miembro["nombre_persona"] == "Ana Torres"
        assert miembro["rol_interno"] == "Jefe de Cuadrilla"

        # aparece embebido al listar cuadrillas
        r = client.get(f"/api/planner/proyectos/{pid}/cuadrillas")
        assert r.status_code == 200
        cuad = next(c for c in r.json() if c["id"] == cid)
        assert any(m["nombre_persona"] == "Ana Torres" for m in cuad["miembros"])

        # remover miembro
        assert client.delete(f"/api/planner/miembros/{mid}").status_code == 200
        assert client.delete(f"/api/planner/miembros/{mid}").status_code == 404
    finally:
        # borrar el proyecto arrastra cuadrillas/miembros (cascade)
        client.delete(f"/api/planner/proyectos/{pid}")
        client.delete(f"/api/planner/personal/{persona_id}")


def test_actividad_crud_y_avance(client):
    proy = client.post("/api/planner/proyectos", json={
        "nombre": "Proy Actividades E2",
        "fecha_inicio": "2026-06-01", "fecha_fin": "2026-06-30",
    }).json()
    pid = proy["id"]
    try:
        # actividad nivel 1 con subtareas (columna JSON)
        r = client.post("/api/planner/actividades", json={
            "proyecto_id": pid, "titulo": "Montaje de estructuras", "nivel": 1,
            "duracion_dias": 5, "prioridad": "Alta",
            "subtareas": [{"texto": "Anclajes", "hecho": False}, {"texto": "Rieles", "hecho": True}],
        })
        assert r.status_code == 201, r.text
        act = r.json()
        aid = act["id"]
        assert act["titulo"] == "Montaje de estructuras"
        assert len(act["subtareas"]) == 2
        assert act["subtareas"][1]["hecho"] is True

        # listar
        r = client.get(f"/api/planner/proyectos/{pid}/actividades")
        assert any(a["id"] == aid for a in r.json())

        # completar → recalcula avance_real del proyecto a 100%
        r = client.patch(f"/api/planner/actividades/{aid}", json={"estado": "Completado"})
        assert r.status_code == 200
        proy_now = client.get(f"/api/planner/proyectos/{pid}").json()
        assert proy_now["avance_real"] == 100.0

        # borrar
        assert client.delete(f"/api/planner/actividades/{aid}").status_code == 200
        assert client.delete(f"/api/planner/actividades/{aid}").status_code == 404
    finally:
        client.delete(f"/api/planner/proyectos/{pid}")


def test_actividad_proyecto_inexistente_da_400(client):
    # FK violada → IntegrityError traducido a 400
    r = client.post("/api/planner/actividades", json={
        "proyecto_id": 999999999, "titulo": "Huérfana", "nivel": 1,
    })
    assert r.status_code == 400


def test_kpis(client):
    r = client.get("/api/planner/kpis")
    assert r.status_code == 200
    body = r.json()
    for k in ("total_proyectos", "proyectos_activos", "total_personal", "total_cuadrillas"):
        assert k in body and isinstance(body[k], int)
