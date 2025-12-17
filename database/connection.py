"""
Gestión de conexiones a la base de datos
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de base de datos desde variables de entorno
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost:5432/ficem_core"
)

# Crear engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "False").lower() == "true",
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
    pool_size=5,
    max_overflow=10
)

# Crear session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para FastAPI que proporciona una sesión de BD.
    Se cierra automáticamente al terminar la request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa la base de datos creando todas las tablas.
    Solo para desarrollo, en producción usar Alembic.
    """
    from database.models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos inicializada")
