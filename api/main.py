"""
Aplicación principal FastAPI para 4C FICEM CORE
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

# Crear aplicación
app = FastAPI(
    title="4C FICEM CORE API",
    description="Backend centralizado del sistema de huella de carbono para la industria cementera de Latinoamérica",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar rutas
from api.routes import auth, procesos, submissions, usuarios

# Registrar rutas
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(usuarios.router, prefix="/api/v1", tags=["Usuarios"])
app.include_router(procesos.router, prefix="/api/v1", tags=["Procesos MRV"])
app.include_router(submissions.router, prefix="/api/v1", tags=["Submissions"])


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "4C FICEM CORE API",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check detallado"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: verificar conexión real
        "service": "4c-ficem-core"
    }
