# 📐 Integración del Módulo LIST en grin_web — Arquitectura para Producción

> Documento de diseño y decisiones. Define cómo integrar el módulo **LIST** (editor visual
> de documentos: subir DOCX/XLSX/PDF → estampar campos y overlays → exportar PDF) dentro de
> grin_web de forma segura, escalable y lista para producción multiusuario.
>
> Fecha: 2026-06-20 | Proyecto: Energreen Perú E.I.R.L. | Relacionado: `stack_tecnologico.md`

---

## Resumen ejecutivo

LIST es un editor visual de documentos **funcional pero construido como app standalone síncrona**.
Su núcleo (estampado de PDF con coordenadas en *points*, editor React con undo/redo) es **sólido y
reutilizable**. Su problema crítico para producción: **la tarea pesada (conversión DOCX/XLSX→PDF con
LibreOffice/MS-Office) se ejecuta dentro del request de FastAPI, bloqueando el event loop**. Además trae
piezas que **chocan** con grin_web (su propio `main.py`/`config`, plantillas en disco como JSON,
dependencias Windows-only, react-router v7, tema dark).

Integración correcta = **3 movimientos**:
1. **Absorber** LIST como un módulo más (`app/modules/list/`) respetando la regla modular.
2. **Extraer** la conversión LibreOffice a una **capa async nueva** (`workers/` + Redis) — infraestructura
   net-new que grin_web aún no tiene y que esta es la primera feature que la justifica.
3. **Reescribir acoplamientos**: storage → `app/storage.py`; plantillas → PostgreSQL; frontend →
   convenciones de grin_web (axios, router v6, Layout, Sidebar, Zustand).

---

## 1. Diagnóstico del módulo LIST actual

### 1.1 Anatomía real

| Pieza | Archivo | Qué hace | Naturaleza |
|---|---|---|---|
| App propia | `LIST/backend/app/main.py` | FastAPI propio, CORS, monta `list_router` | Duplica infra de grin_web |
| Config propia | `LIST/backend/app/core/config.py` | Clase `Settings` plana (no pydantic-settings), dirs, límites, CORS hardcoded | Duplica `app/config.py` |
| Router | `…/modules/list/router.py` | `upload`, `pdf/{filename}`, `export`, `templates`, `health` | Mezcla orquestación + I/O |
| **Conversión** | `…/modules/list/converter.py` | DOCX/XLSX→PDF: 1º **MS Office COM** (`docx2pdf`/`win32com`), 2º fallback **`soffice --headless`** | **TAREA PESADA, bloqueante, OS-level** |
| Estampado | `…/modules/list/pdf_editor.py` | PyMuPDF: overlays + `insert_textbox` | CPU-bound, rápido (C), síncrono en endpoint async |
| Limpieza | `…/modules/list/temp_storage.py` | Borra archivos > 30 min, se dispara como `background_task` en cada request | Hacky |
| Schemas | `…/modules/list/schemas.py` | Pydantic v2 (sin `Literal`/constraints fuertes) | Compatible, perfectible |
| Frontend | `LIST/frontend/src/modules/list/` | React + `react-pdf`/`pdfjs-dist`, estado `useState`+history, `fetch` vía proxy Vite, router v7, tema dark/glass | Estructura `modules/list/` correcta; acoplamientos a reescribir |

### 1.2 ¿Síncrono o asíncrono?

**100% síncrono y bloqueante.** El punto grave:

```
upload_file (async def)
   └─ await file.read()
   └─ convert_to_pdf(...)   ← subprocess.run(soffice) / win32com COM,
                              ejecuta DENTRO del event loop, SIN run_in_executor
   └─ return pdf_url
```

`convert_to_pdf` es código bloqueante síncrono dentro de un `async def`: mientras LibreOffice tarda
(1–10 s, o el timeout de 60 s), **ese worker de Uvicorn no atiende a nadie más**. Con varios usuarios
subiendo Word/Excel a la vez, el API se congela. Esto es exactamente lo que la restricción
arquitectónica del proyecto prohíbe.

### 1.3 Problemas para producción (priorizados)

1. 🔴 **Event loop bloqueado** por la conversión.
2. 🔴 **`docx2pdf`/`win32com` (MS Office COM) es Windows-only y requiere Office instalado** → no
   desplegable en contenedor Linux. Solo sirve como ruta de dev en Windows.
3. 🔴 **LibreOffice tiene lock de instancia única por perfil de usuario**: dos `soffice` concurrentes con
   el mismo perfil colisionan. El código no aísla el perfil → falla bajo concurrencia.
4. 🟠 **Path traversal**: `serve_pdf` y `get_template` construyen rutas con valores del cliente
   (`UPLOAD_DIR / filename`, `TEMPLATE_DIR / f"{template_id}.json"`). Un `..` escapa del directorio.
5. 🟠 **Plantillas como archivos JSON en disco** → no sobreviven a despliegues multi-instancia ni a
   filesystem efímero (contenedores).
6. 🟠 **PyMuPDF (`fitz`) es AGPL-3.0** → para un SaaS comercial cerrado es una decisión de licencia.
7. 🟡 Limpieza de temporales como `background_task` en cada request; retención 30 min en código pero la
   UI dice "24 horas" → inconsistencia.
8. 🟡 Sin DB, sin tests, config y CORS duplicados.

---

## 2. Compatibilidad con grin_web

### 2.1 Reutilizable casi tal cual ✅

- **Estructura de carpetas ya calza**: `app/modules/list/` (backend) y `frontend/src/modules/list/`.
- **Núcleo de estampado** (`apply_overlays_and_fields`) y **matemática de coordenadas HTML↔PDF points**
  (`utils/coords.js`): diseño correcto, agnóstico de UI, portable.
- **Editor visual** (Canvas, Draggable, Toolbar, paneles, undo/redo): lógica pura React.
- **`schemas.py`**: compatible con Pydantic v2; endurecer al estándar grin_web (`Literal`, `Field(ge/le)`,
  `field_validator` para páginas y colores 0–1).

### 2.2 Debe refactorizarse 🔧

| Pieza LIST | Convención grin_web | Acción |
|---|---|---|
| Router con `prefix="/api/list"` | `APIRouter()` sin prefix; prefix en `main.py` | Quitar prefix del router |
| `app/core/config.py` propio | `app/config.py` (pydantic-settings) | Eliminar; mover límites a config |
| I/O a dirs propios | `app/storage.py` (anti-traversal, S3-ready) | Todo el I/O pasa por `storage.py` |
| `temp_storage` en cada request | — | Job programado de limpieza |
| Plantillas en JSON | PostgreSQL + Alembic + `models.py` | Tabla `list_plantillas` |
| Frontend `fetch` + proxy Vite | axios `api`/`fileUrl` de `lib/api.js` | `api/listApi.js` |
| `react-router-dom` v7 | grin_web usa v6 | Alinear a v6 |
| Tema dark/glass | Tema claro, `--primary-color #62B989` | Reconciliar estilos |
| Estado `useState`+history | Zustand | Migrar store a Zustand |

### 2.3 Qué rompería la arquitectura ❌

- Ejecutar `soffice`/COM dentro del proceso FastAPI → viola "tareas pesadas NO en FastAPI".
- `main.py`/`core/` propios de LIST duplican app/CORS/settings → se descartan.
- Plantillas JSON + dirs auto-gestionados saltan `storage.py` y PostgreSQL.
- **Bueno**: LIST no importa otros módulos → encaja en "cero imports cruzados".

> ⚠️ **Nota honesta**: grin_web hoy es 100% síncrono y genera PDFs (QUOTE `xhtml2pdf`, INSPECTOR
> `reportlab`) dentro del request — y está bien, porque son ligeros, Python puro, acotados. La regla de
> colas aplica a la tarea **pesada, OS-level y no acotada** que trae LIST (LibreOffice sobre uploads
> arbitrarios). Integrar LIST = agregar a grin_web su **primera infraestructura asíncrona**. Se hace como
> **infra compartida** (`app/queue.py` + `workers/`) para que futuras tareas pesadas la reutilicen.

---

## 3. Propuesta de integración (módulo)

El módulo **define la capacidad**; el worker la **ejecuta**; la cola es la **frontera**. El router nunca
llama a la conversión directamente, solo **encola**.

```
backend/app/modules/list/
├── __init__.py
├── router.py        # APIRouter() SIN prefix. Endpoints finos: validan, delegan a service.
├── models.py        # SQLAlchemy 2.0: ListPlantilla [+ opcional ListJob para historial]
├── schemas.py       # Pydantic v2 endurecido + JobStatusOut
├── service.py       # Orquesta: valida → storage.save_bytes → encola job → consulta estado → CRUD plantillas
├── converter.py     # Lógica PURA de conversión (comando LibreOffice / cliente Gotenberg). Importable por worker.
└── pdf_stamp.py     # Lógica PURA de estampado (PyMuPDF o reportlab+pypdf). Importable por worker.
```

**Reparto**: `router.py` traduce HTTP y responde `202 {job_id}`; `service.py` es el caso de uso (storage +
encolar + estado + CRUD); `converter.py`/`pdf_stamp.py` son **funciones puras** (sin FastAPI ni Redis),
testeables, **invocadas por el worker**.

> Decisión clave: la lógica pesada **vive en el módulo** (dominio testeable) pero **se ejecuta en el
> worker** (contexto de ejecución). La restricción es sobre *dónde se ejecuta*, no *dónde vive el código*.

---

## 4. Arquitectura async (crítico)

### 4.1 Stack de cola — recomendación: **RQ (Redis Queue)**

RQ sobre Celery: solo Redis, curva mínima ("una función → un job"), encaja con "monolito modular simple".
Aporta de fábrica `job.get_status()`, `job.result`, registries y reintentos con backoff. Migrar a Celery
solo si en el futuro se necesitan workflows complejos / beats / fan-out masivo.

### 4.2 Estructura `backend/workers/`

```
backend/workers/
├── __init__.py
├── worker.py            # Bootstrap RQ: conecta a Redis, escucha colas ["conversion","export"]
├── settings.py          # REDIS_URL, nombres de colas, timeouts, concurrencia
└── tasks/
    ├── __init__.py
    ├── convert.py        # convert_document(rel_in) -> rel_pdf : importa modules.list.converter
    └── export.py         # stamp_document(pdf_rel, fields, overlays) -> rel_out : importa modules.list.pdf_stamp
```

Las tareas son envoltorios delgados de ciclo de vida (estado, storage, errores, cleanup); la lógica de
transformación la importan del módulo.

### 4.3 Conexión con Redis (infra compartida)

`backend/app/queue.py` (NUEVO, infra compartida, no del módulo): `get_redis()` desde `settings.redis_url`
y `get_queue(name)` factory de `rq.Queue`. Usado por `service.py` (encolar) y `worker.py` (consumir).
`app/config.py` gana `redis_url`.

### 4.4 Invocar LibreOffice correctamente desde el worker

**(a) Perfil aislado por job** (resuelve el lock de instancia única):

```bash
soffice --headless --invisible --nodefault --nologo \
        --nofirststartwizard --norestore \
        -env:UserInstallation=file:///tmp/lo_<job_uuid> \
        --convert-to pdf --outdir <outdir> <input>
```

Cada job usa un `UserInstallation` único y lo borra al terminar. Sin esto, dos conversiones simultáneas se
pisan.

**(b) Aislamiento de proceso**: worker como contenedor separado del API, con LibreOffice + fuentes. La
imagen del API queda liviana. Correr non-root, sin red, con `timeout` y captura de `stderr`.

**(c) Sin COM en producción**: `docx2pdf`/`win32com` solo como atajo opcional de dev en Windows; la ruta
canónica es LibreOffice headless (o Gotenberg, §7).

### 4.5 Concurrencia y escalado (multiusuario)

- **Pool de workers**: N procesos RQ, 1 job a la vez cada uno. Escalar agregando workers. LibreOffice es
  CPU+RAM intensivo → workers ≈ núcleos, limitar concurrencia para no provocar OOM.
- **Handoff de archivos**: mientras API y worker estén en el mismo host, disco local (vía `storage.py`)
  sirve. ⚠️ Cuando vivan en hosts distintos, el disco local deja de funcionar → migrar `storage.py` a
  **S3/R2** (para eso es el único punto de cambio).
- **Reintentos**: backoff acotado; fallos de LibreOffice suelen ser deterministas (archivo corrupto) →
  pocos reintentos y marcar `failed`.
- **Ciclo de vida**: `incoming` (TTL corto) → `pdf convertido` (TTL ~24h) → `output` (TTL corto). Reemplaza
  `temp_storage` por un job programado (rq-scheduler / cron-container).

---

## 5. Estructura final sugerida

```
backend/
├── app/
│   ├── main.py                 # + include_router(list_router, prefix="/api/list")  ← único cambio global
│   ├── config.py               # + redis_url, + límites de LIST
│   ├── db.py
│   ├── storage.py              # REUSADO para todo el I/O de LIST
│   ├── ratelimit.py            # REUSADO en /upload y /export
│   ├── queue.py                # NEW · infra compartida: Redis + factory de colas
│   └── modules/list/           # router, models, schemas, service, converter, pdf_stamp
├── workers/                    # NEW · worker.py, settings.py, tasks/{convert,export}.py
├── alembic/versions/xxxx_add_list_tables.py   # NEW · list_plantillas [+ list_jobs]
├── requirements.txt            # + redis, rq  (pymupdf | reportlab+pypdf ya están)
├── Dockerfile.api              # imagen liviana (sin LibreOffice)
├── Dockerfile.worker           # NEW · imagen con LibreOffice + fuentes
└── docker-compose.yml          # api + worker + redis [+ gotenberg opcional]

frontend/src/
├── App.jsx                     # + <Route path="/list"> dentro de <Layout>
├── components/Sidebar.jsx      # + entrada "LIST"
├── lib/api.js                  # REUSADO (axios + fileUrl)
└── modules/list/
    ├── pages/ListEditor.jsx    # adaptado (sin App/main propios)
    ├── components/             # Canvas, Draggable*, Toolbar, paneles (conservados)
    ├── store/listStore.js      # NEW · Zustand
    ├── api/listApi.js          # NEW · sobre lib/api.js
    └── utils/coords.js         # conservado
```

Cambios globales = los de la "regla de expansión modular" **+ una excepción documentada**: la primera
infra async (`app/queue.py`, `workers/`, Redis, Dockerfile.worker). Cero cambios en QUOTE/MATH/INSPECTOR.

---

## 6. Flujo completo real (con concurrencia)

### Conversión (Word/Excel → PDF) — ruta pesada

```
Usuario sube contrato.docx
   ▼
Frontend ── POST /api/list/upload (multipart) ──► FastAPI (rápido, no bloquea):
                                                    1. valida ext+tamaño (+RateLimiter)
                                                    2. storage.save_bytes → uploads/list/incoming/<uuid>.docx
                                                    3. service.encolar("conversion", convert_document, rel_in)
   ◄──────────────── 202 { job_id, "queued" } ──────┘
   (si suben .pdf → atajo síncrono, devuelve pdf_url ya, sin conversión)
   ▼
Frontend polling ── GET /api/list/jobs/{job_id} ──►  Redis(cola) → Worker RQ (contenedor separado):
                                                       - convert_document(rel_in)
                                                       - soffice --headless -env:UserInstallation=… (o Gotenberg)
                                                       - storage.save → uploads/list/pdf/<uuid>.pdf
                                                       - job.result={pdf_url}, status=finished
   ▼ (finished)
Frontend carga PDF (react-pdf) ← GET /api/list/pdf/<uuid>.pdf → editor de overlays/campos
```

### Exportación (estampado) — ruta ligera, mismo patrón

```
POST /api/list/export {pdf_name, fields[], overlays[]} → FastAPI valida → encola "export" → 202 {job_id}
Worker: stamp_document (PyMuPDF / reportlab+pypdf) → storage uploads/list/output/<uuid>.pdf → finished
Frontend: poll → finished → GET /api/list/output/<uuid>.pdf → descarga
```

> Estampado de docs pequeños = milisegundos; en PDFs de 100+ páginas puede tardar. Encolarlo uniformiza el
> patrón y protege el API. Alternativa v1: síncrono pero en threadpool (`run_in_executor`). **Recomendado:
> encolar.**

---

## 7. Mejores decisiones técnicas

### 7.1 Motor de conversión — DECISIÓN (2026-06-20): **Gotenberg en dev y prod**

Gotenberg es un contenedor stateless que **ya incluye LibreOffice** (y Chromium). El worker no
ejecuta `soffice`: hace un `POST` HTTP a Gotenberg y recibe el PDF. Por tanto **no se instala
LibreOffice en ningún host**; LibreOffice corre dentro del contenedor de Gotenberg.

Se adopta Gotenberg **desde el entregable #3, en dev y en prod** (no solo prod). Como el proyecto ya
usa Docker, levantar un servicio `gotenberg` en `docker-compose` da paridad dev=prod y elimina por
completo la gestión de subprocess/lock de instancia/`win32com`.

| Opción | Pro | Contra | Veredicto |
|---|---|---|---|
| **Gotenberg** (contenedor con LibreOffice/Chromium, API HTTP) | `converter.py` = cliente HTTP simple; gestiona lifecycle, lock, aislamiento y concurrencia; dev=prod | Un contenedor más | ✅ **ELEGIDO (dev + prod)** |
| **unoserver** / **`soffice` subprocess** | Sin contenedor extra | Cold-start, aislar perfil y lock manualmente, líos en Windows | ❌ Descartado |
| **MS Office COM** (`win32com`/`docx2pdf`) | Máxima fidelidad | Windows + Office, no contenedor | ❌ Descartado |

**Implicancia de diseño**: `converter.py` es un **cliente HTTP a Gotenberg** (`POST
/forms/libreoffice/convert`, vía `httpx`), no un wrapper de subprocess. Sin `-env:UserInstallation`,
sin `win32com`, sin detección de `soffice`. Config: `GOTENBERG_URL` (default `http://localhost:3000`).

### 7.2 Estampado — decisión de licencia: **PyMuPDF (AGPL) vs reportlab+pypdf**

PyMuPDF (`fitz`) es **AGPL-3.0** (obliga a publicar fuente o comprar licencia comercial).
- **SaaS comercial/cerrado** → reimplementar con **`reportlab` + `pypdf`** (ya están en `requirements.txt`):
  overlay con reportlab + merge con pypdf. Cero dependencia nueva, cero AGPL. ← **recomendado**.
- **Si aceptan AGPL** → PyMuPDF es más simple y robusto (`insert_textbox` con auto-wrap, guardado
  incremental).

### 7.3 Plantillas → **PostgreSQL** (tabla `list_plantillas`)

`id, nombre, pdf_name/hash, fields JSONB, overlays JSONB, created_at` [+ FK opcional a `usuarios` de
`shared/`]. Sobrevive a contenedores efímeros y multi-instancia; consultable.

### 7.4 Estado de jobs → RQ nativo (v1); `list_jobs` en PG opcional para historial/auditoría.

### 7.5 Seguridad (producción multiusuario)

- Validación: extensión + tamaño (ya) + **magic-bytes/MIME** + **ClamAV** antes de convertir.
- LibreOffice: flags sin macros, non-root, contenedor aislado sin red.
- **Arreglar path traversal** en `serve_pdf`/`get_template` vía `storage.resolve` + validar `template_id`
  como UUID.
- **RateLimiter** en `/upload` y `/export`.

---

## 8. Checklist de cambios para "listo para producción"

1. Mover lógica pura a `converter.py`/`pdf_stamp.py`; router/service finos.
2. Quitar prefix del router; registrarlo en `main.py`.
3. Eliminar `main.py`/`core/config.py` propios; usar `app/config.py` + `app/storage.py`.
4. `app/queue.py` (Redis) + `backend/workers/` (RQ) + `Dockerfile.worker` + Redis en compose.
5. Conversión y export **encolados**; LibreOffice con perfil aislado (o Gotenberg).
6. Plantillas → tabla PostgreSQL + migración Alembic.
7. Reemplazar `temp_storage`-en-cada-request por job de limpieza programado.
8. Arreglar path traversal + magic-bytes + RateLimiter.
9. Frontend: descartar `App.jsx`/`main.jsx` propios; ruta en `App.jsx` dentro de `<Layout>`; entrada en
   `Sidebar`; `listApi.js` sobre axios; alinear router v6; store Zustand; reconciliar tema; agregar
   `react-pdf`/`pdfjs-dist` a `package.json`.
10. Decidir licencia de estampado (PyMuPDF AGPL vs reportlab+pypdf).
11. Tests pytest de `converter`/`pdf_stamp` (paridad con MATH).

---

## 9. Plan de entregables (incremental, cada uno verificable)

> Regla de trabajo: antes de ejecutar cada entregable se presenta un resumen de lo que incluye, para
> aprobación.

| # | Entregable | Resultado |
|---|---|---|
| 1 | **Infra async compartida** | `app/queue.py` + `backend/workers/` (esqueleto RQ) + Redis en compose + deps. Sin tocar el módulo. Health del worker verificable. |
| 2 | **Andamiaje del módulo + BD** | `app/modules/list/` (router/models/schemas/service vacíos-mínimos) + migración Alembic `list_plantillas` + registro en `main.py`. |
| 3 | **Conversión async (Gotenberg)** | servicio `gotenberg` en compose + `converter.py` (cliente HTTP) + task `convert` + `POST /upload` (encola) + `GET /jobs/{id}` + `GET /pdf/{name}` por `storage`. Tests. |
| 4 | **Estampado async** | `pdf_stamp.py` (decidir lib) + task `export` + `POST /export` + `GET /output/{name}`. Tests. |
| 5 | **Plantillas en PG** | CRUD `list_plantillas` (service + endpoints). Tests. |
| 6 | **Limpieza + seguridad** | Job programado de limpieza, magic-bytes, RateLimiter, fixes de traversal. |
| 7 | **Frontend integrado** | Página en `App.jsx`+`Layout`+`Sidebar`, `listApi.js`, store Zustand, polling de jobs, tema reconciliado, deps. |
| 8 | **Hardening prod** | Dockerfiles api/worker, compose de prod (api+worker+redis+gotenberg), docs de despliegue. |

> **Estado (2026-06-20): los 8 entregables están implementados y verificados.** Backend con
> 74 tests verdes + verificaciones e2e en vivo; frontend integrado (build OK + render en navegador);
> imágenes Docker de api/worker construidas.

---

## 10. Despliegue (producción)

**Componentes:** API (FastAPI) · Worker (RQ) · Redis · Gotenberg · PostgreSQL (externo/gestionado) ·
Frontend (build estático de Vite servido por tu hosting/CDN o un Nginx).

**Backend con Docker Compose:**

```bash
cd grin_web
# .env junto a docker-compose.prod.yml:
#   DATABASE_URL=postgresql://user:pass@host:5432/bd_grin
#   CORS_ORIGINS=https://tu-frontend.com
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

- `Dockerfile.api` es **slim y NO trae LibreOffice** (la conversión la hace Gotenberg). Aplica
  `alembic upgrade head` al arrancar (en multi-réplica, mover la migración a un job aparte).
- `api` y `worker` comparten el volumen `uploads_data` montado en `/app/uploads` (handoff de archivos).
  Cuando se escale a **varios hosts**, este volumen local deja de servir → migrar `app/storage.py` a
  **S3/R2** (único punto de cambio).
- El worker en Linux usa el `Worker` con `fork` de RQ (el código detecta el SO).

**Frontend:** `cd frontend && npm run build` → servir `dist/` con apuntando `lib/api.js::SERVER_BASE`
al dominio del API (o vía reverse-proxy `/api`).

**Endurecimiento adicional recomendado (no montado en dev):**
- **ClamAV**: servicio comentado en `docker-compose.prod.yml`. Activarlo = descomentar + integrar el
  escaneo en `service.procesar_upload` antes de encolar. Escanea uploads contra malware.
- TLS/HTTPS en el borde (reverse proxy), límites de tamaño en el proxy, y `CORS_ORIGINS` restringido al
  dominio real del frontend.
