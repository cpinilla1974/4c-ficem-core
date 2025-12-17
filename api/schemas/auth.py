"""
Schemas Pydantic para autenticación
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """Request de login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response con JWT token"""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Respuesta con datos del usuario"""
    id: int
    email: str
    nombre: str
    rol: str
    pais: str
    empresa_id: Optional[int] = None
    activo: bool

    class Config:
        from_attributes = True  # Para SQLAlchemy 2.0+
