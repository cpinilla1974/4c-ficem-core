"""
Modelos de base de datos SQLAlchemy para Calculadora País 4C
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class Empresa(Base):
    """Tabla de empresas cementeras/concreteras"""
    __tablename__ = 'empresas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    pais = Column(String(100), nullable=False)
    perfil_planta = Column(String(50), nullable=False)  # integrada/molienda/concreto
    contacto = Column(String(200))
    email = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Empresa(id={self.id}, nombre='{self.nombre}', pais='{self.pais}')>"


def get_engine():
    """Crear engine de SQLAlchemy para PostgreSQL"""
    # Leer configuración desde .env
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'latam4c_db')
    db_user = os.getenv('DB_USER', os.getenv('USER'))
    db_password = os.getenv('DB_PASSWORD', '')

    # Construir URL de conexión PostgreSQL
    # Usar host vacío para conexión UNIX socket (peer authentication)
    if db_password:
        db_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    else:
        # Conexión local sin password usando peer authentication
        db_url = f'postgresql:///{db_name}'

    engine = create_engine(db_url, echo=False)
    return engine


def init_db():
    """Inicializar base de datos y crear tablas"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Crear sesión de base de datos"""
    Session = sessionmaker(bind=engine)
    return Session()
