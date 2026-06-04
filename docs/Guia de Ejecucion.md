# Guía de Ejecución — Proyecto GRIN Web

> **Propósito:** Esta guía permite a cualquier colaborador clonar, configurar y ejecutar el proyecto GRIN en su PC/laptop local, de manera idéntica al entorno de desarrollo principal.

---

## Requisitos previos

Antes de comenzar, instala o verifica que tengas los siguientes programas en tu máquina:
En tu terminal de CMD o PowerShell ejecuta los siguientes comandos:
git --version; python --version; node -v; psql --version
Si no los tienes, instálalos y vuelve a ejecutar los comandos y verifica que tengas la versión correcta:
| **Git** | Cualquier versión reciente 
| **Python** | 3.11 o superior
| **Node.js** | 18 o superior
| **PostgreSQL** | 15 o superior
> ⚠️ **Importante:** Durante la instalación de **Python**, asegúrate de marcar la casilla **"Add Python to PATH"** antes de hacer clic en "Install Now".

---

## Paso 1 — Restaurar la Base de Datos PostgreSQL

En la carpeta Docs se te entregará el archivo de respaldo de la base de datos BD_GRIN (formato `.sql`).

1. Abre **pgAdmin** (se instala automáticamente junto con PostgreSQL).
2. En el panel izquierdo, haz clic derecho sobre **Databases** → **Create** → **Database**.
3. Nombra la base de datos exactamente: **`BD_GRIN`** y guarda.
4. Haz clic derecho sobre `BD_GRIN` → selecciona **Query Tool** y pega el contenido de BD_GRIN.sql de la carpeta Docs y ejecutar ▶️.

---

## Paso 2 — Configurar el Backend (FastAPI)

El backend está construido con **Python + FastAPI**. Abre una terminal y ve a la carpeta del backend:

```bash
cd backend
```

### 2.1 Crear el entorno virtual de Python

```bash
python -m venv venv
```

### 2.2 Activar el entorno virtual

```bash
# En Windows — PowerShell:
venv\Scripts\Activate.ps1

# En Windows — CMD:
venv\Scripts\activate.bat
```

> ✅ Sabrás que el entorno está activo cuando aparezca `(venv)` al inicio de tu línea de comandos.

> ⚠️ **Si PowerShell muestra un error de permisos** al activar el entorno virtual, ejecuta este comando una sola vez y luego vuelve a intentar el paso anterior:
> ```bash
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### 2.3 Instalar las dependencias de Python

```bash
pip install -r requirements.txt
```

### 2.4 Crear el archivo de configuración `.env`

El archivo `.env` contiene las credenciales de conexión a la base de datos. **Este archivo no está en el repositorio** (es ignorado por Git por seguridad), por lo que debes crearlo tú mismo copiando la plantilla:

```bash
# En PowerShell / CMD:
copy .env.example .env
```

Luego abre el archivo `.env` con cualquier editor de texto (Notepad, VS Code, etc.) y edita la primera línea con tus propias credenciales de PostgreSQL:

```env
DATABASE_URL=postgresql://TU_USUARIO:TU_CONTRASEÑA@localhost:5432/BD_GRIN
CORS_ORIGINS=http://localhost:5173
```

Reemplaza:
- `TU_USUARIO` → usuario de PostgreSQL (por defecto es `postgres`)
- `TU_CONTRASEÑA` → la contraseña que configuraste al instalar PostgreSQL

### 2.5 Iniciar el servidor del backend

```bash
uvicorn app.main:app --reload
```

Si todo está correcto, verás en la terminal una salida similar a esta:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

> 💡 Deja esta terminal **abierta**. El backend debe estar corriendo mientras usas la aplicación.

---

## Paso 3 — Configurar el Frontend (React + Vite)

El frontend está construido con **React + Vite**. Abre una **segunda terminal nueva** (sin cerrar la del backend) y navega a la carpeta del frontend:

```bash
cd frontend
```

### 3.1 Instalar las dependencias de Node.js

```bash
npm install
```

> Este comando descarga todos los paquetes necesarios listados en `package.json`. Solo necesitas ejecutarlo **la primera vez** o cuando un compañero añada nuevas dependencias al proyecto.

### 3.2 Iniciar el servidor de desarrollo

```bash
npm run dev
```

Si todo está correcto, verás una salida similar a esta:

```
  VITE v8.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

## Paso 4 — Abrir la aplicación en el navegador

Con ambos servidores corriendo, abre tu navegador preferido y ve a:

**➜ http://localhost:5173**

---

## Resumen — Las 2 terminales necesarias

Para trabajar necesitas **dos terminales abiertas simultáneamente** durante toda la sesión de desarrollo:

| # | Terminal | Directorio | Comando |
|---|---|---|---|
| 1 | **Backend** | `grin_web/backend` | `uvicorn app.main:app --reload` |
| 2 | **Frontend** | `grin_web/frontend` | `npm run dev` |

---

## Contribuir al proyecto

Una vez que el proyecto esté corriendo, sigue este flujo para contribuir:

```bash
# 1. Asegúrate de estar en la rama principal actualizada
git checkout main
git pull origin main

# 2. Crea una rama nueva con un nombre descriptivo
git checkout -b feature/nombre-de-tu-funcionalidad

# 3. Haz tus cambios y guárdalos
git add .
git commit -m "descripción clara de lo que hiciste"

# 4. Sube tu rama al repositorio
git push origin feature/nombre-de-tu-funcionalidad

# 5. Crea un Pull Request en GitHub/GitLab para revisión
```

> ⚠️ **Nunca hagas commits directamente sobre la rama `main`.**

---

## Solución de problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `python` no se reconoce en la terminal | Python no está en el PATH | Reinstala Python marcando **"Add to PATH"** y reinicia la terminal |
| Error de conexión a la base de datos | Credenciales incorrectas en `.env` | Verifica usuario y contraseña en el archivo `backend/.env` |
| Error al activar `venv` en PowerShell | Política de ejecución restringida | Ejecuta: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `npm` no se reconoce | Node.js no instalado o PATH incorrecto | Reinstala Node.js y abre una nueva terminal |
| Puerto 8000 ya está en uso | Otro proceso ocupa el puerto | Cierra otras aplicaciones o ejecuta con `--port 8001` |
| Puerto 5173 ya está en uso | Otro proceso ocupa el puerto | Vite asignará automáticamente el siguiente puerto disponible |

---

## Estructura del proyecto

```
grin_web/
├── backend/                # API REST — Python + FastAPI
│   ├── app/                # Módulos de la aplicación
│   ├── alembic/            # Migraciones de base de datos
│   ├── assets/             # Recursos estáticos del backend (logos, plantillas)
│   ├── requirements.txt    # Dependencias de Python
│   ├── .env.example        # Plantilla de configuración (copiar como .env)
│   └── alembic.ini         # Configuración de migraciones
│
├── frontend/               # Interfaz de usuario — React + Vite
│   ├── src/                # Código fuente React
│   ├── public/             # Archivos públicos estáticos
│   ├── package.json        # Dependencias de Node.js
│   └── vite.config.js      # Configuración de Vite
│
└── docs/                   # Documentación del proyecto
```

---

*Documento generado para el equipo de desarrollo de **Energreen Perú E.I.R.L.***
