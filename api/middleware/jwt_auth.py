"""
Middleware y dependencies para autenticación JWT
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from database.connection import get_db
from database.models import Usuario, UserRole
from api.services.auth_service import decode_token

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependency que extrae y valida el usuario del JWT token.
    Lanza HTTP 401 si el token es inválido o el usuario no existe.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decodificar token
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise credentials_exception

    # Extraer email del payload
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    # Buscar usuario en BD
    user = db.query(Usuario).filter(Usuario.email == email).first()

    if user is None:
        raise credentials_exception

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )

    return user


async def get_current_active_user(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Dependency que verifica que el usuario esté activo.
    """
    if not current_user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user


def require_role(required_role: UserRole):
    """
    Factory de dependency que verifica que el usuario tenga un rol específico.

    Usage:
        @app.get("/admin/users", dependencies=[Depends(require_role(UserRole.OPERADOR_FICEM))])
    """
    async def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.rol != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol {required_role.value}"
            )
        return current_user

    return role_checker


def require_any_role(*required_roles: UserRole):
    """
    Factory de dependency que verifica que el usuario tenga alguno de los roles especificados.

    Usage:
        @app.get("/uploads", dependencies=[Depends(require_any_role(UserRole.EMPRESA, UserRole.COORDINADOR_PAIS))])
    """
    async def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.rol not in required_roles:
            roles_str = ", ".join([r.value for r in required_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de los siguientes roles: {roles_str}"
            )
        return current_user

    return role_checker
