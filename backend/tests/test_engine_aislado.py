"""
Tests UNITARIOS del motor Aislado (funciones puras, sin BD ni TestClient).

Valores esperados verificados a mano contra la lógica del legacy.
"""
import math
import pytest
from app.modules.math import engine_aislado as eng

CARGAS = [
    {"cantidad": 2, "potencia_w": 100, "horas": 5},   # 200 W, 1000 Wh
    {"cantidad": 1, "potencia_w": 50,  "horas": 2},   #  50 W,  100 Wh
]


def test_calcular_consumo():
    pmax, energia, pac = eng.calcular_consumo(CARGAS)
    assert pmax == 250
    assert energia == 1100
    assert pac == pytest.approx(312.5)


@pytest.mark.parametrize("energia,esperado", [
    (500, 12), (999, 12), (1000, 24), (2399, 24), (2400, 48), (5000, 48),
])
def test_seleccionar_voltaje_sistema(energia, esperado):
    assert eng.seleccionar_voltaje_sistema(energia) == esperado


def test_calcular_potencia_pico():
    assert eng.calcular_potencia_pico(1000, 5) == pytest.approx(1250 / 3.75)


def test_calcular_potencia_pico_hsp_cero_falla():
    with pytest.raises(ValueError):
        eng.calcular_potencia_pico(1000, 0)


@pytest.mark.parametrize("pp,potencia,esperado", [
    (333.33, 580, 1),
    (580, 580, 1),
    (581, 580, 2),
    (1200, 580, 3),
])
def test_calcular_numero_paneles(pp, potencia, esperado):
    assert eng.calcular_numero_paneles(pp, {"Potencia": potencia}) == esperado


def test_calcular_numero_paneles_panel_invalido():
    with pytest.raises(ValueError):
        eng.calcular_numero_paneles(500, {"Potencia": 0})


def test_calcular_capacidad_baterias_plomo_vs_litio():
    plomo = eng.calcular_capacidad_baterias(1000, 2, "Lead acid", 24)
    litio = eng.calcular_capacidad_baterias(1000, 2, "Lithium", 24)
    assert plomo == pytest.approx(2000 / 9.6)     # 208.33
    assert litio == pytest.approx(2000 / 18.24)   # 109.65
    assert litio < plomo                          # litio admite más descarga


def test_calcular_numero_baterias():
    # 24V con baterías de 12V -> 2 en serie; ceil(208.33/100)=3 -> 6
    n = eng.calcular_numero_baterias(208.33, {"capacidad": 100, "Vbat": 12}, 24)
    assert n == 6


def test_calcular_numero_baterias_invalida():
    with pytest.raises(ValueError):
        eng.calcular_numero_baterias(200, {"capacidad": 0, "Vbat": 12}, 24)


def test_calcular_potencia_inversor():
    assert eng.calcular_potencia_inversor(312.5) == pytest.approx((312.5 / 0.93) * 1.25)


def test_sugerir_inversores_en_paralelo():
    inversores = [
        {"descripcion": "Solis 5kW", "marca": "Solis", "wout": 5000, "Vbat": 48},
        {"descripcion": "Malo", "marca": "X", "wout": 0, "Vbat": 48},   # se omite (wout<=0)
    ]
    out = eng.sugerir_inversores_en_paralelo(inversores, 48, 12000)
    assert len(out) == 1
    assert out[0]["cantidad"] == math.ceil(12000 / 5000)  # 3
    assert out[0]["potencia_total"] == 15000
    assert out[0]["modelo"] == "Solis 5kW"


def test_calcular_aislado_end_to_end():
    res = eng.calcular_aislado(
        cargas=CARGAS,
        hsp=5,
        dias_autonomia=2,
        tipo_bateria="Lead acid",
        panel={"Potencia": 580, "descripcion": "Panel 580"},
        bateria={"capacidad": 100, "Vbat": 12, "descripcion": "Bat 12V/100Ah"},
        inversores=[{"descripcion": "Solis 5kW", "marca": "Solis", "wout": 5000, "Vbat": 48}],
    )
    assert res["consumo"]["energia_diaria_wh"] == 1100
    assert res["consumo"]["potencia_ac_w"] == pytest.approx(312.5)
    assert res["voltaje_sistema"] == 24                # 1100 Wh -> 24V automático
    # La salida del orquestador se redondea a 2 decimales (los pasos puros van a precisión completa).
    assert res["potencia_pico_wp"] == round(1375 / 3.75, 2)
    assert res["num_paneles"] == 1
    assert res["num_baterias"] == 6
    assert res["panel"]["descripcion"] == "Panel 580"
    assert res["inversores_sugeridos"][0]["cantidad"] == 1


def test_calcular_aislado_voltaje_override():
    res = eng.calcular_aislado(
        cargas=CARGAS, hsp=5, dias_autonomia=2, tipo_bateria="Lead acid",
        panel={"Potencia": 580}, bateria={"capacidad": 100, "Vbat": 12},
        inversores=[], voltaje_sistema=48,
    )
    assert res["voltaje_sistema"] == 48


def test_calcular_aislado_sin_cargas_falla():
    with pytest.raises(ValueError):
        eng.calcular_aislado(
            cargas=[], hsp=5, dias_autonomia=2, tipo_bateria="Lead acid",
            panel={"Potencia": 580}, bateria={"capacidad": 100, "Vbat": 12}, inversores=[],
        )
