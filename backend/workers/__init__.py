"""
Paquete de WORKERS — procesos separados del API que ejecutan las tareas pesadas
encoladas en Redis (RQ).

NO importar este paquete desde `app/` (FastAPI). El flujo es de una sola dirección:
la capa de servicio del módulo encola en Redis (vía `app.queue`) y el worker, en un
proceso aparte, consume y ejecuta. Las tareas viven en `workers/tasks/`.

Ejecución (dev):  cd backend && python -m workers.worker
"""
