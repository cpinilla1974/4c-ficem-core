"""
Esquemas Pydantic para Procesos MRV y Submissions
"""
from pydantic import BaseModel, Field, UUID4
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class TipoProceso(str, Enum):
    """Tipos de procesos MRV"""
    PRODUCE = "PRODUCE"
    MRV_HR = "MRV_HR"
    CUATRO_C_NACIONAL = "4C_NACIONAL"
    OTRO = "OTRO"


class EstadoProceso(str, Enum):
    """Estados de un proceso MRV"""
    BORRADOR = "borrador"
    ACTIVO = "activo"
    CERRADO = "cerrado"
    ARCHIVADO = "archivado"


class EstadoSubmission(str, Enum):
    """Estados de un submission"""
    BORRADOR = "BORRADOR"                      # Informante trabajando
    ENVIADO = "ENVIADO"                        # Informante envió a supervisor
    APROBADO_EMPRESA = "APROBADO_EMPRESA"      # Supervisor empresa aprobó
    EN_REVISION_FICEM = "EN_REVISION_FICEM"    # Admin FICEM revisando
    APROBADO_FICEM = "APROBADO_FICEM"          # Admin FICEM aprobó (final)
    RECHAZADO_EMPRESA = "RECHAZADO_EMPRESA"    # Supervisor rechazó
    RECHAZADO_FICEM = "RECHAZADO_FICEM"        # Admin FICEM rechazó
    PUBLICADO = "PUBLICADO"                    # Visible públicamente
    ARCHIVADO = "ARCHIVADO"                    # Histórico


# Esquemas de configuración
class WorkflowStep(BaseModel):
    """Paso del workflow de un proceso"""
    step: str
    roles: List[str]
    descripcion: Optional[str] = None
    notificar: Optional[List[str]] = None
    triggers: Optional[List[str]] = None
    visible: Optional[bool] = False


class Validacion(BaseModel):
    """Validación de un proceso"""
    tipo: str
    nivel: str  # error | warning
    mensaje: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


class ConfigProceso(BaseModel):
    """Configuración completa de un proceso"""
    template_version: str
    hojas_requeridas: List[str]
    validaciones: List[Validacion]
    workflow_steps: List[WorkflowStep]
    deadline_envio: Optional[str] = None
    deadline_revision: Optional[str] = None
    calculos_habilitados: List[str] = ["gcca", "bandas"]
    esquema_bd: Optional[str] = None


# Esquemas para Procesos
class ProcesoCreate(BaseModel):
    """Crear proceso MRV"""
    id: str = Field(..., description="ID único del proceso (ej: 'produce-peru-2024')")
    pais_iso: str = Field(..., min_length=2, max_length=2, description="Código ISO país")
    tipo: TipoProceso
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    ciclo: Optional[str] = Field(None, max_length=20)
    coordinador_ficem_id: Optional[int] = Field(None, description="ID del admin_proceso responsable")
    config: ConfigProceso


class ProcesoUpdate(BaseModel):
    """Actualizar proceso MRV"""
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    config: Optional[ConfigProceso] = None


class ProcesoEstadoUpdate(BaseModel):
    """Cambiar estado de un proceso"""
    estado: EstadoProceso


class ProcesoResponse(BaseModel):
    """Respuesta con datos de un proceso"""
    id: str
    pais_iso: str
    tipo: TipoProceso
    nombre: str
    descripcion: Optional[str]
    ciclo: Optional[str]
    estado: EstadoProceso
    coordinador_ficem_id: Optional[int]
    config: Dict[str, Any]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProcesoListItem(BaseModel):
    """Item de lista de procesos (sin config completo)"""
    id: str
    pais_iso: str
    tipo: TipoProceso
    nombre: str
    descripcion: Optional[str]
    ciclo: Optional[str]
    estado: EstadoProceso
    created_at: datetime

    class Config:
        from_attributes = True


class ProcesoList(BaseModel):
    """Lista paginada de procesos"""
    total: int
    items: List[ProcesoListItem]


# Esquemas para Submissions
class SubmissionCreate(BaseModel):
    """Crear submission"""
    empresa_id: int
    planta_id: Optional[int] = None


class SubmissionUpload(BaseModel):
    """Metadata de archivo subido"""
    url: str
    filename: str
    hash: Optional[str] = None
    size_bytes: int
    uploaded_at: datetime


class WorkflowHistoryItem(BaseModel):
    """Item del historial de workflow"""
    estado: str
    fecha: datetime
    user_id: int
    user_nombre: Optional[str] = None


class ValidacionResult(BaseModel):
    """Resultado de una validación"""
    tipo: str
    status: str  # ok | warning | error
    mensaje: Optional[str] = None
    detalles: Optional[List[str]] = None


class ComentarioItem(BaseModel):
    """Comentario en un submission"""
    user_id: int
    user_nombre: str
    fecha: datetime
    texto: str


class SubmissionResponse(BaseModel):
    """Respuesta con datos de un submission"""
    id: UUID4
    proceso_id: str
    empresa_id: int
    empresa_nombre: Optional[str] = None
    planta_id: Optional[int]
    planta_nombre: Optional[str] = None
    usuario_id: int
    estado_actual: EstadoSubmission
    workflow_history: List[Dict[str, Any]]
    archivo_excel: Optional[Dict[str, Any]]
    validaciones: Optional[List[Dict[str, Any]]]
    comentarios: Optional[List[Dict[str, Any]]]
    resultados_calculos: Optional[Dict[str, Any]]
    created_at: datetime
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    approved_at: Optional[datetime]

    class Config:
        from_attributes = True


class SubmissionListItem(BaseModel):
    """Item de lista de submissions"""
    id: UUID4
    proceso_id: str
    empresa_id: int
    empresa_nombre: Optional[str]
    planta_nombre: Optional[str]
    estado_actual: EstadoSubmission
    submitted_at: Optional[datetime]
    dias_en_estado: Optional[int] = None

    class Config:
        from_attributes = True


class SubmissionList(BaseModel):
    """Lista paginada de submissions"""
    total: int
    items: List[SubmissionListItem]


class SubmissionValidateResponse(BaseModel):
    """Respuesta de validación de submission"""
    submission_id: UUID4
    valido: bool
    errores: List[str]
    advertencias: List[str]
    validaciones: List[ValidacionResult]


class SubmissionSubmitResponse(BaseModel):
    """Respuesta al enviar submission"""
    id: UUID4
    estado_actual: EstadoSubmission
    submitted_at: datetime
    proximos_pasos: str


class SubmissionReviewRequest(BaseModel):
    """Request para revisar submission"""
    accion: str  # aprobar | rechazar
    comentario: str


class SubmissionReviewResponse(BaseModel):
    """Respuesta de revisión"""
    id: UUID4
    estado_actual: EstadoSubmission
    reviewed_at: datetime
    proximos_pasos: str


class ComentarioCreate(BaseModel):
    """Crear comentario"""
    texto: str = Field(..., min_length=1, max_length=2000)


class ComentarioResponse(BaseModel):
    """Respuesta con comentario creado"""
    id: str
    submission_id: UUID4
    user_id: int
    user_nombre: str
    texto: str
    fecha: datetime