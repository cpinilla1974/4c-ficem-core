"""
Rutas para gestión de usuarios
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from database.connection import get_db
from database.models import Usuario, UserRole
from api.middleware.jwt_auth import get_current_user
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Schemas
class UsuarioResponse(BaseModel):
    id: int
    email: str
    nombre: str
    rol: str
    pais: str
    empresa_id: Optional[int]
    activo: bool
    created_at: str

    class Config:
        from_attributes = True


class UsuarioCreate(BaseModel):
    email: EmailStr
    nombre: str
    password: str
    rol: str
    pais: str
    empresa_id: Optional[int] = None
    activo: bool = True


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[str] = None
    pais: Optional[str] = None
    empresa_id: Optional[int] = None
    activo: Optional[bool] = None


@router.get("/usuarios", response_model=List[UsuarioResponse])
async def listar_usuarios(
    pais: Optional[str] = Query(None, description="Filtrar por país"),
    rol: Optional[str] = Query(None, description="Filtrar por rol"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar usuarios con filtros opcionales.

    Requiere autenticación. Solo usuarios ROOT y ADMIN_PROCESO pueden ver todos los usuarios.
    """
    # Verificar permisos
    if current_user.rol not in [UserRole.ROOT, UserRole.ADMIN_PROCESO]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para listar usuarios"
        )

    # Query base
    query = db.query(Usuario)

    # Aplicar filtros
    if pais and pais != "Todos":
        query = query.filter(Usuario.pais == pais)

    if rol and rol != "Todos":
        query = query.filter(Usuario.rol == rol)

    if activo is not None:
        query = query.filter(Usuario.activo == activo)

    # Ordenar por fecha de creación
    query = query.order_by(Usuario.created_at.desc())

    usuarios = query.all()

    # Convertir a response
    return [
        UsuarioResponse(
            id=u.id,
            email=u.email,
            nombre=u.nombre,
            rol=u.rol.value,
            pais=u.pais,
            empresa_id=u.empresa_id,
            activo=u.activo,
            created_at=u.created_at.isoformat()
        )
        for u in usuarios
    ]


@router.get("/usuarios/{usuario_id}", response_model=UsuarioResponse)
async def obtener_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener un usuario por ID.
    """
    # Verificar permisos
    if current_user.rol not in [UserRole.ROOT, UserRole.ADMIN_PROCESO]:
        if current_user.id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver este usuario"
            )

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return UsuarioResponse(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        rol=usuario.rol.value,
        pais=usuario.pais,
        empresa_id=usuario.empresa_id,
        activo=usuario.activo,
        created_at=usuario.created_at.isoformat()
    )


@router.post("/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    usuario_data: UsuarioCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo usuario.

    Solo usuarios ROOT y ADMIN_PROCESO pueden crear usuarios.
    """
    # Verificar permisos
    if current_user.rol not in [UserRole.ROOT, UserRole.ADMIN_PROCESO]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear usuarios"
        )

    # Verificar si el email ya existe
    existing_user = db.query(Usuario).filter(Usuario.email == usuario_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email"
        )

    # Validar rol
    try:
        rol_enum = UserRole(usuario_data.rol)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol inválido: {usuario_data.rol}"
        )

    # Hash de la contraseña
    hashed_password = pwd_context.hash(usuario_data.password)

    # Crear usuario
    nuevo_usuario = Usuario(
        email=usuario_data.email,
        password_hash=hashed_password,
        nombre=usuario_data.nombre,
        rol=rol_enum,
        pais=usuario_data.pais,
        empresa_id=usuario_data.empresa_id,
        activo=usuario_data.activo
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return UsuarioResponse(
        id=nuevo_usuario.id,
        email=nuevo_usuario.email,
        nombre=nuevo_usuario.nombre,
        rol=nuevo_usuario.rol.value,
        pais=nuevo_usuario.pais,
        empresa_id=nuevo_usuario.empresa_id,
        activo=nuevo_usuario.activo,
        created_at=nuevo_usuario.created_at.isoformat()
    )


@router.put("/usuarios/{usuario_id}", response_model=UsuarioResponse)
async def actualizar_usuario(
    usuario_id: int,
    usuario_data: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar un usuario existente.
    """
    # Verificar permisos
    if current_user.rol not in [UserRole.ROOT, UserRole.ADMIN_PROCESO]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar usuarios"
        )

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Actualizar campos
    if usuario_data.nombre is not None:
        usuario.nombre = usuario_data.nombre

    if usuario_data.rol is not None:
        try:
            usuario.rol = UserRole(usuario_data.rol)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol inválido: {usuario_data.rol}"
            )

    if usuario_data.pais is not None:
        usuario.pais = usuario_data.pais

    if usuario_data.empresa_id is not None:
        usuario.empresa_id = usuario_data.empresa_id

    if usuario_data.activo is not None:
        usuario.activo = usuario_data.activo

    db.commit()
    db.refresh(usuario)

    return UsuarioResponse(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        rol=usuario.rol.value,
        pais=usuario.pais,
        empresa_id=usuario.empresa_id,
        activo=usuario.activo,
        created_at=usuario.created_at.isoformat()
    )


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar (desactivar) un usuario.

    Solo ROOT puede eliminar usuarios.
    """
    if current_user.rol != UserRole.ROOT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo ROOT puede eliminar usuarios"
        )

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # No eliminar, solo desactivar
    usuario.activo = False
    db.commit()

    return None