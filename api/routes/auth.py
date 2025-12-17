"""
Rutas de autenticación
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Usuario
from api.schemas.auth import LoginRequest, TokenResponse, UserResponse
from api.services.auth_service import authenticate_user, create_access_token
from api.middleware.jwt_auth import get_current_user

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint de login.

    Retorna un JWT token si las credenciales son correctas.
    """
    # Autenticar usuario
    user = authenticate_user(db, credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Crear JWT token con datos del usuario
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "rol": user.rol.value,
            "pais": user.pais,
            "empresa_id": user.empresa_id
        }
    )

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener información del usuario autenticado.

    Requiere JWT token válido.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        nombre=current_user.nombre,
        rol=current_user.rol.value,
        pais=current_user.pais,
        empresa_id=current_user.empresa_id,
        activo=current_user.activo
    )
