"""
scheduler.py — Motor de cronograma del módulo PLANNER (funciones PURAS).

Calcula fechas en **días laborables** (lunes–viernes) descontando feriados, y
propaga el cronograma según dependencias.

v1: solo dependencias **FS (Finish-to-Start) + lag**, el tipo dominante. Las
dependencias SS/FF/SF se persisten pero todavía no condicionan fechas (extensión
posterior). Todo aquí es sin BD ni I/O para poder testear con solidez.
"""
from collections import deque
from datetime import date, timedelta
from typing import Iterable


def es_dia_laborable(fecha: date, feriados: set[date]) -> bool:
    """True si `fecha` es lunes–viernes y no es feriado."""
    return fecha.weekday() < 5 and fecha not in feriados


def siguiente_laborable(fecha: date, feriados: set[date]) -> date:
    """Menor día laborable >= `fecha`."""
    f = fecha
    while not es_dia_laborable(f, feriados):
        f += timedelta(days=1)
    return f


def avanzar_laborables(fecha: date, n: int, feriados: set[date]) -> date:
    """Avanza `n` días laborables desde `fecha` (n>0 adelante, n<0 atrás).

    n == 0 normaliza al siguiente día laborable (>= fecha).
    """
    if n == 0:
        return siguiente_laborable(fecha, feriados)
    paso = 1 if n > 0 else -1
    restantes = abs(n)
    actual = fecha
    while restantes > 0:
        actual += timedelta(days=paso)
        if es_dia_laborable(actual, feriados):
            restantes -= 1
    return actual


def fecha_fin_laborable(inicio: date, duracion_dias: int, feriados: set[date]) -> date:
    """Fecha de fin dado un inicio y una duración en días laborables.

    duracion<=1 ⇒ fin == inicio (un día de trabajo, o hito). El inicio se
    normaliza al siguiente día laborable.
    """
    inicio = siguiente_laborable(inicio, feriados)
    if duracion_dias <= 1:
        return inicio
    return avanzar_laborables(inicio, duracion_dias - 1, feriados)


def contar_laborables(desde: date, hasta: date, feriados: set[date]) -> int:
    """Cantidad de días laborables en el rango [desde, hasta] (inclusivo)."""
    if hasta < desde:
        return 0
    n = 0
    f = desde
    while f <= hasta:
        if es_dia_laborable(f, feriados):
            n += 1
        f += timedelta(days=1)
    return n


def recalcular_cronograma(actividades: list[dict], dependencias: list[dict],
                          feriados: Iterable[date]) -> dict[int, dict]:
    """Propaga fechas del Gantt según dependencias FS+lag.

    `actividades`: dicts con {id, fecha_inicio_plan, duracion_dias, es_hito}.
    `dependencias`: dicts con {actividad_id, depende_de_id, tipo, lag_dias}.
        actividad_id = sucesora; depende_de_id = predecesora.
    Devuelve {id: {"fecha_inicio_plan": date|None, "fecha_fin_plan": date|None}}.

    Cada actividad arranca en el máximo entre su inicio propio (si lo tiene) y
    el inicio impuesto por sus predecesoras FS: fin_pred + (1 + lag) laborables.
    """
    feriados = set(feriados)
    acts = {a["id"]: a for a in actividades}
    preds: dict[int, list[tuple[int, int]]] = {aid: [] for aid in acts}
    adj: dict[int, list[int]] = {aid: [] for aid in acts}
    indeg: dict[int, int] = {aid: 0 for aid in acts}

    for d in dependencias:
        if str(getattr(d["tipo"], "value", d["tipo"])) != "FS":
            continue  # v1: solo FS condiciona fechas
        succ, pred = d["actividad_id"], d["depende_de_id"]
        if succ in acts and pred in acts:
            preds[succ].append((pred, d.get("lag_dias") or 0))
            adj[pred].append(succ)
            indeg[succ] += 1

    # Orden topológico (Kahn). Si hay ciclo, los restantes se procesan al final
    # sin restricción de predecesora (degradación segura, sin colgarse).
    cola = deque([a for a in acts if indeg[a] == 0])
    orden: list[int] = []
    while cola:
        n = cola.popleft()
        orden.append(n)
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                cola.append(m)
    if len(orden) < len(acts):
        orden += [a for a in acts if a not in orden]

    resultado: dict[int, dict] = {}
    for aid in orden:
        a = acts[aid]
        base = a.get("fecha_inicio_plan")
        candidatos: list[date] = []
        if base:
            candidatos.append(siguiente_laborable(base, feriados))
        for pred_id, lag in preds[aid]:
            fin_pred = resultado.get(pred_id, {}).get("fecha_fin_plan")
            if fin_pred:
                candidatos.append(avanzar_laborables(fin_pred, 1 + lag, feriados))
        inicio = max(candidatos) if candidatos else None
        if inicio is None:
            resultado[aid] = {"fecha_inicio_plan": None, "fecha_fin_plan": None}
            continue
        dur = 0 if a.get("es_hito") else (a.get("duracion_dias") or 1)
        fin = inicio if dur <= 0 else fecha_fin_laborable(inicio, dur, feriados)
        resultado[aid] = {"fecha_inicio_plan": inicio, "fecha_fin_plan": fin}
    return resultado
