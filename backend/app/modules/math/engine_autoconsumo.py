"""
Motor de cálculo — Sistema Autoconsumo (grid-tie sin baterías).

Portado de MATH/models/config_model.py como funciones puras. Dado un panel y un
inversor, calcula el rango de paneles en serie (corregido por temperatura) y
devuelve 3 configuraciones por ratio DC/AC: mínima (~0.8), óptima (~1.2) y
máxima (~1.4), cada una con su nº total de paneles.

Se implementa en el Entregable #7.
"""
