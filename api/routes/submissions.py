"""
Endpoints para gestión de Submissions (Envíos)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database.connection import get_db
from database.models import (
    Submission,
    ProcesoMRV,
    Usuario,
    Empresa,
    Planta,
    EstadoSubmission,
    EstadoProceso
)
from api.schemas.procesos import (
    SubmissionCreate,
    SubmissionResponse,
    SubmissionList,
    SubmissionListItem,
    SubmissionValidateResponse,
    SubmissionSubmitResponse,
    SubmissionReviewRequest,
    SubmissionReviewResponse,
    ComentarioCreate,
    ComentarioResponse,
    ValidacionResult
)
from api.middleware.jwt_auth import get_current_user
import uuid

router = APIRouter()


@router.post("/procesos/{proceso_id}/submissions", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def crear_submission(
    proceso_id: str,
    submission_data: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear nuevo submission para un proceso
    """
    # Verificar que el proceso existe y está activo
    proceso = db.query(ProcesoMRV).filter(
        ProcesoMRV.id == proceso_id,
        ProcesoMRV.estado == EstadoProceso.ACTIVO
    ).first()

    if not proceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proceso '{proceso_id}' no encontrado o no está activo"
        )

    # Verificar permisos de empresa
    if current_user.rol.value == "empresa":
        if submission_data.empresa_id != current_user.empresa_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede crear submissions para otra empresa"
            )

    # Verificar que la empresa existe
    empresa = db.query(Empresa).filter(Empresa.id == submission_data.empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empresa {submission_data.empresa_id} no encontrada"
        )

    # Verificar que no exista submission activo para esta empresa en este proceso
    existing = db.query(Submission).filter(
        Submission.proceso_id == proceso_id,
        Submission.empresa_id == submission_data.empresa_id,
        Submission.estado_actual != EstadoSubmission.ARCHIVADO
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un submission activo para esta empresa en este proceso. ID: {existing.id}"
        )

    # Crear submission
    nuevo_submission = Submission(
        id=uuid.uuid4(),
        proceso_id=proceso_id,
        empresa_id=submission_data.empresa_id,
        planta_id=submission_data.planta_id,
        usuario_id=current_user.id,
        estado_actual=EstadoSubmission.BORRADOR,
        workflow_history=[{
            "estado": "borrador",
            "fecha": datetime.utcnow().isoformat(),
            "user_id": current_user.id,
            "user_nombre": current_user.nombre
        }],
        validaciones=[],
        comentarios=[]
    )

    db.add(nuevo_submission)
    db.commit()
    db.refresh(nuevo_submission)

    return SubmissionResponse.model_validate(nuevo_submission)


@router.get("/procesos/{proceso_id}/submissions", response_model=SubmissionList)
async def listar_submissions(
    proceso_id: str,
    empresa_id: Optional[int] = Query(None),
    estado: Optional[EstadoSubmission] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Listar submissions de un proceso
    """
    query = db.query(Submission).filter(Submission.proceso_id == proceso_id)

    # Si es empresa, solo ver sus propios submissions
    if current_user.rol.value == "empresa":
        query = query.filter(Submission.empresa_id == current_user.empresa_id)
    elif empresa_id:  # Coordinador puede filtrar por empresa
        query = query.filter(Submission.empresa_id == empresa_id)

    if estado:
        query = query.filter(Submission.estado_actual == estado)

    total = query.count()
    submissions = query.order_by(Submission.created_at.desc()).offset(offset).limit(limit).all()

    # Enriquecer con datos de empresa
    items = []
    for s in submissions:
        empresa = db.query(Empresa).filter(Empresa.id == s.empresa_id).first()
        planta = db.query(Planta).filter(Planta.id == s.planta_id).first() if s.planta_id else None

        item = SubmissionListItem(
            id=s.id,
            proceso_id=s.proceso_id,
            empresa_id=s.empresa_id,
            empresa_nombre=empresa.nombre if empresa else None,
            planta_nombre=planta.nombre if planta else None,
            estado_actual=s.estado_actual,
            submitted_at=s.submitted_at,
            dias_en_estado=None  # TODO: calcular
        )
        items.append(item)

    return SubmissionList(total=total, items=items)


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
async def obtener_submission(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener detalle completo de un submission
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} no encontrado"
        )

    # Verificar permisos
    if current_user.rol.value == "empresa":
        if submission.empresa_id != current_user.empresa_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver este submission"
            )

    # Enriquecer con nombres
    empresa = db.query(Empresa).filter(Empresa.id == submission.empresa_id).first()
    planta = db.query(Planta).filter(Planta.id == submission.planta_id).first() if submission.planta_id else None

    response = SubmissionResponse.model_validate(submission)
    response.empresa_nombre = empresa.nombre if empresa else None
    response.planta_nombre = planta.nombre if planta else None

    return response


@router.post("/submissions/{submission_id}/upload")
async def subir_archivo(
    submission_id: uuid.UUID,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Subir archivo Excel a un submission

    **TODO**: Implementar almacenamiento real (S3, filesystem)
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} no encontrado"
        )

    # Verificar permisos
    if current_user.rol.value == "empresa":
        if submission.empresa_id != current_user.empresa_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para modificar este submission"
            )

    # Validar que el estado sea borrador
    if submission.estado_actual != EstadoSubmission.BORRADOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden subir archivos en estado borrador"
        )

    # Validar tipo de archivo
    if not archivo.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos .xlsx"
        )

    # TODO: Guardar archivo en S3 o filesystem
    # Por ahora solo simulamos
    file_url = f"s3://ficem-uploads/{submission.proceso_id}/{submission_id}/{archivo.filename}"

    submission.archivo_excel = {
        "url": file_url,
        "filename": archivo.filename,
        "size_bytes": 0,  # TODO: calcular tamaño real
        "uploaded_at": datetime.utcnow().isoformat()
    }

    db.commit()
    db.refresh(submission)

    return {
        "id": str(submission.id),
        "archivo_excel": submission.archivo_excel,
        "mensaje": "Archivo cargado exitosamente (simulado - implementar almacenamiento real)"
    }


@router.post("/submissions/{submission_id}/validate", response_model=SubmissionValidateResponse)
async def validar_submission(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Ejecutar validaciones en un submission

    **TODO**: Implementar validaciones reales según config del proceso
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} no encontrado"
        )

    # Verificar que tenga archivo
    if not submission.archivo_excel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe subir un archivo antes de validar"
        )

    # TODO: Ejecutar validaciones reales
    # Por ahora retornamos validaciones dummy
    validaciones = [
        ValidacionResult(tipo="estructura", status="ok", mensaje="Estructura correcta"),
        ValidacionResult(tipo="rangos", status="ok", mensaje="Rangos válidos"),
        ValidacionResult(tipo="consistencia", status="warning", mensaje="Producción 15% mayor que año anterior", detalles=["Revisar si es correcto"])
    ]

    # Guardar validaciones
    submission.validaciones = [v.model_dump() for v in validaciones]
    db.commit()

    errores = [v.mensaje for v in validaciones if v.status == "error"]
    advertencias = [v.mensaje for v in validaciones if v.status == "warning"]

    return SubmissionValidateResponse(
        submission_id=submission.id,
        valido=len(errores) == 0,
        errores=errores,
        advertencias=advertencias,
        validaciones=validaciones
    )


@router.post("/submissions/{submission_id}/submit", response_model=SubmissionSubmitResponse)
async def enviar_submission(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Enviar submission para revisión (cambiar estado a 'enviado')
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} no encontrado"
        )

    # Verificar permisos
    if current_user.rol.value == "empresa":
        if submission.empresa_id != current_user.empresa_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para enviar este submission"
            )

    # Verificar estado
    if submission.estado_actual != EstadoSubmission.BORRADOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede enviar un submission en estado '{submission.estado_actual.value}'"
        )

    # Verificar que tenga archivo y esté validado
    if not submission.archivo_excel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe subir un archivo antes de enviar"
        )

    if not submission.validaciones:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe validar el archivo antes de enviar"
        )

    # Verificar que no haya errores de validación
    errores = [v for v in submission.validaciones if v.get('status') == 'error']
    if errores:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede enviar con errores de validación"
        )

    # Cambiar estado
    submission.estado_actual = EstadoSubmission.ENVIADO
    submission.submitted_at = datetime.utcnow()

    # Agregar al historial
    history = submission.workflow_history or []
    history.append({
        "estado": "enviado",
        "fecha": datetime.utcnow().isoformat(),
        "user_id": current_user.id,
        "user_nombre": current_user.nombre
    })
    submission.workflow_history = history

    db.commit()
    db.refresh(submission)

    return SubmissionSubmitResponse(
        id=submission.id,
        estado_actual=submission.estado_actual,
        submitted_at=submission.submitted_at,
        proximos_pasos="Su envío será revisado por el coordinador nacional en los próximos 7 días"
    )


@router.post("/submissions/{submission_id}/review", response_model=SubmissionReviewResponse)
async def revisar_submission(
    submission_id: uuid.UUID,
    review_data: SubmissionReviewRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Aprobar o rechazar un submission (solo coordinador)
    """
    # Verificar permisos
    if current_user.rol.value not in ["coordinador_pais", "operador_ficem"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo coordinadores pueden revisar submissions"
        )

    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} no encontrado"
        )

    # Verificar estado
    if submission.estado_actual not in [EstadoSubmission.ENVIADO, EstadoSubmission.EN_REVISION]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede revisar un submission en estado '{submission.estado_actual.value}'"
        )

    # Validar acción
    if review_data.accion not in ["aprobar", "rechazar"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Acción debe ser 'aprobar' o 'rechazar'"
        )

    # Cambiar estado
    if review_data.accion == "aprobar":
        submission.estado_actual = EstadoSubmission.APROBADO
        submission.approved_at = datetime.utcnow()
        proximos_pasos = "Los cálculos se ejecutarán automáticamente"
    else:
        submission.estado_actual = EstadoSubmission.RECHAZADO
        proximos_pasos = "Corrija los datos y vuelva a enviar"

    submission.reviewed_at = datetime.utcnow()

    # Agregar al historial
    history = submission.workflow_history or []
    history.append({
        "estado": submission.estado_actual.value,
        "fecha": datetime.utcnow().isoformat(),
        "user_id": current_user.id,
        "user_nombre": current_user.nombre
    })
    submission.workflow_history = history

    # Agregar comentario
    comentarios = submission.comentarios or []
    comentarios.append({
        "user_id": current_user.id,
        "user_nombre": current_user.nombre,
        "fecha": datetime.utcnow().isoformat(),
        "texto": review_data.comentario
    })
    submission.comentarios = comentarios

    db.commit()
    db.refresh(submission)

    return SubmissionReviewResponse(
        id=submission.id,
        estado_actual=submission.estado_actual,
        reviewed_at=submission.reviewed_at,
        proximos_pasos=proximos_pasos
    )


@router.post("/submissions/{submission_id}/comentarios", response_model=ComentarioResponse, status_code=status.HTTP_201_CREATED)
async def agregar_comentario(
    submission_id: uuid.UUID,
    comentario_data: ComentarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Agregar comentario a un submission
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} no encontrado"
        )

    # Agregar comentario
    comentarios = submission.comentarios or []
    nuevo_comentario = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "user_nombre": current_user.nombre,
        "fecha": datetime.utcnow().isoformat(),
        "texto": comentario_data.texto
    }
    comentarios.append(nuevo_comentario)
    submission.comentarios = comentarios

    db.commit()

    return ComentarioResponse(
        id=nuevo_comentario["id"],
        submission_id=submission.id,
        user_id=current_user.id,
        user_nombre=current_user.nombre,
        texto=comentario_data.texto,
        fecha=datetime.fromisoformat(nuevo_comentario["fecha"])
    )


@router.get("/submissions/{submission_id}/results")
async def obtener_resultados(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener resultados de cálculos de un submission

    **TODO**: Implementar motor de cálculos
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} no encontrado"
        )

    # Verificar que esté aprobado
    if submission.estado_actual not in [EstadoSubmission.APROBADO, EstadoSubmission.PUBLICADO]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resultados no disponibles. Estado actual: {submission.estado_actual.value}"
        )

    # TODO: Ejecutar cálculos si no existen
    if not submission.resultados_calculos:
        # Por ahora retornamos error
        return {
            "submission_id": str(submission.id),
            "estado": submission.estado_actual.value,
            "mensaje": "Cálculos aún no ejecutados. Motor de cálculos en desarrollo."
        }

    return {
        "submission_id": str(submission.id),
        "estado": submission.estado_actual.value,
        "resultados_calculos": submission.resultados_calculos
    }