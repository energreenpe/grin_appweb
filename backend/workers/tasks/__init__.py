"""
Tareas ejecutables por el worker RQ.

Cada tarea es una función de nivel de módulo (RQ guarda su ruta de importación y el
worker la re-importa). Mantener las tareas como envoltorios delgados: la lógica de
dominio pesada vive en el módulo correspondiente (p. ej. `app.modules.list.converter`)
y la tarea solo orquesta (estado, storage, errores, cleanup).
"""
