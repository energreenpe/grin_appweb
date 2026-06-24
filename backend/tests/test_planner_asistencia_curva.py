"""
Tests del módulo PLANNER — asistencia + Curva S (entregable E3).

Integración contra la BD de desarrollo migrada (tablas planner_*). Cada test
limpia el proyecto que crea (cascade arrastra asistencias y snapshots).
"""


def _crear_proyecto(client, **kw):
    payload = {"nombre": "Proy E3", "fecha_inicio": "2026-06-01", "fecha_fin": "2026-06-30"}
    payload.update(kw)
    return client.post("/api/planner/proyectos", json=payload).json()


def test_asistencia_individual_y_listado(client):
    proy = _crear_proyecto(client)
    pid = proy["id"]
    persona = client.post("/api/planner/personal", json={"nombre": "Carlos Ruiz"}).json()
    try:
        r = client.post("/api/planner/asistencia", json={
            "proyecto_id": pid, "persona_id": persona["id"],
            "estado": "Tardanza", "hora": "08:15", "fecha": "2026-06-10",
            "observacion": "Llegó 15 min tarde",
        })
        assert r.status_code == 201, r.text
        reg = r.json()
        assert reg["estado"] == "Tardanza"
        assert reg["nombre_persona"] == "Carlos Ruiz"  # derivado limpio

        # listar por fecha
        r = client.get(f"/api/planner/proyectos/{pid}/asistencia", params={"fecha": "2026-06-10"})
        assert r.status_code == 200
        assert len(r.json()) == 1 and r.json()[0]["id"] == reg["id"]

        # otra fecha → vacío
        r = client.get(f"/api/planner/proyectos/{pid}/asistencia", params={"fecha": "2026-06-11"})
        assert r.json() == []

        # actualizar y borrar
        r = client.patch(f"/api/planner/asistencia/{reg['id']}", json={"estado": "Presente"})
        assert r.status_code == 200 and r.json()["estado"] == "Presente"
        assert client.delete(f"/api/planner/asistencia/{reg['id']}").status_code == 200
        assert client.delete(f"/api/planner/asistencia/{reg['id']}").status_code == 404
    finally:
        client.delete(f"/api/planner/proyectos/{pid}")
        client.delete(f"/api/planner/personal/{persona['id']}")


def test_asistencia_bulk_upsert(client):
    proy = _crear_proyecto(client)
    pid = proy["id"]
    p1 = client.post("/api/planner/personal", json={"nombre": "Bulk Uno"}).json()
    p2 = client.post("/api/planner/personal", json={"nombre": "Bulk Dos"}).json()
    try:
        body = {
            "proyecto_id": pid, "fecha": "2026-06-12", "registrado_por": "Supervisor",
            "registros": [
                {"persona_id": p1["id"], "estado": "Presente", "hora": "08:00"},
                {"persona_id": p2["id"], "estado": "Ausente"},
            ],
        }
        r = client.post("/api/planner/asistencia/bulk", json=body)
        assert r.status_code == 201, r.text
        assert len(r.json()) == 2

        # mismo día, mismo personal → upsert (no duplica), cambia estado
        body["registros"][1]["estado"] = "Presente"
        r = client.post("/api/planner/asistencia/bulk", json=body)
        assert r.status_code == 201

        r = client.get(f"/api/planner/proyectos/{pid}/asistencia", params={"fecha": "2026-06-12"})
        regs = r.json()
        assert len(regs) == 2  # upsert, no duplicó
        assert all(x["estado"] == "Presente" for x in regs)
    finally:
        client.delete(f"/api/planner/proyectos/{pid}")
        client.delete(f"/api/planner/personal/{p1['id']}")
        client.delete(f"/api/planner/personal/{p2['id']}")


def test_curva_s_snapshot(client):
    proy = _crear_proyecto(client)
    pid = proy["id"]
    try:
        # sin snapshots aún
        assert client.get(f"/api/planner/proyectos/{pid}/curva-s").json() == []

        # crear una actividad y completarla → avance_real sube
        act = client.post("/api/planner/actividades", json={
            "proyecto_id": pid, "titulo": "Cableado DC", "nivel": 1, "duracion_dias": 3,
        }).json()
        client.patch(f"/api/planner/actividades/{act['id']}", json={"estado": "Completado"})

        # snapshot
        r = client.post(f"/api/planner/proyectos/{pid}/curva-s/snapshot")
        assert r.status_code == 201, r.text
        snap = r.json()
        assert snap["actividades_total"] == 1
        assert snap["actividades_hechas"] == 1
        assert snap["avance_real"] == 100.0

        # aparece en la curva
        r = client.get(f"/api/planner/proyectos/{pid}/curva-s")
        assert r.status_code == 200 and len(r.json()) == 1
    finally:
        client.delete(f"/api/planner/proyectos/{pid}")


def test_snapshot_proyecto_inexistente(client):
    assert client.post("/api/planner/proyectos/999999999/curva-s/snapshot").status_code == 404
