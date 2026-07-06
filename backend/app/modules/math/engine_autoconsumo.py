"""
Motor de cálculo — Sistema Autoconsumo (grid-tie sin baterías).

Portado de MATH/models/config_model.py como FUNCIONES PURAS (sin I/O, sin prints).
Dado un panel y un inversor, calcula el rango de paneles en serie (corregido por
temperatura) y devuelve 3 configuraciones por ratio DC/AC:
  - mínima  (~0.8)
  - óptima  (~1.2)
  - máxima  (~1.4)
cada una con su nº total de paneles.

Convenciones de entrada (specs del EquipoTecnico):
  - panel:    {"Potencia": W, "Vmpp", "Impp", "Voc", "Isc", "descripcion", opc "CoefTempVoc"}
  - inversor: {"Wout": W, "Vmax", "Vstartup", "Vmpp_min", "Vmpp_max", "Impp", "Isc",
               "MPPT", "Input_MPPT", "Wp_max", "descripcion"}
"""
import math
from typing import List, Dict, Optional

COEF_TEMP_VOC_DEFAULT = -0.3      # %/°C (coeficiente de temperatura de Voc, negativo)
TEMP_MIN_DEFAULT = -10            # °C
TEMP_MAX_DEFAULT = 70            # °C
TARGET_RATIOS = {"min": 0.8, "opt": 1.2, "max": 1.4}

# Constantes del dimensionamiento por consumo (del legacy main_view.calcular).
HORAS_SOL_EQUIVALENTES = 4.5
PERFORMANCE_RATIO_CONSUMO = 0.75


def potencia_minima_desde_consumo(consumo_mensual_kwh: float, autarquia_pct: float) -> float:
    """Potencia mínima requerida (kW) a partir del consumo mensual y la autarquía.
    Fórmula del legacy: (consumo_mensual/30 × autarquía) / (HSE × PR)."""
    if consumo_mensual_kwh <= 0:
        raise ValueError("El consumo mensual debe ser mayor a 0.")
    consumo_diario = (consumo_mensual_kwh / 30) * (autarquia_pct / 100)
    return consumo_diario / (HORAS_SOL_EQUIVALENTES * PERFORMANCE_RATIO_CONSUMO)


def _a_kw(valor: float, umbral: float) -> float:
    """Convierte W→kW si el valor supera el umbral (los JSON traen W)."""
    return valor / 1000 if valor > umbral else valor


def calcular_rango_paneles(Voc, temp_min, temp_max, coef_temp_voc, startup_voltage, max_input_voltage):
    """Rango [min, max] de paneles en serie según la ventana de voltaje del inversor,
    corrigiendo Voc por temperatura (sube en frío, baja en calor)."""
    voc_max = Voc * (1 + (temp_min - 25) * (coef_temp_voc / 100))   # máximo voltaje (frío)
    voc_min = Voc * (1 + (temp_max - 25) * (coef_temp_voc / 100))   # mínimo voltaje (calor)
    if voc_min <= 0 or voc_max <= 0:
        raise ValueError("Voc corregido por temperatura inválido (revise el panel).")
    min_paneles = math.ceil(startup_voltage / (voc_min * 0.95))     # 5% margen
    max_paneles = math.floor(max_input_voltage / (voc_max * 1.05))  # 5% margen
    return max(1, min_paneles), max_paneles


def ajustar_modulos(num_modulos_inicial: float) -> int:
    """Ajusta el nº de módulos (redondeo a par superior)."""
    if num_modulos_inicial <= 1:
        return 1
    elif num_modulos_inicial % 2 != 0:
        return math.ceil(num_modulos_inicial / 2) * 2
    return int(num_modulos_inicial)


def _validar_configuracion(
    V_total, Vmpp_total, Impp_total, Isc_total, potencia_sistema,
    max_input_voltage, startup_voltage, mppt_min_voltage, mppt_max_voltage,
    max_isc_mppt, max_input_current_mppt, max_pv_power, output_power,
    is_max_config: bool = False,
) -> bool:
    """Valida una configuración contra los límites del inversor. Con is_max_config
    aplica márgenes más flexibles (búsqueda del máximo técnico)."""
    voltaje_margin = 1.02 if is_max_config else 1.05
    corriente_margin = 1.05 if is_max_config else 1.1
    potencia_margin = 1.02 if is_max_config else 1.05

    condiciones = [
        V_total <= max_input_voltage * voltaje_margin,
        Vmpp_total >= startup_voltage * 0.95,
        mppt_min_voltage <= Vmpp_total <= mppt_max_voltage * (1.05 if is_max_config else 1.03),
        Impp_total <= max_input_current_mppt * corriente_margin,
        Isc_total <= max_isc_mppt * corriente_margin,
        0.8 <= (potencia_sistema / output_power) <= (1.5 if is_max_config else 1.4),
        potencia_sistema <= max_pv_power * potencia_margin,
    ]
    return all(condiciones)


def verificar_condiciones(
    Voc, Vmpp, Isc, Impp, PV_power, num_paneles_min, num_paneles_max,
    num_mpp_trackers, max_inputs, max_input_voltage, startup_voltage,
    mppt_min_voltage, mppt_max_voltage, output_power, max_isc_mppt,
    max_input_current_mppt, max_pv_power,
) -> List[Dict]:
    """Busca las configuraciones mínima (0.8), óptima (1.2) y máxima (1.4) por
    ratio DC/AC dentro del rango de paneles en serie válido."""
    configs = {name: {"ratio_obj": r, "paneles_serie": None, "diff": float("inf")}
               for name, r in TARGET_RATIOS.items()}
    num_inputs = max_inputs

    for num_serie in range(num_paneles_min, num_paneles_max + 1):
        num_paneles = num_mpp_trackers * num_inputs * num_serie
        potencia = num_paneles * PV_power
        ratio = potencia / output_power

        valido_normal = _validar_configuracion(
            num_serie * Voc, num_serie * Vmpp, num_inputs * Impp, num_inputs * Isc,
            potencia, max_input_voltage, startup_voltage, mppt_min_voltage, mppt_max_voltage,
            max_isc_mppt, max_input_current_mppt, max_pv_power, output_power, is_max_config=False)
        valido_max = _validar_configuracion(
            num_serie * Voc, num_serie * Vmpp, num_inputs * Impp, num_inputs * Isc,
            potencia, max_input_voltage, startup_voltage, mppt_min_voltage, mppt_max_voltage,
            max_isc_mppt, max_input_current_mppt, max_pv_power, output_power, is_max_config=True)

        for name, config in configs.items():
            diff = abs(ratio - config["ratio_obj"])
            valido = valido_max if name == "max" else valido_normal
            if valido and diff < config["diff"]:
                config["diff"] = diff
                config["paneles_serie"] = num_serie
                config["potencia"] = potencia
                config["ratio"] = ratio

    soluciones = []
    for name, config in configs.items():
        if config["paneles_serie"] is not None:
            num_serie = config["paneles_serie"]
            num_paneles = num_mpp_trackers * num_inputs * num_serie
            soluciones.append({
                "target": name,
                "paneles_serie": num_serie,
                "mppt_trackers": num_mpp_trackers,
                "entradas_por_mppt": num_inputs,
                "paneles_total": num_paneles,
                "potencia_sistema_kW": round(config["potencia"], 2),
                "ratio_dc_ac": round(config["ratio"], 2),
            })

    soluciones.sort(key=lambda x: x["ratio_dc_ac"])

    # Asegurar que "max" sea el verdadero máximo técnico (búsqueda descendente).
    if soluciones and soluciones[-1]["target"] == "max":
        max_actual = soluciones[-1]["paneles_serie"]
        for num_serie in range(num_paneles_max, max_actual, -1):
            num_paneles = num_mpp_trackers * num_inputs * num_serie
            potencia = num_paneles * PV_power
            if _validar_configuracion(
                num_serie * Voc, num_serie * Vmpp, num_inputs * Impp, num_inputs * Isc,
                potencia, max_input_voltage, startup_voltage, mppt_min_voltage, mppt_max_voltage,
                max_isc_mppt, max_input_current_mppt, max_pv_power, output_power, is_max_config=True):
                soluciones[-1] = {
                    "target": "max",
                    "paneles_serie": num_serie,
                    "mppt_trackers": num_mpp_trackers,
                    "entradas_por_mppt": num_inputs,
                    "paneles_total": num_paneles,
                    "potencia_sistema_kW": round(potencia, 2),
                    "ratio_dc_ac": round(potencia / output_power, 2),
                }
                break

    return soluciones


def _mensaje_sin_soluciones(num_paneles_min, num_paneles_max, Vmpp, mppt_min_voltage, mppt_max_voltage):
    """Mensaje explicativo cuando no hay configuración válida."""
    partes = []
    vmpp_min_serie = max(1, num_paneles_min) * Vmpp
    if vmpp_min_serie < mppt_min_voltage:
        partes.append(f"se necesitan al menos {math.ceil(mppt_min_voltage / Vmpp)} paneles en serie para alcanzar {mppt_min_voltage}V")
    if vmpp_min_serie > mppt_max_voltage:
        partes.append(f"máximo {math.floor(mppt_max_voltage / Vmpp)} paneles en serie para no exceder {mppt_max_voltage}V")
    if num_paneles_min > num_paneles_max:
        partes.append(f"no hay rango válido (mínimo {num_paneles_min}, máximo {num_paneles_max})")
    detalle = "; ".join(partes) if partes else "el panel y el inversor no son compatibles con los parámetros dados"
    return f"No se encontraron configuraciones válidas: {detalle}."


def calcular_autoconsumo(
    *,
    panel: Dict,
    inversor: Dict,
    temp_min: float = TEMP_MIN_DEFAULT,
    temp_max: float = TEMP_MAX_DEFAULT,
    potencia_minima: Optional[float] = None,
) -> Dict:
    """Ejecuta el dimensionamiento grid-tie y devuelve las 3 configuraciones.
    Lanza ValueError ante incompatibilidades (lo mapea el servicio a HTTP 400)."""
    # Parámetros del panel (a kW si viene en W)
    P_PV_MAX = _a_kw(panel.get("Potencia", 0), 100)
    Vmpp = panel.get("Vmpp", 0)
    Impp = panel.get("Impp", 0)
    Voc = panel.get("Voc", 0)
    Isc = panel.get("Isc", 0)
    coef_temp_voc = panel.get("CoefTempVoc", COEF_TEMP_VOC_DEFAULT)
    if P_PV_MAX <= 0 or Voc <= 0 or Vmpp <= 0:
        raise ValueError("El panel seleccionado no tiene datos eléctricos válidos.")

    # Parámetros del inversor (a kW si viene en W)
    max_input_voltage = inversor.get("Vmax", 0)
    startup_voltage = inversor.get("Vstartup", 0)
    mppt_min_voltage = inversor.get("Vmpp_min", 0)
    mppt_max_voltage = inversor.get("Vmpp_max", 0)
    output_power = _a_kw(inversor.get("Wout", 0), 1000)
    max_isc_mppt = inversor.get("Isc", 0)
    max_input_current_mppt = inversor.get("Impp", 0)
    num_mpp_trackers = inversor.get("MPPT", 0)
    max_inputs = inversor.get("Input_MPPT", 0)
    max_pv_power = _a_kw(inversor.get("Wp_max", 0), 1000)
    if output_power <= 0 or num_mpp_trackers <= 0 or max_inputs <= 0:
        raise ValueError("El inversor seleccionado no tiene datos válidos (potencia/MPPT).")

    # Compatibilidad de corriente por entrada
    if Impp > max_input_current_mppt:
        raise ValueError(
            f"La corriente del panel (Impp {Impp}A) excede la del inversor ({max_input_current_mppt}A).")
    if Isc > max_isc_mppt:
        raise ValueError(
            f"La corriente de cortocircuito del panel (Isc {Isc}A) excede la del inversor ({max_isc_mppt}A).")

    num_paneles_min, num_paneles_max = calcular_rango_paneles(
        Voc, temp_min, temp_max, coef_temp_voc, startup_voltage, max_input_voltage)

    soluciones = verificar_condiciones(
        Voc, Vmpp, Isc, Impp, P_PV_MAX, num_paneles_min, num_paneles_max,
        num_mpp_trackers, max_inputs, max_input_voltage, startup_voltage,
        mppt_min_voltage, mppt_max_voltage, output_power, max_isc_mppt,
        max_input_current_mppt, max_pv_power)

    if not soluciones:
        raise ValueError(_mensaje_sin_soluciones(
            num_paneles_min, num_paneles_max, Vmpp, mppt_min_voltage, mppt_max_voltage))

    return {
        "panel": {
            "descripcion": panel.get("descripcion"),
            "potencia_w": panel.get("Potencia", 0),
        },
        "inversor": {
            "descripcion": inversor.get("descripcion"),
            "wout_w": inversor.get("Wout", 0),
        },
        "opciones": soluciones,
    }
