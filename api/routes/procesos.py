"""
Endpoints para gestión de Procesos MRV
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database.connection import get_db
from database.models import ProcesoMRV, Usuario, EstadoProceso, TipoProceso
from api.schemas.procesos import (
    ProcesoCreate,
    ProcesoUpdate,
    ProcesoEstadoUpdate,
    ProcesoResponse,
    ProcesoList,
    ProcesoListItem
)
from api.middleware.jwt_auth import get_current_user
from api.permissions import tiene_permiso

router = APIRouter()


@router.get("/procesos", response_model=ProcesoList, summary="Listar procesos")
async def listar_procesos(
    pais: Optional[str] = Query(None, description="Filtrar por código ISO país (ej: PE, CO)"),
    estado: Optional[EstadoProceso] = Query(None, description="Filtrar por estado"),
    tipo: Optional[TipoProceso] = Query(None, description="Filtrar por tipo de proceso"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Listar procesos MRV disponibles

    **Uso típico**:
    - Frontend país lista procesos activos: `?pais=PE&estado=activo`
    - Admin FICEM lista todos: sin filtros
    """
    query = db.query(ProcesoMRV)

    # Aplicar filtros
    if pais:
        query = query.filter(ProcesoMRV.pais_iso == pais.upper())

    if estado:
        query = query.filter(ProcesoMRV.estado == estado)

    if tipo:
        query = query.filter(ProcesoMRV.tipo == tipo)

    # Total
    total = query.count()

    # Paginación
    procesos = query.order_by(ProcesoMRV.created_at.desc()).offset(offset).limit(limit).all()

    return ProcesoList(
        total=total,
        items=[ProcesoListItem.model_validate(p) for p in procesos]
    )


@router.get("/procesos/{proceso_id}", response_model=ProcesoResponse, summary="Obtener proceso")
async def obtener_proceso(
    proceso_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener detalle completo de un proceso (incluye config)
    """
    proceso = db.query(ProcesoMRV).filter(ProcesoMRV.id == proceso_id).first()

    if not proceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proceso '{proceso_id}' no encontrado"
        )

    return ProcesoResponse.model_validate(proceso)


@router.post("/procesos", response_model=ProcesoResponse, status_code=status.HTTP_201_CREATED, summary="Crear proceso")
async def crear_proceso(
    proceso_data: ProcesoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear nuevo proceso MRV

    **Requiere**: permiso `procesos.crear`
    """
    if not tiene_permiso(current_user, "procesos.crear"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para crear procesos"
        )

    # Verificar si ya existe
    existing = db.query(ProcesoMRV).filter(ProcesoMRV.id == proceso_data.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un proceso con ID '{proceso_data.id}'"
        )

    # Crear proceso
    nuevo_proceso = ProcesoMRV(
        id=proceso_data.id,
        pais_iso=proceso_data.pais_iso.upper(),
        tipo=proceso_data.tipo,
        nombre=proceso_data.nombre,
        descripcion=proceso_data.descripcion,
        ciclo=proceso_data.ciclo,
        estado=EstadoProceso.BORRADOR,
        coordinador_ficem_id=proceso_data.coordinador_ficem_id,
        config=proceso_data.config.model_dump(),
        created_by=current_user.id
    )

    db.add(nuevo_proceso)
    db.commit()
    db.refresh(nuevo_proceso)

    return ProcesoResponse.model_validate(nuevo_proceso)


@router.put("/procesos/{proceso_id}", response_model=ProcesoResponse, summary="Actualizar proceso")
async def actualizar_proceso(
    proceso_id: str,
    proceso_data: ProcesoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualizar configuración de un proceso

    **Requiere**: permiso `procesos.editar`
    """
    if not tiene_permiso(current_user, "procesos.editar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para editar procesos"
        )

    proceso = db.query(ProcesoMRV).filter(ProcesoMRV.id == proceso_id).first()

    if not proceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proceso '{proceso_id}' no encontrado"
        )

    # Actualizar campos
    if proceso_data.nombre:
        proceso.nombre = proceso_data.nombre

    if proceso_data.descripcion is not None:
        proceso.descripcion = proceso_data.descripcion

    if proceso_data.config:
        proceso.config = proceso_data.config.model_dump()

    db.commit()
    db.refresh(proceso)

    return ProcesoResponse.model_validate(proceso)


@router.patch("/procesos/{proceso_id}/estado", response_model=ProcesoResponse, summary="Cambiar estado de proceso")
async def cambiar_estado_proceso(
    proceso_id: str,
    estado_data: ProcesoEstadoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cambiar estado de un proceso (borrador → activo → cerrado → archivado)

    **Requiere**: permiso `procesos.cambiar_estado`
    """
    if not tiene_permiso(current_user, "procesos.cambiar_estado"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para cambiar estado de procesos"
        )

    proceso = db.query(ProcesoMRV).filter(ProcesoMRV.id == proceso_id).first()

    if not proceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proceso '{proceso_id}' no encontrado"
        )

    proceso.estado = estado_data.estado

    db.commit()
    db.refresh(proceso)

    return ProcesoResponse.model_validate(proceso)


@router.delete("/procesos/{proceso_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar proceso")
async def eliminar_proceso(
    proceso_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Eliminar un proceso (solo si no tiene submissions)

    **Requiere**: permiso `procesos.eliminar`
    """
    if not tiene_permiso(current_user, "procesos.eliminar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para eliminar procesos"
        )

    proceso = db.query(ProcesoMRV).filter(ProcesoMRV.id == proceso_id).first()

    if not proceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proceso '{proceso_id}' no encontrado"
        )

    # Verificar que no tenga submissions
    if proceso.submissions and len(proceso.submissions) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un proceso con submissions asociados"
        )

    db.delete(proceso)
    db.commit()

    return None


@router.get("/procesos/{proceso_id}/template", summary="Descargar template Excel")
async def descargar_template(
    proceso_id: str,
    empresa_id: Optional[int] = Query(None, description="Pre-poblar con datos de esta empresa"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Descargar plantilla Excel para un proceso

    **TODO**: Implementar generación de Excel dinámico
    """
    proceso = db.query(ProcesoMRV).filter(ProcesoMRV.id == proceso_id).first()

    if not proceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proceso '{proceso_id}' no encontrado"
        )

    # TODO: Generar Excel basado en proceso.config.template_version
    # Por ahora retornar error
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Generación de templates aún no implementada. Ver /api/plantillas/{tipo}"
    )