"""
Servicio de autenticación
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from database.models import Usuario

load_dotenv()

# Configuración
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# Context para hashear passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar que el password coincida con el hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashear un password"""
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str) -> Optional[Usuario]:
    """
    Autenticar usuario por email y password.
    Retorna el usuario si las credenciales son correctas, None si no.
    """
    user = db.query(Usuario).filter(Usuario.email == email).first()

    if not user:
        return None

    if not user.activo:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crear un JWT token.

    Args:
        data: Diccionario con los datos a incluir en el token
        expires_delta: Tiempo de expiración (default: 60 minutos)

    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decodificar un JWT token.

    Args:
        token: Token JWT a decodificar

    Returns:
        Diccionario con los datos del token o None si es inválido
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
