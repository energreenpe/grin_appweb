"""
Módulo PLANNER — gestión de proyectos fotovoltaicos: cronograma Gantt
(jerárquico, con dependencias y feriados), cuadrillas y personal, asistencia,
evidencia fotográfica, Curva S y reportes PDF (Cliente / Oficina).

Aislado como el resto de módulos (cero imports cruzados con quote/math/
inspector/list). Las referencias a otros módulos (quote_id, inspector_visita_id)
son soft-references Integer sin FK.
"""
