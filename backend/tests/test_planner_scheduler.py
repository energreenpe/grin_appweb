"""
Tests del motor de cronograma PLANNER (entregable E4).

- Tests PUROS de scheduler.py (sin BD): fines de semana, feriados, dependencias FS+lag.
- Tests de INTEGRACIÓN del recálculo (avance por días laborables + fechas plan).
"""
from datetime import date
from types import SimpleNamespace

from app.modules.planner import scheduler, service

# Semana de referencia: lun 2026-06-01 ... dom 2026-06-07.
LUN = date(2026, 6, 1)
VIE = date(2026, 6, 5)
SAB = date(2026, 6, 6)


# ───────────── PUROS ─────────────
def test_es_dia_laborable_fin_de_semana_y_feriado():
    assert scheduler.es_dia_laborable(LUN, set()) is True
    assert scheduler.es_dia_laborable(SAB, set()) is False          # sábado
    assert scheduler.es_dia_laborable(LUN, {LUN}) is False          # feriado


def test_siguiente_laborable_salta_finde():
    # Sábado 06 → lunes 08
    assert scheduler.siguiente_laborable(SAB, set()) == date(2026, 6, 8)


def test_fecha_fin_laborable_salta_finde():
    # Inicio jueves 04, duración 3 laborables → jue, vie, lun = lunes 08.
    fin = scheduler.fecha_fin_laborable(date(2026, 6, 4), 3, set())
    assert fin == date(2026, 6, 8)


def test_fecha_fin_laborable_descuenta_feriado():
    # Inicio lun 01, duración 3; con feriado el mié 03 → lun, mar, jue = jue 04.
    fin = scheduler.fecha_fin_laborable(LUN, 3, {date(2026, 6, 3)})
    assert fin == date(2026, 6, 4)


def test_hito_duracion_cero():
    assert scheduler.fecha_fin_laborable(LUN, 0, set()) == LUN


def test_contar_laborables_excluye_finde():
    # lun 01 .. dom 07 → 5 laborables (lun-vie).
    assert scheduler.contar_laborables(LUN, date(2026, 6, 7), set()) == 5
    # con un feriado el martes → 4.
    assert scheduler.contar_laborables(LUN, date(2026, 6, 7), {date(2026, 6, 2)}) == 4


def test_cronograma_fs_lag():
    # A: inicia lun 01, dura 5 laborables → termina vie 05.
    # B: depende FS de A con lag 0 → arranca el siguiente laborable = lun 08.
    acts = [
        {"id": 1, "fecha_inicio_plan": LUN, "duracion_dias": 5, "es_hito": False},
        {"id": 2, "fecha_inicio_plan": None, "duracion_dias": 2, "es_hito": False},
    ]
    deps = [{"actividad_id": 2, "depende_de_id": 1, "tipo": "FS", "lag_dias": 0}]
    r = scheduler.recalcular_cronograma(acts, deps, set())
    assert r[1]["fecha_fin_plan"] == VIE
    assert r[2]["fecha_inicio_plan"] == date(2026, 6, 8)   # lunes siguiente
    # B dura 2 → lun 08, mar 09.
    assert r[2]["fecha_fin_plan"] == date(2026, 6, 9)


def test_cronograma_fs_con_lag_positivo():
    acts = [
        {"id": 1, "fecha_inicio_plan": LUN, "duracion_dias": 1, "es_hito": False},  # fin lun 01
        {"id": 2, "fecha_inicio_plan": None, "duracion_dias": 1, "es_hito": False},
    ]
    deps = [{"actividad_id": 2, "depende_de_id": 1, "tipo": "FS", "lag_dias": 2}]
    r = scheduler.recalcular_cronograma(acts, deps, set())
    # fin pred = lun 01; +1 (siguiente) +2 lag = jueves 04.
    assert r[2]["fecha_inicio_plan"] == date(2026, 6, 4)


def test_cronograma_tolera_ciclo_sin_colgarse():
    acts = [
        {"id": 1, "fecha_inicio_plan": LUN, "duracion_dias": 1, "es_hito": False},
        {"id": 2, "fecha_inicio_plan": LUN, "duracion_dias": 1, "es_hito": False},
    ]
    deps = [
        {"actividad_id": 1, "depende_de_id": 2, "tipo": "FS", "lag_dias": 0},
        {"actividad_id": 2, "depende_de_id": 1, "tipo": "FS", "lag_dias": 0},
    ]
    r = scheduler.recalcular_cronograma(acts, deps, set())  # no debe colgarse
    assert set(r.keys()) == {1, 2}


# ───────────── AVANCE PLANIFICADO (determinista, hoy explícito) ─────────────
def test_avance_planificado_dias_laborables():
    # Semana laboral lun 01 .. vie 05 (5 días laborables).
    proy = SimpleNamespace(fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 6, 5))
    # hoy posterior al fin → 100%.
    assert service._avance_planificado(proy, set(), hoy=date(2026, 6, 30)) == 100.0
    # hoy = miércoles 03 → 3 de 5 laborables = 60%.
    assert service._avance_planificado(proy, set(), hoy=date(2026, 6, 3)) == 60.0
    # hoy anterior al inicio → 0%.
    assert service._avance_planificado(proy, set(), hoy=date(2026, 5, 1)) == 0.0
    # con feriado el martes 02 → total 4 laborables; al mié 03 van 2 → 50%.
    assert service._avance_planificado(proy, {date(2026, 6, 2)}, hoy=date(2026, 6, 3)) == 50.0


def test_avance_planificado_sin_fechas():
    proy = SimpleNamespace(fecha_inicio=None, fecha_fin=None)
    assert service._avance_planificado(proy, set()) == 0.0


def test_fechas_actividad_respetan_dias_laborables(client):
    proy = client.post("/api/planner/proyectos", json={
        "nombre": "Proy Fechas E4",
    }).json()
    pid = proy["id"]
    try:
        # Inicio jueves 04, duración 3 laborables → fin lunes 08 (salta finde).
        act = client.post("/api/planner/actividades", json={
            "proyecto_id": pid, "titulo": "Estructura", "nivel": 1,
            "fecha_inicio_plan": "2026-06-04", "duracion_dias": 3,
        }).json()
        assert act["fecha_inicio_plan"] == "2026-06-04"
        assert act["fecha_fin_plan"] == "2026-06-08"
    finally:
        client.delete(f"/api/planner/proyectos/{pid}")


def test_recalcular_gantt_endpoint_404(client):
    assert client.post("/api/planner/proyectos/999999999/recalcular-gantt").status_code == 404


def test_feriado_crud_y_efecto_en_fechas(client):
    # Feriado regional Piura el viernes 05 → una actividad jue-vie de 2 días salta al lunes.
    fer = client.post("/api/planner/feriados", json={
        "nombre": "Feriado Piura Test", "fecha": "2026-06-05",
        "tipo": "Regional", "region": "Piura",
    }).json()
    proy = client.post("/api/planner/proyectos", json={
        "nombre": "Proy Feriado E4", "region": "Piura",
    }).json()
    pid = proy["id"]
    try:
        assert fer["anio"] == 2026  # derivado de la fecha
        # Inicio jue 04, duración 2; con feriado el vie 05 → jue 04 + lun 08.
        act = client.post("/api/planner/actividades", json={
            "proyecto_id": pid, "titulo": "Montaje", "nivel": 1,
            "fecha_inicio_plan": "2026-06-04", "duracion_dias": 2,
        }).json()
        assert act["fecha_fin_plan"] == "2026-06-08"
    finally:
        client.delete(f"/api/planner/proyectos/{pid}")
        client.delete(f"/api/planner/feriados/{fer['id']}")
