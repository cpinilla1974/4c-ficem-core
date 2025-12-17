"""
Script para crear usuario administrador inicial
Uso: python scripts/crear_usuario_admin.py
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Usuario, UserRole
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def crear_usuario_admin():
    """Crear usuario ROOT inicial"""
    db: Session = SessionLocal()

    try:
        # Verificar si ya existe un usuario ROOT
        existing_root = db.query(Usuario).filter(Usuario.rol == UserRole.ROOT).first()

        if existing_root:
            print(f"✓ Ya existe un usuario ROOT: {existing_root.email}")
            print(f"  Nombre: {existing_root.nombre}")
            return

        # Crear usuario ROOT
        email = "admin@ficem.org"
        password = "admin123"  # Contraseña temporal

        hashed_password = pwd_context.hash(password)

        nuevo_usuario = Usuario(
            email=email,
            password_hash=hashed_password,
            nombre="Administrador FICEM",
            rol=UserRole.ROOT,
            pais="LATAM",
            empresa_id=None,
            activo=True
        )

        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)

        print("=" * 60)
        print("✓ Usuario ROOT creado exitosamente")
        print("=" * 60)
        print(f"Email:    {email}")
        print(f"Password: {password}")
        print(f"Nombre:   {nuevo_usuario.nombre}")
        print(f"Rol:      {nuevo_usuario.rol.value}")
        print(f"País:     {nuevo_usuario.pais}")
        print("=" * 60)
        print("\n⚠️  IMPORTANTE: Cambiar la contraseña después del primer login")

    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear usuario: {str(e)}")
        raise
    finally:
        db.close()


def crear_usuarios_ejemplo():
    """Crear usuarios de ejemplo para testing"""
    db: Session = SessionLocal()

    try:
        usuarios_ejemplo = [
            {
                "email": "coord.peru@asocem.org",
                "password": "peru123",
                "nombre": "Coordinador Perú",
                "rol": UserRole.COORDINADOR_PAIS,
                "pais": "PERU"
            },
            {
                "email": "coord.colombia@ficem.org",
                "password": "colombia123",
                "nombre": "Coordinador Colombia",
                "rol": UserRole.COORDINADOR_PAIS,
                "pais": "COLOMBIA"
            },
            {
                "email": "admin.proceso@ficem.org",
                "password": "proceso123",
                "nombre": "Admin Procesos FICEM",
                "rol": UserRole.ADMIN_PROCESO,
                "pais": "LATAM"
            }
        ]

        print("\nCreando usuarios de ejemplo...")

        for user_data in usuarios_ejemplo:
            # Verificar si ya existe
            existing = db.query(Usuario).filter(Usuario.email == user_data["email"]).first()
            if existing:
                print(f"  • {user_data['email']} - Ya existe")
                continue

            hashed_password = pwd_context.hash(user_data["password"])

            nuevo_usuario = Usuario(
                email=user_data["email"],
                password_hash=hashed_password,
                nombre=user_data["nombre"],
                rol=user_data["rol"],
                pais=user_data["pais"],
                empresa_id=None,
                activo=True
            )

            db.add(nuevo_usuario)
            print(f"  ✓ {user_data['email']} - Creado (password: {user_data['password']})")

        db.commit()
        print("\n✓ Usuarios de ejemplo creados")

    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear usuarios de ejemplo: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Creando usuario administrador inicial...\n")
    crear_usuario_admin()

    # Preguntar si desea crear usuarios de ejemplo
    respuesta = input("\n¿Desea crear usuarios de ejemplo para testing? (s/n): ")
    if respuesta.lower() in ['s', 'si', 'y', 'yes']:
        crear_usuarios_ejemplo()

    print("\n✓ Proceso completado")