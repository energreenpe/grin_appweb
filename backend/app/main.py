from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.modules.quote.router import router as quote_router
from app.modules.quote.service import QuoteError
from app.modules.inspector.router import router as inspector_router

settings = get_settings()

app = FastAPI(
    title="GRIN Web API",
    description="API REST para la plataforma GRIN — Energreen Perú E.I.R.L.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── EXCEPCIONES DE NEGOCIO ────────────────────────────────────────────────────
@app.exception_handler(QuoteError)
async def quote_error_handler(request: Request, exc: QuoteError):
    return JSONResponse(status_code=exc.code, content={"detail": exc.message})


# ── ROUTERS — agregar aquí cada nuevo módulo ──────────────────────────────────
app.include_router(quote_router, prefix="/api/quote", tags=["Quote"])
# app.include_router(math_router,     prefix="/api/math",      tags=["Math"])      # Módulo 2
app.include_router(inspector_router, prefix="/api/inspector", tags=["Inspector"]) # Módulo 3

# ── ARCHIVOS ESTÁTICOS (UPLOADS) ───────────────────────────────────────────────
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": "GRIN Web API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
