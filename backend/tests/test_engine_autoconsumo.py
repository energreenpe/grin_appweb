"""
Tests UNITARIOS del motor Autoconsumo (funciones puras, sin BD).

Escenario controlado (valores verificados a mano):
  Panel:    440 Wp, Vmpp 33, Impp 10, Voc 40, Isc 12
  Inversor: 5 kW, Vmax 600, Vstartup 100, Vmpp 90–560, Impp 12, Isc 15,
            MPPT 2, Input_MPPT 1, Wp_max 7.5 kW
  Rango de paneles en serie esperado: 4..12
  Config óptima (ratio~1.2): 7 en serie -> 14 paneles totales
"""
import pytest
from app.modules.math import engine_autoconsumo as eng

PANEL = {"descripcion": "P440", "Potencia": 440, "Vmpp": 33, "Impp": 10, "Voc": 40, "Isc": 12}
INV = {
    "descripcion": "INV5k", "Wout": 5000, "Vmax": 600, "Vstartup": 100,
    "Vmpp_min": 90, "Vmpp_max": 560, "Impp": 12, "Isc": 15,
    "MPPT": 2, "Input_MPPT": 1, "Wp_max": 7500,
}


def test_potencia_minima_desde_consumo():
    # (300/30 × 0.40) / (4.5 × 0.75) = 4 / 3.375
    assert eng.potencia_minima_desde_consumo(300, 40) == pytest.approx(4 / 3.375)
    with pytest.raises(ValueError):
        eng.potencia_minima_desde_consumo(0, 40)


def test_calcular_rango_paneles():
    rango = eng.calcular_rango_paneles(
        Voc=40, temp_min=-10, temp_max=70, coef_temp_voc=-0.3,
        startup_voltage=100, max_input_voltage=600,
    )
    assert rango == (4, 12)


def test_ajustar_modulos():
    assert eng.ajustar_modulos(0.5) == 1
    assert eng.ajustar_modulos(3) == 4      # impar -> par superior
    assert eng.ajustar_modulos(4) == 4


def test_calcular_autoconsumo_tres_opciones():
    res = eng.calcular_autoconsumo(panel=PANEL, inversor=INV)
    assert res["panel"]["potencia_w"] == 440
    assert res["inversor"]["wout_w"] == 5000

    opciones = res["opciones"]
    assert len(opciones) == 3
    por_target = {o["target"]: o for o in opciones}
    assert set(por_target) == {"min", "opt", "max"}

    # Config óptima: 7 en serie -> 14 paneles totales (2 MPPT × 1 entrada × 7).
    assert por_target["opt"]["paneles_serie"] == 7
    assert por_target["opt"]["paneles_total"] == 14

    assert por_target["min"]["paneles_total"] == 10
    assert por_target["max"]["paneles_total"] == 16

    # Ordenadas por ratio ascendente.
    ratios = [o["ratio_dc_ac"] for o in opciones]
    assert ratios == sorted(ratios)


def test_guard_corriente_panel_excede_inversor():
    panel_alta_corriente = {**PANEL, "Impp": 13}  # > inversor Impp 12
    with pytest.raises(ValueError):
        eng.calcular_autoconsumo(panel=panel_alta_corriente, inversor=INV)


def test_sin_soluciones_lanza_valueerror():
    inv_sobredimensionado = {**INV, "Wout": 50000}  # ratios siempre < 0.8
    with pytest.raises(ValueError):
        eng.calcular_autoconsumo(panel=PANEL, inversor=inv_sobredimensionado)


def test_panel_invalido_lanza_valueerror():
    with pytest.raises(ValueError):
        eng.calcular_autoconsumo(panel={**PANEL, "Potencia": 0}, inversor=INV)
