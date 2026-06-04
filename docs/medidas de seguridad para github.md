# Medidas de Seguridad para GitHub — Proyecto GRIN Web

> **Propósito:** Este documento explica qué archivos son sensibles o innecesarios en el repositorio, la estrategia de `.gitignore` a implementar, y las medidas de seguridad recomendadas antes de hacer el primer `push` público o privado.

---

## ¿Un `.gitignore` o varios?

**Respuesta corta: uno general en la raíz de `grin_web/` es suficiente y más ordenado.**

### La situación actual

| Ubicación | Estado | Observación |
|---|---|---|
| `grin_app/.gitignore` | ✅ Existe | Solo ignora `__pycache__/` y `*.pyc`. Muy incompleto. |
| `grin_web/frontend/.gitignore` | ✅ Existe | Generado por Vite. Correcto para el frontend, pero está mal ubicado si el repo raíz es `grin_web/`. |
| `grin_web/.gitignore` | ❌ No existe | **Aquí debe estar el `.gitignore` principal.** |

### La regla de Git

Git aplica el `.gitignore` **de forma relativa** desde donde se encuentra el archivo hacia abajo. Si el repositorio que vas a subir es la carpeta `grin_web/`, entonces el `.gitignore` debe estar en la raíz de `grin_web/` y cubrir todo — tanto el `backend/` como el `frontend/`.

Tener el `.gitignore` solo dentro de `frontend/` hace que las reglas **no apliquen** al backend ni a la raíz del proyecto.

**Lo que haremos:**
1. Crear un `.gitignore` raíz en `grin_web/` que cubra todo el proyecto.
2. Eliminar el `.gitignore` de `frontend/` (sus reglas ya estarán incluidas en el raíz) — **o dejarlo como respaldo**, no causa conflicto pero es redundante.

---

## Archivos sensibles detectados en el proyecto

### 🔴 CRÍTICOS — Nunca deben subirse a Git

| Archivo / Carpeta | Motivo |
|---|---|
| `backend/.env` | Contiene credenciales reales de PostgreSQL (`usuario:contraseña`) |
| `backend/alembic.ini` | Contiene la URL de conexión a la BD con credenciales en texto plano |

> ⚠️ Si estos archivos ya fueron incluidos en un commit anterior, las credenciales quedan expuestas en el historial de Git aunque luego se eliminen. En ese caso se debe cambiar la contraseña de PostgreSQL.

### 🟠 INNECESARIOS — Generados automáticamente, no deben subirse

| Archivo / Carpeta | Motivo |
|---|---|
| `backend/venv/` | Entorno virtual de Python. Pesa mucho y cada colaborador lo genera con `pip install -r requirements.txt` |
| `backend/__pycache__/` | Archivos compilados de Python. Se regeneran solos |
| `backend/app/__pycache__/` | Igual |
| `backend/alembic/__pycache__/` | Igual |
| `backend/alembic/versions/__pycache__/` | Igual |
| `frontend/node_modules/` | Dependencias de Node.js. Pesa cientos de MB. Se regeneran con `npm install` |
| `frontend/dist/` | Build de producción. Se regenera con `npm run build` |
| `frontend/dist-ssr/` | Build SSR. Igual |

### 🟡 DE SISTEMA / EDITOR — Deben ignorarse

| Archivo / Carpeta | Motivo |
|---|---|
| `.DS_Store` | Metadatos de macOS. No tienen utilidad en el proyecto |
| `Thumbs.db` | Metadatos de Windows |
| `.vscode/` | Configuración personal del editor VS Code (excepto extensiones recomendadas) |
| `.idea/` | Configuración de JetBrains (PyCharm, WebStorm) |
| `*.suo`, `*.sln`, `*.njsproj` | Archivos de Visual Studio |
| `*.log` | Logs de npm, yarn, etc. |

### 🟢 LO QUE SÍ DEBE SUBIRSE (no ignorar)

| Archivo / Carpeta | Motivo |
|---|---|
| `backend/.env.example` | Plantilla sin credenciales reales. Indispensable para los colaboradores |
| `backend/requirements.txt` | Lista de dependencias de Python |
| `backend/alembic/versions/*.py` | Scripts de migración de la BD. Son código fuente |
| `backend/alembic/env.py` | Configuración de Alembic (sin credenciales si lee del `.env`) |
| `backend/assets/` | Logos e imágenes del backend (logo empresa, logos bancos) |
| `frontend/src/` | Todo el código fuente React |
| `frontend/public/` | Archivos públicos estáticos |
| `frontend/package.json` | Lista de dependencias de Node.js |
| `frontend/package-lock.json` | Lock file para reproducibilidad exacta |
| `docs/` | Toda la documentación del proyecto |

---

## Problema detectado en `alembic.ini`

El archivo `alembic.ini` tiene las credenciales de la base de datos escritas directamente:

```ini
# ⚠️ ESTO NO DEBE SUBIRSE TAL CUAL:
sqlalchemy.url = postgresql://postgres:javier123@localhost:5432/BD_GRIN
```

**Solución:** Modificar `alembic/env.py` para que lea la URL desde el archivo `.env`, y luego limpiar `alembic.ini` dejando la URL como placeholder:

```ini
# ✅ ESTO SÍ ES SEGURO:
sqlalchemy.url = driver://user:pass@localhost/dbname
```

Esto se incluirá en el `.gitignore` como medida inmediata, y se documentará como mejora pendiente.

---

## Lo que se va a crear

### Archivo: `grin_web/.gitignore` (nuevo, en la raíz del repo)

Este archivo cubrirá **todo el proyecto** — backend, frontend y raíz:

```
# ============================================================
# GRIN Web — .gitignore
# ============================================================

# ─── SEGURIDAD: Variables de entorno ─────────────────────────
.env
.env.local
.env.*.local

# ─── PYTHON: Entorno virtual y caché ────────────────────────
venv/
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python

# ─── NODE.JS: Dependencias y builds ─────────────────────────
node_modules/
dist/
dist-ssr/

# ─── LOGS ────────────────────────────────────────────────────
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# ─── EDITORES / SISTEMA OPERATIVO ────────────────────────────
.vscode/*
!.vscode/extensions.json
.idea/
.DS_Store
Thumbs.db
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
*.local

# ─── BASE DE DATOS (solo backups locales) ────────────────────
*.sql
*.backup
*.dump
```

> **Nota sobre `*.sql`:** Si en algún momento se decide versionar scripts de inicialización dentro del repo (por ejemplo en una carpeta `docs/db/`), se puede excepcionar con `!docs/db/*.sql`.

---

## Verificación antes del primer `push`

Antes de subir el proyecto, ejecutar este comando en la terminal dentro de `grin_web/` para verificar qué archivos detectaría Git:

```bash
git status
```

Y para ver explícitamente qué está siendo ignorado:

```bash
git check-ignore -v backend/.env
git check-ignore -v backend/venv
git check-ignore -v frontend/node_modules
```

Si alguno de esos comandos **no muestra salida**, significa que ese archivo NO está siendo ignorado y hay que revisarlo.

---

## Resumen de acciones a ejecutar

| # | Acción | Archivo afectado | Estado |
|---|---|---|---|
| 1 | Crear `.gitignore` raíz completo | `grin_web/.gitignore` | ⏳ Pendiente de aprobación |
| 2 | Verificar que `backend/.env` queda ignorado | `grin_web/.gitignore` | ⏳ Pendiente |
| 3 | Limpiar credenciales de `alembic.ini` | `backend/alembic.ini` | ⏳ Pendiente |
| 4 | Mantener `backend/.env.example` sin credenciales reales | `backend/.env.example` | ✅ Ya está correcto |
| 5 | El `.gitignore` de `frontend/` puede eliminarse o dejarse | `frontend/.gitignore` | Opcional |

---

*Documento de seguridad para el equipo de desarrollo de **Energreen Perú E.I.R.L.***
