# 🛠️ Stack Tecnológico — GRIN Web Platform

> Documento de validación y definición del stack tecnológico para la migración del sistema GRIN desktop a arquitectura web moderna.  
> Fecha de definición: 2026-04-26 | Revisado: 2026-04-26  
> Proyecto: Energreen Perú E.I.R.L.

> [!IMPORTANT]
> **Estrategia de desarrollo**: Modular Monolith Incremental. Se construye **un módulo a la vez**, completamente aislado. Sin auth, sin dependencias cruzadas entre módulos hasta que cada uno esté consolidado. El primer módulo es **QUOTE**.

---

## ✅ Veredicto: El Stack es Correcto

Tras el análisis del código fuente real del repositorio `grin_app`, el stack propuesto **React + Vite / FastAPI / PostgreSQL** es **técnicamente correcto y el más adecuado** para este proyecto. A continuación se justifica módulo por módulo con evidencia directa del código.

---

## 🧠 Por qué FastAPI como Backend

| Argumento | Evidencia en el código actual |
|---|---|
| El código Python existente (modelos, utils, repository) migra directamente a FastAPI sin reescritura total | `electrodomestico_model.py`, `sistema_aislado_utils.py`, `repository.py` y `datasource.py` son Python puro sin dependencias de UI |
| La capa de datos ya está abstraída con `DataSource` (ABC) y `ProductRepository` | `QUOTE/datasource.py` + `QUOTE/repository.py` — listo para conectar con SQLAlchemy |
| `postgres_datasource.py` ya usa `psycopg2` y mapea objetos `Product` — la misma lógica pasa a SQLAlchemy + Pydantic | `QUOTE/postgres_datasource.py` |
| Los motores de cálculo (`calcular_consumo`, `calcular_potencia_pico`, `sugerir_inversores_en_paralelo`) son funciones puras que se convierten en endpoints REST sin modificación | `MATH/models/electrodomestico_model.py`, `MATH/utils/sistema_aislado_utils.py` |
| FastAPI genera documentación OpenAPI automática (Swagger UI), fundamental para exponer los cálculos al frontend React | — |
| Tipado con Pydantic es compatible con `TypedDict` y `@dataclass` ya usados en el sistema | `calculadora_controller.py` usa `TypedDict`; `datasource.py` usa `@dataclass` |

---

## ⚛️ Por qué React + Vite como Frontend

| Argumento | Evidencia / Justificación |
|---|---|
| Los wizard flows secuenciales del INSPECTOR (8 vistas encadenadas) se modelan perfectamente con React Router + estado de formulario | `INSPECTOR/views/`: 8 vistas (DatosCliente → TipoSistema → Techo → Fotos → CargasCríticas → ...) |
| La calculadora MATH con múltiples modos (Autoconsumo, Híbrido, Aislado) requiere manejo de estado complejo → React con Zustand o Context API | `calculadora_controller.py` actúa como state manager — React reemplaza esto nativamente |
| El cotizador QUOTE tiene tablas dinámicas, cálculos inline de monedas/IGV, y agrupaciones por partición → ideal para componentes React con estado reactivo | `QUOTE/interfaz.py` > 1000 líneas mezclando UI y lógica — React separa esto por diseño |
| Vite ofrece HMR (Hot Module Replacement) nativo — el proyecto actual simulaba hot reload con `watchdog` de forma precaria en QUOTE | `QUOTE/main.py` usa `watchdog` para simular reload |
| Escalabilidad modular: cada módulo GRIN (MATH, INSPECTOR, QUOTE) se convierte en un módulo/sección de la SPA independiente | — |

---

## 🗄️ Por qué PostgreSQL como Base de Datos

| Argumento | Evidencia en el código actual |
|---|---|
| El sistema ya tiene implementado `postgres_datasource.py` con queries reales (`SELECT`, `INSERT`) contra una BD `cotizaciones` | `QUOTE/postgres_datasource.py` |
| `db_config.py` ya define la estructura mínima de la tabla `productos` (id, categoria, nombre, descripcion, unidad, precio, moneda) | `QUOTE/db_config.py` |
| PostgreSQL soporta multi-usuario nativo — resuelve el problema crítico actual de `products.xlsx` y `counter.txt` compartidos | Problema: Data Splicing entre vendedores con archivos locales |
| PostgreSQL + SQLAlchemy permite migrar los modelos `Product`, `Visita`, `Cotizacion` a tablas relacionales con FK | Modelos ya definidos en Python con `@dataclass` y clases normales |

---

## 📐 Arquitectura del Stack Definida

```
┌─────────────────────────────────────────────────────────┐
│                 FRONTEND  (React + Vite)                 │
│                                                          │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌────────┐  │
│  │  MATH    │  │ INSPECTOR │  │  QUOTE   │  │  [+]   │  │
│  │ Module   │  │  Module   │  │  Module  │  │ Future │  │
│  └──────────┘  └───────────┘  └──────────┘  └────────┘  │
│                                                          │
│   React Router v6 · Zustand · TanStack Query · Axios    │
│   Shadcn/ui · Tailwind CSS · Recharts · React Hook Form  │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST (JSON)
                       │ OpenAPI / Swagger UI
┌──────────────────────▼──────────────────────────────────┐
│                  BACKEND  (FastAPI)                      │
│                                                          │
│   /api/quote/*     → [ACTIVO] Cotizaciones y productos  │
│   /api/math/*      → [PENDIENTE] Cálculo solar          │
│   /api/inspector/* → [PENDIENTE] Visitas técnicas       │
│                                                          │
│   SQLAlchemy ORM · Alembic · Pydantic v2                │
│   WeasyPrint (PDF) · python-dotenv (.env)               │
└──────────────────────┬──────────────────────────────────┘
                       │ psycopg2-binary
┌──────────────────────▼──────────────────────────────────┐
│               BASE DE DATOS  (PostgreSQL 16)             │
│                                                          │
│  [ACTIVO] productos · cotizaciones                      │
│            items_cotizacion · empresa_config            │
│  [PENDIENTE] equipos_tecnicos · visitas · ...           │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Stack Completo por Capa

### Frontend

| Tecnología | Versión | Rol |
|---|---|---|
| **React** | 18.x | Framework UI principal |
| **Vite** | 5.x | Build tool y dev server (HMR nativo) |
| **React Router** | v6 | Enrutamiento SPA modular |
| **Zustand** | 4.x | Manejo de estado global ligero |
| **TanStack Query** | v5 | Fetching, caching y sincronización de datos |
| **Axios** | 1.x | Cliente HTTP |
| **Shadcn/ui** | Latest | Componentes UI accesibles y customizables |
| **Tailwind CSS** | v3 | Utilidades de estilos |
| **Recharts** | 2.x | Gráficos para resultados de cálculo solar |
| **React Hook Form** | 7.x | Formularios complejos (INSPECTOR wizard, QUOTE) |
| **Zod** | 3.x | Validación de esquemas de formulario |

### Backend

| Tecnología | Versión | Estado | Rol |
|---|---|---|---|
| **FastAPI** | 0.111.x | ✅ Fase 1 | Framework API REST principal |
| **Pydantic** | v2 | ✅ Fase 1 | Validación y serialización de datos |
| **SQLAlchemy** | 2.x | ✅ Fase 1 | ORM para PostgreSQL |
| **Alembic** | 1.x | ✅ Fase 1 | Migraciones de base de datos |
| **psycopg2-binary** | 2.9.x | ✅ Fase 1 | Driver PostgreSQL |
| **python-dotenv** | 1.x | ✅ Fase 1 | Variables de entorno (reemplaza credenciales hardcodeadas) |
| **WeasyPrint** | 62.x | ✅ Fase 1 (QUOTE) | Generación de PDFs desde templates HTML/CSS |
| **Uvicorn** | 0.29.x | ✅ Fase 1 | Servidor ASGI para desarrollo |
| **python-multipart** | Latest | ⏳ Fase 3 (INSPECTOR) | Soporte para upload de fotos |
| **python-jose** | 3.x | ⏳ Futuro | JWT — solo cuando se implemente auth |
| **passlib[bcrypt]** | 1.7.x | ⏳ Futuro | Hash de contraseñas — solo con auth |

### Base de Datos

| Tecnología | Versión | Rol |
|---|---|---|
| **PostgreSQL** | 16.x | Base de datos relacional principal |
| **pgAdmin 4** | Latest | Administración de BD en desarrollo |

### DevOps / Herramientas

| Tecnología | Rol |
|---|---|
| **Git** | Control de versiones (ya activo en el repo) |
| **dotenv / `.env`** | Variables de entorno (reemplaza credenciales hardcodeadas en `db_config.py`) |
| **ESLint + Prettier** | Calidad de código frontend |
| **pytest** | Tests unitarios del backend (especialmente lógica MATH) |

---

## 🗂️ Estructura de Carpetas del Proyecto Web

> [!NOTE]
> La estructura sigue el patrón **Modular Monolith**: cada módulo es una carpeta autónoma con sus propios modelos, schemas, servicios y rutas. No hay imports cruzados entre módulos. Se agregan carpetas de módulo a medida que se construyen.

```
grin_web/
├── frontend/                        # React + Vite
│   ├── src/
│   │   ├── modules/
│   │   │   ├── quote/               # ✅ MÓDULO ACTIVO
│   │   │   │   ├── pages/
│   │   │   │   │   ├── QuoteList.jsx       # Lista de cotizaciones
│   │   │   │   │   └── QuoteEditor.jsx     # Editor de cotización
│   │   │   │   ├── components/
│   │   │   │   │   ├── ProductSearch.jsx   # Buscador de productos
│   │   │   │   │   ├── QuoteTable.jsx      # Tabla de ítems
│   │   │   │   │   ├── QuoteHeader.jsx     # Cabecera (cliente, tipo cambio)
│   │   │   │   │   └── QuoteSummary.jsx    # Totales IGV/moneda
│   │   │   │   ├── store/
│   │   │   │   │   └── quoteStore.js       # Zustand store (estado del editor)
│   │   │   │   └── api/
│   │   │   │       └── quoteApi.js         # Llamadas Axios al backend
│   │   │   │
│   │   │   ├── math/                # ⏳ Pendiente Módulo 2
│   │   │   └── inspector/           # ⏳ Pendiente Módulo 3
│   │   │
│   │   ├── components/              # Componentes compartidos (Layout, Navbar, Sidebar)
│   │   └── lib/
│   │       └── api.js               # Instancia Axios base (baseURL, headers)
│   └── package.json
│
├── backend/                         # FastAPI
│   ├── app/
│   │   ├── main.py                  # App FastAPI — incluye routers activos
│   │   ├── db.py                    # Engine + SessionLocal + Base declarativa
│   │   ├── config.py                # Settings desde .env (python-dotenv)
│   │   │
│   │   └── modules/
│   │       ├── quote/               # ✅ MÓDULO ACTIVO — completamente aislado
│   │       │   ├── __init__.py
│   │       │   ├── router.py        # APIRouter prefix=/api/quote
│   │       │   ├── models.py        # SQLAlchemy: Producto, Cotizacion, ItemCotizacion, EmpresaConfig
│   │       │   ├── schemas.py       # Pydantic: request/response schemas
│   │       │   ├── service.py       # Lógica: IGV, monedas, correlativo, particiones
│   │       │   └── pdf.py           # WeasyPrint: generación PDF cotización
│   │       │
│   │       ├── math/                # ⏳ Pendiente Módulo 2
│   │       └── inspector/           # ⏳ Pendiente Módulo 3
│   │
│   ├── alembic/                     # Migraciones (solo tablas del módulo activo)
│   ├── .env                         # Variables de entorno (NO en git)
│   ├── .env.example                 # Plantilla pública
│   └── requirements.txt
│
└── docs/
    ├── stack_tecnologico.md
    └── analisis_sistema_grin.md
```

---

## 🚀 Orden de Construcción — Modular Incremental

> [!IMPORTANT]
> Cada módulo se construye completo (backend + frontend + BD) antes de pasar al siguiente. **No hay auth hasta que la lógica de negocio esté estabilizada.** Agregar un módulo nuevo = agregar una carpeta en `modules/`, un router en `main.py`, y una migración Alembic. Nada más.

| Módulo | Estado | BD involucrada | Restricciones |
|---|---|---|---|
| 💰 **QUOTE** | 🟢 **ACTIVO — Empezamos aquí** | `productos`, `cotizaciones`, `items_cotizacion`, `empresa_config` | Sin auth. Sin relación con otros módulos. |
| 📐 **MATH** | ⏳ Pendiente (Módulo 2) | `equipos_tecnicos`, `regiones` | No se toca hasta QUOTE completo. |
| 📋 **INSPECTOR** | ⏳ Pendiente (Módulo 3) | `visitas`, `cargas_visita` | No se toca hasta MATH completo. |
| 🔮 **Futuros** | ⏳ Sin definir | A definir | Dashboard, CRM, Reportes, etc. |

### Regla de expansión modular

Cuando se agrega un módulo nuevo, **los únicos cambios globales permitidos son**:
1. Crear `backend/app/modules/<nuevo_modulo>/` con su propio `router.py`, `models.py`, `schemas.py`, `service.py`.
2. Agregar `app.include_router(nuevo_router)` en `backend/app/main.py`.
3. Crear una migración Alembic nueva con las tablas del módulo.
4. Crear `frontend/src/modules/<nuevo_modulo>/` con sus páginas y componentes.
5. Agregar la ruta en `React Router` en `App.jsx`.

Nada más. Cero cambios en módulos existentes.

---

> **Conclusión**: El stack React + Vite / FastAPI / PostgreSQL con arquitectura Modular Monolith Incremental es la elección óptima. Maximiza la reutilización del código Python existente, resuelve todos los problemas de arquitectura identificados, y permite construir módulo a módulo sin deuda técnica acumulada.
