"""
Modelos de base de datos SQLAlchemy para 4C FICEM CORE
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()


# Enums
class UserRole(str, enum.Enum):
    """Roles de usuario en el sistema"""
    # FICEM (nivel global)
    ROOT = "ROOT"                              # Superadmin, todo
    ADMIN_PROCESO = "ADMIN_PROCESO"            # Staff FICEM, gestiona procesos
    EJECUTIVO_FICEM = "EJECUTIVO_FICEM"        # Directivo, solo lectura
    AMIGO_FICEM = "AMIGO_FICEM"                # Académico/consultor, datos amigos

    # País (nivel país)
    COORDINADOR_PAIS = "COORDINADOR_PAIS"      # Asociación nacional, supervisa

    # Empresa (nivel empresa)
    SUPERVISOR_EMPRESA = "SUPERVISOR_EMPRESA"  # Jefe, aprueba antes de enviar
    INFORMANTE_EMPRESA = "INFORMANTE_EMPRESA"  # Carga datos
    VISOR_EMPRESA = "VISOR_EMPRESA"            # Solo lectura


class PerfilPlanta(str, enum.Enum):
    """Perfiles de planta"""
    INTEGRADA = "integrada"
    MOLIENDA = "molienda"
    CONCRETO = "concreto"


class EstadoEnvio(str, enum.Enum):
    """Estados del ciclo de vida de un envío (DEPRECATED - usar Submission)"""
    BORRADOR = "borrador"
    VALIDANDO = "validando"
    RECHAZADO = "rechazado"
    APROBADO_PAIS = "aprobado_pais"
    APROBADO_FICEM = "aprobado_ficem"
    PROCESADO = "procesado"


class EstadoProceso(str, enum.Enum):
    """Estados de un proceso MRV"""
    BORRADOR = "borrador"
    ACTIVO = "activo"
    CERRADO = "cerrado"
    ARCHIVADO = "archivado"


class EstadoSubmission(str, enum.Enum):
    """Estados de un submission en el workflow"""
    BORRADOR = "BORRADOR"                      # Informante trabajando
    ENVIADO = "ENVIADO"                        # Informante envió a supervisor
    APROBADO_EMPRESA = "APROBADO_EMPRESA"      # Supervisor empresa aprobó
    EN_REVISION_FICEM = "EN_REVISION_FICEM"    # Admin FICEM revisando
    APROBADO_FICEM = "APROBADO_FICEM"          # Admin FICEM aprobó (final)
    RECHAZADO_EMPRESA = "RECHAZADO_EMPRESA"    # Supervisor rechazó
    RECHAZADO_FICEM = "RECHAZADO_FICEM"        # Admin FICEM rechazó
    PUBLICADO = "PUBLICADO"                    # Visible públicamente
    ARCHIVADO = "ARCHIVADO"                    # Histórico


class TipoProceso(str, enum.Enum):
    """Tipos de procesos MRV"""
    PRODUCE = "PRODUCE"
    MRV_HR = "MRV_HR"
    CUATRO_C_NACIONAL = "4C_NACIONAL"
    OTRO = "OTRO"


# Modelos
class Usuario(Base):
    """Tabla de usuarios del sistema"""
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(200), nullable=False)
    rol = Column(Enum(UserRole), nullable=False, index=True)
    pais = Column(String(100), nullable=False, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    empresa = relationship("Empresa", back_populates="usuarios")

    def __repr__(self):
        return f"<Usuario(id={self.id}, email='{self.email}', rol='{self.rol}')>"


class Empresa(Base):
    """Tabla de empresas cementeras/concreteras"""
    __tablename__ = 'empresas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    pais = Column(String(100), nullable=False, index=True)
    perfil_planta = Column(Enum(PerfilPlanta), nullable=False)
    contacto = Column(String(200))
    email = Column(String(200))
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    usuarios = relationship("Usuario", back_populates="empresa")
    plantas = relationship("Planta", back_populates="empresa")
    envios = relationship("Envio", back_populates="empresa")

    def __repr__(self):
        return f"<Empresa(id={self.id}, nombre='{self.nombre}', pais='{self.pais}')>"


class Planta(Base):
    """Tabla de plantas de producción"""
    __tablename__ = 'plantas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    nombre = Column(String(200), nullable=False)
    ciudad = Column(String(200))
    latitud = Column(Float)
    longitud = Column(Float)
    tipo = Column(Enum(PerfilPlanta), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    empresa = relationship("Empresa", back_populates="plantas")

    def __repr__(self):
        return f"<Planta(id={self.id}, nombre='{self.nombre}', empresa_id={self.empresa_id})>"


class Envio(Base):
    """Tabla de envíos de datos (archivos Excel)"""
    __tablename__ = 'envios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    archivo_nombre = Column(String(500), nullable=False)
    archivo_path = Column(String(1000), nullable=False)
    estado = Column(Enum(EstadoEnvio), default=EstadoEnvio.BORRADOR, nullable=False, index=True)
    errores_validacion = Column(Text)  # JSON con errores
    comentarios = Column(Text)  # Comentarios de revisión
    aprobado_por_pais = Column(Integer, ForeignKey('usuarios.id'))
    aprobado_por_ficem = Column(Integer, ForeignKey('usuarios.id'))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    empresa = relationship("Empresa", back_populates="envios")
    resultados = relationship("Resultado", back_populates="envio")

    def __repr__(self):
        return f"<Envio(id={self.id}, empresa_id={self.empresa_id}, estado='{self.estado}')>"


class Resultado(Base):
    """Tabla de resultados de cálculos de huella de carbono"""
    __tablename__ = 'resultados'

    id = Column(Integer, primary_key=True, autoincrement=True)
    envio_id = Column(Integer, ForeignKey('envios.id'), nullable=False, unique=True)

    # Cálculos A1-A3
    a1_clinker = Column(Float)  # kg CO2/ton clinker
    a2_cemento = Column(Float)  # kg CO2/ton cemento
    a3_concreto = Column(Float)  # kg CO2/m3 concreto

    # Clasificación GCCA
    banda_gcca = Column(String(5))  # AA, A, B, C, D, E, F
    resistencia = Column(Float)  # MPa

    # Datos agregados (JSON)
    datos_detalle = Column(Text)  # JSON con detalles completos

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    envio = relationship("Envio", back_populates="resultados")

    def __repr__(self):
        return f"<Resultado(id={self.id}, envio_id={self.envio_id}, banda_gcca='{self.banda_gcca}')>"


class FactorEmision(Base):
    """Tabla de factores de emisión configurables"""
    __tablename__ = 'factores_emision'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    categoria = Column(String(100), nullable=False)  # combustible, electricidad, transporte, etc.
    valor = Column(Float, nullable=False)
    unidad = Column(String(50), nullable=False)  # kg CO2/kWh, kg CO2/L, etc.
    pais = Column(String(100))  # NULL = global
    fuente = Column(String(500))
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<FactorEmision(id={self.id}, nombre='{self.nombre}', valor={self.valor})>"


class BlogPost(Base):
    """Tabla de posts del blog público"""
    __tablename__ = 'blog_posts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(500), nullable=False)
    slug = Column(String(500), unique=True, nullable=False, index=True)
    contenido = Column(Text, nullable=False)  # Markdown
    autor = Column(String(200), nullable=False)
    pais = Column(String(100))  # NULL = regional
    categoria = Column(String(100))
    publicado = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime)

    def __repr__(self):
        return f"<BlogPost(id={self.id}, titulo='{self.titulo}', publicado={self.publicado})>"


class ProcesoMRV(Base):
    """Tabla de procesos MRV configurables por país"""
    __tablename__ = 'procesos_mrv'

    id = Column(String(100), primary_key=True)  # Ej: 'produce-peru-2024'
    pais_iso = Column(String(2), nullable=False, index=True)  # Ej: 'PE', 'CO'
    tipo = Column(Enum(TipoProceso), nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    ciclo = Column(String(20))  # Ej: '2024', '2024-2025'
    estado = Column(Enum(EstadoProceso), default=EstadoProceso.ACTIVO, nullable=False, index=True)

    # Coordinador FICEM responsable del proceso
    coordinador_ficem_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)

    # Configuración completa del proceso (JSON)
    config = Column(JSONB, nullable=False)
    """
    Estructura config:
    {
        "template_version": "produce_peru_v2.1.xlsx",
        "hojas_requeridas": ["Cemento", "Concreto", "Clinker"],
        "validaciones": [
            {"tipo": "estructura", "nivel": "error"},
            {"tipo": "rangos", "nivel": "warning", "params": {...}}
        ],
        "workflow_steps": [
            {"step": "borrador", "roles": ["empresa"]},
            {"step": "enviado", "roles": ["empresa"], "notificar": ["coordinador"]},
            {"step": "en_revision", "roles": ["coordinador_pais"]},
            {"step": "aprobado", "roles": ["coordinador_pais"], "triggers": ["ejecutar_calculos"]}
        ],
        "deadline_envio": "2025-03-31",
        "deadline_revision": "2025-04-30",
        "calculos_habilitados": ["gcca", "bandas", "benchmarking"],
        "esquema_bd": "peru_data"
    }
    """

    created_by = Column(Integer, ForeignKey('usuarios.id'))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    submissions = relationship("Submission", back_populates="proceso", cascade="all, delete-orphan")
    creador = relationship("Usuario", foreign_keys=[created_by])
    coordinador_ficem = relationship("Usuario", foreign_keys=[coordinador_ficem_id])

    def __repr__(self):
        return f"<ProcesoMRV(id='{self.id}', pais='{self.pais_iso}', tipo='{self.tipo}')>"


class Submission(Base):
    """Tabla de submissions (envíos) dentro de un proceso MRV"""
    __tablename__ = 'submissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proceso_id = Column(String(100), ForeignKey('procesos_mrv.id', ondelete='CASCADE'), nullable=False, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id', ondelete='CASCADE'), nullable=False, index=True)
    planta_id = Column(Integer, ForeignKey('plantas.id', ondelete='SET NULL'), nullable=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False, index=True)

    # Estado actual y historial
    estado_actual = Column(Enum(EstadoSubmission), nullable=False, default=EstadoSubmission.BORRADOR, index=True)
    workflow_history = Column(JSONB, default=list, nullable=False)
    """
    Estructura workflow_history:
    [
        {"estado": "borrador", "fecha": "2024-11-01T10:00:00", "user_id": 123},
        {"estado": "enviado", "fecha": "2024-11-15T14:30:00", "user_id": 123},
        {"estado": "en_revision", "fecha": "2024-11-16T09:00:00", "user_id": 456}
    ]
    """

    # Archivos y datos
    archivo_excel = Column(JSONB)
    """
    Estructura archivo_excel:
    {
        "url": "s3://ficem-uploads/PE/2024/empresa123_20241115.xlsx",
        "filename": "datos_2024.xlsx",
        "hash": "sha256:...",
        "size_bytes": 245678,
        "uploaded_at": "2024-11-15T14:30:00"
    }
    """

    datos_extraidos = Column(JSONB)
    """
    Estructura datos_extraidos:
    {
        "cemento": [...],
        "concreto": [...],
        "clinker": [...]
    }
    """

    validaciones = Column(JSONB, default=list)
    """
    Estructura validaciones:
    [
        {"tipo": "estructura", "status": "ok"},
        {"tipo": "rangos", "status": "warning", "detalles": [...]}
    ]
    """

    comentarios = Column(JSONB, default=list)
    """
    Estructura comentarios:
    [
        {
            "user_id": 456,
            "user_nombre": "Coordinador ASOCEM",
            "fecha": "2024-11-20T10:00:00",
            "texto": "Revisar valor clinker planta Lima"
        }
    ]
    """

    resultados_calculos = Column(JSONB)
    """
    Estructura resultados_calculos:
    {
        "ejecutado": "2024-11-25T15:00:00",
        "gcca": {...},
        "bandas": {...},
        "benchmarking": {...}
    }
    """

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    submitted_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    approved_at = Column(DateTime)

    # Relaciones
    proceso = relationship("ProcesoMRV", back_populates="submissions")
    empresa = relationship("Empresa")
    planta = relationship("Planta")
    usuario = relationship("Usuario")

    def __repr__(self):
        return f"<Submission(id={self.id}, proceso='{self.proceso_id}', estado='{self.estado_actual}')>"
