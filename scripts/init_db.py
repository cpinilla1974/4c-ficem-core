"""
Script para inicializar la base de datos con datos de prueba
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import engine, SessionLocal, init_db
from database.models import Usuario, Empresa, UserRole, PerfilPlanta
from api.services.auth_service import get_password_hash


def create_test_data():
    """Crear datos de prueba"""
    db = SessionLocal()

    try:
        # Verificar si ya existen datos
        existing_users = db.query(Usuario).count()
        if existing_users > 0:
            print("⚠️  La base de datos ya contiene datos. Saltando creación de datos de prueba.")
            return

        print("Creando datos de prueba...")

        # Crear empresas
        empresa_peru = Empresa(
            nombre="Cementos Lima",
            pais="peru",
            perfil_planta=PerfilPlanta.INTEGRADA,
            contacto="Juan Pérez",
            email="contacto@cementoslima.com"
        )

        empresa_colombia = Empresa(
            nombre="Argos Colombia",
            pais="colombia",
            perfil_planta=PerfilPlanta.INTEGRADA,
            contacto="María García",
            email="contacto@argos.com"
        )

        empresa_chile = Empresa(
            nombre="Polpaico",
            pais="chile",
            perfil_planta=PerfilPlanta.MOLIENDA,
            contacto="Carlos Rojas",
            email="contacto@polpaico.cl"
        )

        db.add_all([empresa_peru, empresa_colombia, empresa_chile])
        db.flush()  # Para obtener los IDs

        # Crear usuarios
        usuarios = [
            # Operador FICEM
            Usuario(
                email="ficem@ficem.org",
                password_hash=get_password_hash("ficem123"),
                nombre="Operador FICEM",
                rol=UserRole.OPERADOR_FICEM,
                pais="regional",
                empresa_id=None
            ),
            # Coordinador Perú
            Usuario(
                email="coordinador@asocem.pe",
                password_hash=get_password_hash("peru123"),
                nombre="Coordinador ASOCEM",
                rol=UserRole.COORDINADOR_PAIS,
                pais="peru",
                empresa_id=None
            ),
            # Empresa Perú
            Usuario(
                email="empresa@cementoslima.com",
                password_hash=get_password_hash("lima123"),
                nombre="Usuario Cementos Lima",
                rol=UserRole.EMPRESA,
                pais="peru",
                empresa_id=empresa_peru.id
            ),
            # Coordinador Colombia
            Usuario(
                email="coordinador@asocreto.org",
                password_hash=get_password_hash("colombia123"),
                nombre="Coordinador ASOCRETO",
                rol=UserRole.COORDINADOR_PAIS,
                pais="colombia",
                empresa_id=None
            ),
            # Empresa Colombia
            Usuario(
                email="empresa@argos.com",
                password_hash=get_password_hash("argos123"),
                nombre="Usuario Argos",
                rol=UserRole.EMPRESA,
                pais="colombia",
                empresa_id=empresa_colombia.id
            ),
            # Empresa Chile
            Usuario(
                email="empresa@polpaico.cl",
                password_hash=get_password_hash("polpaico123"),
                nombre="Usuario Polpaico",
                rol=UserRole.EMPRESA,
                pais="chile",
                empresa_id=empresa_chile.id
            ),
        ]

        db.add_all(usuarios)
        db.commit()

        print("\n✅ Datos de prueba creados exitosamente\n")
        print("=" * 60)
        print("USUARIOS DE PRUEBA")
        print("=" * 60)
        print("\n🔹 OPERADOR FICEM:")
        print("   Email: ficem@ficem.org")
        print("   Password: ficem123")
        print("\n🔹 COORDINADOR PERÚ:")
        print("   Email: coordinador@asocem.pe")
        print("   Password: peru123")
        print("\n🔹 EMPRESA PERÚ (Cementos Lima):")
        print("   Email: empresa@cementoslima.com")
        print("   Password: lima123")
        print("\n🔹 COORDINADOR COLOMBIA:")
        print("   Email: coordinador@asocreto.org")
        print("   Password: colombia123")
        print("\n🔹 EMPRESA COLOMBIA (Argos):")
        print("   Email: empresa@argos.com")
        print("   Password: argos123")
        print("\n🔹 EMPRESA CHILE (Polpaico):")
        print("   Email: empresa@polpaico.cl")
        print("   Password: polpaico123")
        print("\n" + "=" * 60)

    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear datos de prueba: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Inicializando base de datos...")
    init_db()
    create_test_data()
