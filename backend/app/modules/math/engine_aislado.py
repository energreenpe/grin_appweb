"""
Motor de cálculo — Sistema Aislado (off-grid con baterías).

Portado de MATH/models/electrodomestico_model.py y MATH/utils/sistema_aislado_utils.py
como FUNCIONES PURAS: sin I/O, sin prints, sin estado. Reciben datos planos
(dicts/listas) y devuelven valores. Esto las hace testeables con pytest sin BD.

Cadena de dimensionamiento:
  consumo -> voltaje de sistema -> potencia pico -> nº paneles ->
  capacidad de baterías -> nº baterías -> potencia de inversor -> inversores sugeridos.

Convenciones de entrada:
  - cargas:  lista de dicts {cantidad: int, potencia_w: float, horas: float}
  - panel:   dict con al menos {"Potencia": W, "descripcion": str}        (specs del EquipoTecnico)
  - bateria: dict con al menos {"Vbat": V, "capacidad": Ah, "descripcion": str}
  - inversores: lista de dicts {"descripcion","marca","wout","Vbat"}
"""
import math
from typing import List, Dict, Optional, Tuple

# ── Constantes del modelo (tomadas del legacy, sin cambios de criterio) ───────
FACTOR_POTENCIA_AC = 1.25          # margen sobre la potencia máxima -> potencia AC
FACTOR_DISENO = 0.25               # fd: factor de diseño (pérdidas) en potencia pico
PERFORMANCE_RATIO = 0.75           # pr: performance ratio del sistema FV
EFICIENCIA_INVERSOR = 0.93         # eficiencia del inversor
FACTOR_SEGURIDAD_INVERSOR = 1.25   # factor de seguridad de la potencia del inversor

# Profundidad de descarga y eficiencia por tipo de batería.
DOD = {"Lead acid": 0.5, "Lithium": 0.8}
EFICIENCIA_BATERIA = {"Lead acid": 0.8, "Lithium": 0.95}


# ── Pasos individuales (funciones puras) ──────────────────────────────────────
def calcular_consumo(cargas: List[Dict]) -> Tuple[float, float, float]:
    """Devuelve (potencia_maxima_W, energia_diaria_Wh, potencia_ac_W)."""
    potencia_maxima = sum(c["cantidad"] * c["potencia_w"] for c in cargas)
    energia_diaria = sum(c["cantidad"] * c["potencia_w"] * c["horas"] for c in cargas)
    potencia_ac = potencia_maxima * FACTOR_POTENCIA_AC
    return potencia_maxima, energia_diaria, potencia_ac


def seleccionar_voltaje_sistema(energia_diaria: float) -> int:
    """Voltaje de banco (12/24/48 V) según el consumo diario (Wh)."""
    if energia_diaria < 1000:
        return 12
    elif energia_diaria < 2400:
        return 24
    return 48


def calcular_potencia_pico(
    energia_diaria: float, hsp: float,
    fd: float = FACTOR_DISENO, pr: float = PERFORMANCE_RATIO,
) -> float:
    """Potencia pico requerida (Wp)."""
    if hsp <= 0:
        raise ValueError("El HSP de la región debe ser mayor a 0.")
    return (energia_diaria * (1 + fd)) / (hsp * pr)


def calcular_numero_paneles(potencia_pico: float, panel: Dict) -> int:
    """Nº de paneles (redondeo hacia arriba, mínimo 1)."""
    potencia_panel = panel.get("Potencia", 0) or 0
    if potencia_panel <= 0:
        raise ValueError("El panel seleccionado no tiene una potencia válida.")
    return max(math.ceil(potencia_pico / potencia_panel), 1)


def corregir_potencia_solar(num_paneles: int, panel: Dict) -> float:
    """Potencia solar real instalada (W)."""
    return num_paneles * (panel.get("Potencia", 0) or 0)


def calcular_capacidad_baterias(
    energia_diaria: float, dias_autonomia: int,
    tipo_bateria: str, voltaje_sistema: int,
) -> float:
    """Capacidad requerida del banco de baterías (Ah)."""
    dod = DOD.get(tipo_bateria, 0.5)
    eficiencia = EFICIENCIA_BATERIA.get(tipo_bateria, 0.8)
    if voltaje_sistema <= 0:
        raise ValueError("El voltaje de sistema debe ser mayor a 0.")
    return (energia_diaria * dias_autonomia) / (dod * eficiencia * voltaje_sistema)


def calcular_numero_baterias(capacidad_ah: float, bateria: Dict, voltaje_sistema: int) -> int:
    """Nº de baterías = (en serie para el voltaje) × (strings en paralelo, ceil)."""
    capacidad_nominal = bateria.get("capacidad", 0) or 0
    volt_bateria = bateria.get("Vbat", 0) or 0
    if capacidad_nominal <= 0 or volt_bateria <= 0:
        raise ValueError("La batería seleccionada no tiene capacidad/voltaje válidos.")
    baterias_serie = max(1, voltaje_sistema // volt_bateria)
    strings_paralelo = math.ceil(capacidad_ah / capacidad_nominal)
    return baterias_serie * strings_paralelo


def calcular_potencia_inversor(
    potencia_ac: float,
    eficiencia_inversor: float = EFICIENCIA_INVERSOR,
    factor_seguridad: float = FACTOR_SEGURIDAD_INVERSOR,
) -> float:
    """Potencia requerida del inversor (W)."""
    return (potencia_ac / eficiencia_inversor) * factor_seguridad


def sugerir_inversores_en_paralelo(
    inversores: List[Dict], voltaje_banco: int, potencia_requerida: float,
) -> List[Dict]:
    """Para cada inversor del catálogo, cuántas unidades en paralelo cubren la
    potencia requerida. Reproduce la lógica del legacy (sin filtrar por voltaje de
    banco); omite entradas con wout<=0 o malformadas."""
    resultado: List[Dict] = []
    for inv in inversores:
        try:
            wout = float(inv["wout"])
            if wout <= 0:
                continue
            cantidad = math.ceil(potencia_requerida / wout) if potencia_requerida > 0 else 1
            resultado.append({
                "modelo": inv.get("descripcion", ""),
                "marca": inv.get("marca", ""),
                "wout": wout,
                "cantidad": cantidad,
                "potencia_total": cantidad * wout,
            })
        except (KeyError, TypeError, ValueError):
            continue
    return resultado


# ── Orquestador (función pura) ────────────────────────────────────────────────
def calcular_aislado(
    *,
    cargas: List[Dict],
    hsp: float,
    dias_autonomia: int,
    tipo_bateria: str,
    panel: Dict,
    bateria: Dict,
    inversores: List[Dict],
    voltaje_sistema: Optional[int] = None,
) -> Dict:
    """Ejecuta toda la cadena y devuelve el resultado estructurado.
    Lanza ValueError ante entradas inválidas (lo mapea el servicio a HTTP 400)."""
    if not cargas:
        raise ValueError("Debe ingresar al menos una carga/electrodoméstico.")
    if hsp is None or hsp <= 0:
        raise ValueError("HSP inválido para la región seleccionada.")

    potencia_maxima, energia_diaria, potencia_ac = calcular_consumo(cargas)
    if energia_diaria <= 0:
        raise ValueError("El consumo diario calculado es 0; revise cantidades, potencias y horas.")

    if voltaje_sistema is None:
        voltaje_sistema = seleccionar_voltaje_sistema(energia_diaria)

    potencia_pico = calcular_potencia_pico(energia_diaria, hsp)
    num_paneles = calcular_numero_paneles(potencia_pico, panel)
    potencia_solar = corregir_potencia_solar(num_paneles, panel)

    capacidad_ah = calcular_capacidad_baterias(energia_diaria, dias_autonomia, tipo_bateria, voltaje_sistema)
    num_baterias = calcular_numero_baterias(capacidad_ah, bateria, voltaje_sistema)

    potencia_inversor = calcular_potencia_inversor(potencia_ac)
    inversores_sugeridos = sugerir_inversores_en_paralelo(inversores, voltaje_sistema, potencia_inversor)

    return {
        "consumo": {
            "potencia_maxima_w": round(potencia_maxima, 2),
            "energia_diaria_wh": round(energia_diaria, 2),
            "potencia_ac_w": round(potencia_ac, 2),
        },
        "voltaje_sistema": voltaje_sistema,
        "hsp": round(hsp, 2),
        "potencia_pico_wp": round(potencia_pico, 2),
        "num_paneles": num_paneles,
        "potencia_solar_corregida_w": round(potencia_solar, 2),
        "panel": {
            "descripcion": panel.get("descripcion"),
            "potencia_w": panel.get("Potencia", 0) or 0,
        },
        "capacidad_ah": round(capacidad_ah, 2),
        "num_baterias": num_baterias,
        "bateria": {
            "descripcion": bateria.get("descripcion"),
            "vbat": bateria.get("Vbat", 0) or 0,
            "capacidad_ah": bateria.get("capacidad", 0) or 0,
        },
        "potencia_inversor_w": round(potencia_inversor, 2),
        "inversores_sugeridos": [
            {**inv, "wout": round(inv["wout"], 2), "potencia_total": round(inv["potencia_total"], 2)}
            for inv in inversores_sugeridos
        ],
    }
