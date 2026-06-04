# 📊 Análisis Técnico del Sistema GRIN Actual

> Resultado del análisis de ingeniería inversa aplicado al repositorio `grin_app`.  
> Base para la migración a arquitectura web: FastAPI + React + Vite + PostgreSQL.  
> Fecha de análisis: 2026-04-26 | Analista: Antigravity AI

---

## 1. 📦 Estructura del Proyecto

```
grin_app/
├── main_interface.py          # Lanzador principal (CustomTkinter)
├── assets/                    # Logos e iconos generales
├── MATH/                      # Calculadora de dimensionamiento solar
│   ├── main.py                # Entry point PyQt5
│   ├── controllers/
│   │   ├── calculadora_controller.py   # State manager + router de vistas
│   │   └── config_controller.py
│   ├── models/
│   │   ├── electrodomestico_model.py   # 293 líneas — modelo + 12 métodos de cálculo
│   │   └── config_model.py             # 23 KB — configuración solar por región/tipo
│   ├── utils/
│   │   └── sistema_aislado_utils.py    # 196 líneas — funciones puras de cálculo
│   ├── views/                          # 12 archivos de UI PyQt5
│   │   ├── main_view.py                # 67 KB — vista principal Autoconsumo/Híbrido
│   │   ├── automatico_view.py          # 41 KB
│   │   ├── mostrar_equipos.py          # 19 KB
│   │   └── temp_cotizacion.json        # ⚠️ Archivo de acoplamiento entre MATH y QUOTE
│   ├── data_tecnica/
│   │   ├── inversores_aislados.json
│   │   ├── inversores_autoconsumo.json  # 12 KB — catálogo de inversores
│   │   ├── baterias.json
│   │   └── paneles.json
│   └── data/
│       └── electrodomesticos.json      # Estado en disco de la lista de cargas
│
├── INSPECTOR/                          # Módulo de visitas técnicas
│   ├── main.py                         # ListApp — router tipo wizard
│   ├── models/
│   │   └── visita.py                   # Modelo Visita con to_dict()
│   ├── views/                          # 8 formularios secuenciales
│   │   ├── datos_cliente_view.py
│   │   ├── tipo_cliente_view.py
│   │   ├── tipo_sistema_view.py
│   │   ├── conexion_red_view.py
│   │   ├── tipo_techo_view.py
│   │   ├── captura_fotos_view.py
│   │   ├── recibo_luz_view.py
│   │   └── cargas_criticas_view.py
│   └── utils/
│       └── pdf_generator.py            # Genera PDF técnico de visita
│
└── QUOTE/                              # Cotizador / Facturador
    ├── main.py                         # Wrapper + watchdog hot-reload
    ├── interfaz.py                     # 58 KB — monolito UI + lógica de negocio
    ├── cotizaciones.py                 # 21 KB — generación PDF con ReportLab
    ├── datasource.py                   # Abstracción DataSource (ABC) + Product @dataclass
    ├── repository.py                   # ProductRepository (patrón Repository)
    ├── excel_datasource.py             # DataSource sobre products.xlsx
    ├── postgres_datasource.py          # DataSource sobre PostgreSQL (psycopg2)
    ├── db_config.py                    # ⚠️ Credenciales hardcodeadas
    ├── estilos.py                      # Definición de estilos Tkinter
    ├── btnagregar.py                   # Componente botón agregar producto
    ├── solicitar_detalles.py           # Dialog para detalles de ítem
    ├── txtword.py                      # Exportación a Word
    ├── counter.txt                     # ⚠️ Correlativo de cotización en archivo plano
    ├── empresa.txt                     # Datos de empresa (nombre, RUC, etc.)
    └── products.xlsx                   # ⚠️ Catálogo de productos en Excel local
```

---

## 2. 🧩 Módulos del Sistema

### A. Lanzador Principal (`main_interface.py`)

- **Propósito**: Menú de entrada tipo "App Launcher" con botones por módulo.
- **Tecnología UI**: `CustomTkinter`
- **Mecanismo**: Lanza cada módulo con `subprocess.Popen(["python", "main.py"], cwd="./NOMBRE_MODULO")`.
- **Estado compartido**: ❌ Ninguno. Los módulos arrancan como procesos OS independientes.
- **Equivalente web**: El Dashboard principal de la SPA con navegación a cada módulo.

### B. Módulo MATH

- **Propósito**: Calculadora y dimensionamiento de sistemas fotovoltaicos.
- **Tecnología UI**: `PyQt5`
- **Patrón**: MVC — `CalculadoraController` orquesta vistas y modelos.
- **Modos de sistema**: Autoconsumo, Híbrido, Aislado (On-grid pendiente: existe `ongrid_view.py`)
- **State manager actual**: `CalculadoraController` mantiene referencias a vistas activas y datos de sesión en atributos de instancia.

**Modelos clave:**

```python
# MATH/models/electrodomestico_model.py — 12 métodos de cálculo
class ElectrodomesticoModel:
    def calcular_consumo() -> Tuple[float, float, float]
    def seleccionar_voltaje_sistema(energia_diaria) -> int  # 12/24/48V
    def calcular_potencia_pico(hsp_promedio, fd=0.25, pr=0.75) -> float
    def calcular_numero_paneles(potencia_pico, panel_seleccionado) -> int
    def calcular_capacidad_baterias(dias_autonomia, tipo_bateria, voltaje_sistema) -> float
    def calcular_numero_baterias(capacidad_ah, bateria_seleccionada, voltaje_sistema) -> int
    def calcular_potencia_inversor(eficiencia=0.93, factor_seguridad=1.25) -> float
```

```python
# MATH/utils/sistema_aislado_utils.py — funciones puras
def cargar_paneles(path) -> list
def cargar_baterias(path) -> list
def cargar_inversores(path) -> list
def filtrar_baterias(baterias, tipo, voltaje) -> list
def filtrar_inversores(inversores, voltaje_banco, potencia_minima) -> list
def sugerir_inversores_en_paralelo(inversores, voltaje_banco, potencia_requerida) -> list
def obtener_hsp(regiones, region_nombre, tipo_hsp) -> float
```

**Datos técnicos en JSON:**
- `paneles.json` — potencia, marca, dimensiones
- `baterias.json` — capacidad Ah, Vbat, tipo (Lead Acid / Lithium)
- `inversores_aislados.json` — wout, Vbat, marca, descripción
- `inversores_autoconsumo.json` — especificaciones para sistemas grid-tie

### C. Módulo INSPECTOR

- **Propósito**: Wizard de captura de datos técnicos para visitas de campo.
- **Tecnología UI**: `CustomTkinter`
- **Patrón**: Wizard flow con callbacks. `ListApp` en `main.py` enruta entre las 8 vistas usando un dict de callbacks.

**Modelo `Visita`:**

```python
# INSPECTOR/models/visita.py
class Visita:
    tipo_cliente: str          # "Persona" o "Empresa"
    nombre: str
    documento: str             # DNI (8 dígitos) o RUC (11 dígitos)
    telefono: str
    direccion: str
    lat: Optional[float]       # GPS
    lng: Optional[float]       # GPS
    tipo_sistema: str          # Aislado, Autoconsumo, Híbrido
    conexion_red: str          # "Sí" / "No"
    recibo_ruta: Optional[str] # Ruta local del archivo de recibo
    tipo_techo: str
    fotos_techo: str           # Rutas separadas por "|"
    fotos_interior: str        # Rutas separadas por "|"
    obs_techo: str
    obs_interior: str
    cargas_aislado: List[Dict] # Lista de electrodomésticos para aislado
    fecha: str                 # ISO datetime string
    
    def to_dict() -> dict      # ← migra directamente a Pydantic BaseModel
```

**Flujo de las 8 vistas:**
```
DatosClienteView → TipoClienteView → TipoSistemaView → ConexionRedView
    → TipoTechoView → CapturaFotosView → ReciboLuzView → CargasCriticasView → [PDF]
```

### D. Módulo QUOTE

- **Propósito**: Explorador de inventario y generador de propuestas/cotizaciones PDF.
- **Tecnología UI**: `Tkinter` estándar + `ttkbootstrap`
- **Patrón**: Monolítico — `interfaz.py` (58 KB) mezcla vistas, lógica de negocio, acceso a datos y configuración de empresa.
- **Hot reload**: `watchdog` en `main.py` detecta cambios en `interfaz.py` y reinicia el proceso.

**Abstracción de datos (bien diseñada):**

```python
# QUOTE/datasource.py
@dataclass
class Product:
    id: str
    categoria: str
    nombre: str
    description: str
    marca: str
    unit: str
    unit_price: float
    moneda: str = "PEN"
    qty: int = 1
    partition: str = "Principal"
    
    @property
    def subtotal(self) -> float:
        return self.unit_price * self.qty

class DataSource(ABC):          # ← Interfaz abstracta intercambiable
    def read_products(search) -> List[Product]
    def get_product(product_id) -> Optional[Product]
    def get_next_id() -> int
    def add(product: dict) -> None

class ProductRepository:        # ← Patrón Repository sobre DataSource
    def search(query) -> List[Product]
    def get(product_id) -> Optional[Product]
    def add(product: dict)
```

**Implementaciones de DataSource:**
- `ExcelDataSource` → lee/escribe `products.xlsx` con `pandas`
- `PostgresDataSource` → opera contra tabla `productos` en PostgreSQL (**ya funcional**)

**Tabla `productos` ya definida en PostgreSQL:**
```sql
SELECT id, categoria, nombre, descripcion, unidad, precio, moneda
FROM productos
```

**Lógica de negocio en cotizaciones:**
- Conversión bimoneda (PEN / USD) con tipo de cambio configurable en runtime
- Cálculo inline de IGV (18%) por partición y total
- Márgenes de utilidad configurables por cotización
- Agrupación de ítems por `partition` (Principal, Adicional, etc.)
- Incrustación de JSON en metadatos del PDF para re-importación futura

---

## 3. 🔗 Integraciones Detectadas

### Integración MATH → QUOTE (Única y Frágil)

```
MATH/views/temp_cotizacion.json  ←(escribe)── resultado_view.py
QUOTE/interfaz.py ──(lee)──► cargar_json_temp() → hardcodea "../MATH/views/temp_cotizacion.json"
```

**Problema**: Acoplamiento por sistema de archivos. Race conditions si los procesos corren en paralelo. Ruta hardcodeada relativa.

**Solución en web**: El resultado de MATH se envía como JSON al frontend, que lo pasa como payload al endpoint de creación de cotización en QUOTE. Sin archivos intermedios.

### Datos Técnicos (JSON → BD)

Los archivos `data_tecnica/*.json` son el catálogo de equipos solares. En la web migran a tablas en PostgreSQL:

| Archivo actual | Tabla destino |
|---|---|
| `paneles.json` | `equipos_tecnicos` (tipo='panel') |
| `baterias.json` | `equipos_tecnicos` (tipo='bateria') |
| `inversores_aislados.json` | `equipos_tecnicos` (tipo='inversor_aislado') |
| `inversores_autoconsumo.json` | `equipos_tecnicos` (tipo='inversor_autoconsumo') |

---

## 4. 💾 Manejo de Datos Actual

| Tipo | Archivo | Módulo | Estado | Problema |
|---|---|---|---|---|
| JSON en disco | `electrodomesticos.json` | MATH | Persistencia de cargas del usuario | Se sobreescribe con cada sesión, sin historial |
| JSON en disco | `data_tecnica/*.json` | MATH | Catálogo de equipos solares | No editable sin tocar el código |
| JSON temporal | `views/temp_cotizacion.json` | MATH→QUOTE | Comunicación entre módulos | Race condition, ruta hardcodeada |
| Excel | `products.xlsx` | QUOTE | Catálogo de productos | No multi-usuario, requiere pandas |
| PostgreSQL | `cotizaciones` DB | QUOTE | Catálogo alternativo (incubado) | Credenciales expuestas en texto plano |
| TXT plano | `counter.txt` | QUOTE | Correlativo de cotización | Se divide si múltiples vendedores trabajan en paralelo |
| TXT plano | `empresa.txt` | QUOTE | Configuración de empresa | Sin validación, sin historial |
| JSON en PDF | metadatos PDF | QUOTE | Estado de cotización embebido | Expone márgenes y costos origen al destinatario |

---

## 5. ⚠️ Problemas Detectados en el Código

### Críticos (Seguridad)

```python
# QUOTE/db_config.py — CREDENCIALES EN TEXTO PLANO
def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="cotizaciones",
        user="postgres",
        password="javier123",   # ← EXPUESTO EN REPO
        port=5432
    )
```
**Solución**: Variables de entorno con `python-dotenv` + `.env` en `.gitignore`.

### Graves (Arquitectura)

| Problema | Localización | Impacto |
|---|---|---|
| Monolito UI+Lógica+Datos | `QUOTE/interfaz.py` (58 KB, ~1000+ líneas) | Imposible de mantener y testear |
| Acoplamiento por filesystem | `QUOTE/interfaz.py::cargar_json_temp()` | Race conditions, ruta hardcodeada |
| `counter.txt` para IDs | `QUOTE/counter.txt` | Data corruption en multi-usuario |
| 4 frameworks UI distintos | CustomTkinter + Tkinter + ttkbootstrap + PyQt5 | Dependencias masivas, inconsistencia visual |
| PDF render por coordenadas | `QUOTE/cotizaciones.py` ReportLab canvas | Inmantenible para cambios de template |
| Debug prints en producción | `calculadora_controller.py`, `sistema_aislado_utils.py` | Ruido en logs, datos sensibles expuestos |

### Moderados (Escalabilidad)

| Problema | Localización | Impacto |
|---|---|---|
| JSON embebido en PDFs con márgenes y precios origen | `cotizaciones.py` | Expone información comercial sensible si el PDF es analizado |
| `electrodomesticos.json` como estado de sesión | `MATH/data/` | Sin historial, sin multi-usuario |
| Datos de empresa en `.txt` | `QUOTE/empresa.txt` | Sin validación ni historial de cambios |

---

## 6. 🧱 Componentes Reutilizables para Migración

Estos son los componentes del sistema actual con **alto valor de reutilización directa** en FastAPI:

| Componente actual | Ruta en grin_app | Ruta destino en FastAPI | Esfuerzo |
|---|---|---|---|
| Lógica de dimensionamiento (12 métodos) | `MATH/models/electrodomestico_model.py` | `backend/app/services/math_service.py` | 🟢 Bajo — copiar + wrappear en endpoint |
| Funciones de filtrado/cálculo aislado | `MATH/utils/sistema_aislado_utils.py` | `backend/app/services/math_service.py` | 🟢 Bajo — funciones puras, copiar directo |
| Catálogo técnico (JSON) | `MATH/data_tecnica/*.json` | Seed en tabla `equipos_tecnicos` PostgreSQL | 🟡 Medio — script de seed |
| Modelo `Product` + abstracción `DataSource` | `QUOTE/datasource.py` | `backend/app/schemas/product.py` + SQLAlchemy model | 🟢 Bajo — `@dataclass` → `BaseModel` Pydantic |
| `ProductRepository` | `QUOTE/repository.py` | `backend/app/services/product_service.py` | 🟢 Bajo — adaptar a SQLAlchemy session |
| `PostgresDataSource` con queries ya escritas | `QUOTE/postgres_datasource.py` | Migrar queries a SQLAlchemy ORM | 🟡 Medio |
| Modelo `Visita` con `to_dict()` | `INSPECTOR/models/visita.py` | `backend/app/schemas/visita.py` (Pydantic) | 🟢 Bajo — 1:1 con Pydantic BaseModel |
| Lógica de extracción JSON de PDFs | `QUOTE/cotizaciones.py::extraer_json_de_pdf()` | `backend/app/services/pdf_service.py` | 🟡 Medio — adaptar para WeasyPrint |
| Catálogo de potencias de electrodomésticos | `MATH/models/electrodomestico_model.py::POTENCIAS` | Tabla `electrodomesticos_catalogo` o constante en servicio | 🟢 Bajo |

---

## 7. 📊 Complejidad por Módulo

```
ALTA COMPLEJIDAD LÓGICA (Requieren tests unitarios extensos antes de migrar):

  MATH — Motores de Cálculo
  ├── calcular_potencia_pico()        → depende de HSP + fd + pr
  ├── calcular_numero_baterias()      → múltiplos de serie, ceil logic
  ├── sugerir_inversores_en_paralelo() → iteración sobre JSON técnico
  └── seleccionar_voltaje_sistema()   → condicional 12/24/48V según Wh/día

  QUOTE — Motor de Cotización  
  ├── Conversión bimoneda PEN/USD inline
  ├── Cálculo de IGV por partición y total
  ├── Márgenes de utilidad por ítem/global
  └── Agrupación de ítems por partition

BAJA COMPLEJIDAD LÓGICA (Alta complejidad UI actual, simple como API REST):

  INSPECTOR — Formulario Wizard
  └── 8 pasos secuenciales → React multi-step form + POST /visitas

  QUOTE — CRUD de Productos
  └── Búsqueda + agregar al carrito → React table + GET/POST /productos
```

---

## 8. 🗺️ Mapa de Migración por Módulo

```
grin_app (Desktop)              →    grin_web (Web)
─────────────────────────────────────────────────────

MATH/
  calculadora_controller.py     →    React: Zustand store (math)
  electrodomestico_model.py     →    FastAPI: MathService
  sistema_aislado_utils.py      →    FastAPI: MathService (funciones puras)
  views/*.py                    →    React: modules/math/pages/
  data_tecnica/*.json           →    PostgreSQL: tabla equipos_tecnicos (seed)

INSPECTOR/
  main.py (ListApp wizard)      →    React: modules/inspector/pages/ (multi-step)
  models/visita.py              →    FastAPI: Pydantic VisitaSchema + SQLAlchemy Visita
  views/*.py                    →    React: components de formulario por paso
  utils/pdf_generator.py        →    FastAPI: PdfService (WeasyPrint)

QUOTE/
  datasource.py (Product)       →    FastAPI: Pydantic ProductSchema
  repository.py                 →    FastAPI: ProductService (SQLAlchemy)
  postgres_datasource.py        →    FastAPI: CRUD sobre ORM (queries reutilizadas)
  cotizaciones.py               →    FastAPI: QuoteService + PdfService
  interfaz.py                   →    React: modules/quote/ (descomposición en componentes)
  
main_interface.py               →    React: Layout principal + React Router
db_config.py (credenciales)     →    backend/.env + python-dotenv
counter.txt                     →    PostgreSQL: SERIAL / SEQUENCE autoincremental
empresa.txt                     →    PostgreSQL: tabla empresa_config
products.xlsx                   →    PostgreSQL: tabla productos (importación inicial)
```

---

> **Estado del sistema**: Sistema de escritorio funcional con lógica de negocio sólida pero arquitectura monolítica, acoplada por sistema de archivos e inescalable para multi-usuario. Todo el capital de lógica de negocio (cálculos solares, modelos, abstracción de datos) es recuperable y migrará directamente a la nueva arquitectura web con esfuerzo moderado-bajo.
