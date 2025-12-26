"""
Script para inicializar la base de datos con datos de prueba

NOTA: Este script usa credenciales de desarrollo.
Ver storage/keys/DEV_CREDENTIALS.md para los valores.
Configura las variables en tu .env antes de ejecutar.
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import engine, SessionLocal, init_db
from database.models import Usuario, Empresa, UserRole, PerfilPlanta
from api.services.auth_service import get_password_hash

# Leer credenciales de variables de entorno
FICEM_PASSWORD = os.getenv("FICEM_PASSWORD", "")
COORD_PERU_PASSWORD = os.getenv("COORD_PERU_PASSWORD", "")
COORD_COLOMBIA_PASSWORD = os.getenv("COORD_COLOMBIA_PASSWORD", "")
EMPRESA_PERU_PASSWORD = os.getenv("EMPRESA_PERU_PASSWORD", "")
EMPRESA_COLOMBIA_PASSWORD = os.getenv("EMPRESA_COLOMBIA_PASSWORD", "")
EMPRESA_CHILE_PASSWORD = os.getenv("EMPRESA_CHILE_PASSWORD", "")


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

        # Verificar credenciales
        missing_creds = []
        if not FICEM_PASSWORD:
            missing_creds.append("FICEM_PASSWORD")
        if not COORD_PERU_PASSWORD:
            missing_creds.append("COORD_PERU_PASSWORD")
        if not COORD_COLOMBIA_PASSWORD:
            missing_creds.append("COORD_COLOMBIA_PASSWORD")
        if not EMPRESA_PERU_PASSWORD:
            missing_creds.append("EMPRESA_PERU_PASSWORD")
        if not EMPRESA_COLOMBIA_PASSWORD:
            missing_creds.append("EMPRESA_COLOMBIA_PASSWORD")
        if not EMPRESA_CHILE_PASSWORD:
            missing_creds.append("EMPRESA_CHILE_PASSWORD")

        if missing_creds:
            print("❌ Error: Variables de entorno no configuradas:")
            for cred in missing_creds:
                print(f"   - {cred}")
            print("\nConfigura estas variables en tu .env")
            print("Ver storage/keys/DEV_CREDENTIALS.md para valores de desarrollo")
            return

        # Crear usuarios
        usuarios = [
            # Operador FICEM
            Usuario(
                email="ficem@ficem.org",
                password_hash=get_password_hash(FICEM_PASSWORD),
                nombre="Operador FICEM",
                rol=UserRole.OPERADOR_FICEM,
                pais="regional",
                empresa_id=None
            ),
            # Coordinador Perú
            Usuario(
                email="coordinador@asocem.pe",
                password_hash=get_password_hash(COORD_PERU_PASSWORD),
                nombre="Coordinador ASOCEM",
                rol=UserRole.COORDINADOR_PAIS,
                pais="peru",
                empresa_id=None
            ),
            # Empresa Perú
            Usuario(
                email="empresa@cementoslima.com",
                password_hash=get_password_hash(EMPRESA_PERU_PASSWORD),
                nombre="Usuario Cementos Lima",
                rol=UserRole.EMPRESA,
                pais="peru",
                empresa_id=empresa_peru.id
            ),
            # Coordinador Colombia
            Usuario(
                email="coordinador@asocreto.org",
                password_hash=get_password_hash(COORD_COLOMBIA_PASSWORD),
                nombre="Coordinador ASOCRETO",
                rol=UserRole.COORDINADOR_PAIS,
                pais="colombia",
                empresa_id=None
            ),
            # Empresa Colombia
            Usuario(
                email="empresa@argos.com",
                password_hash=get_password_hash(EMPRESA_COLOMBIA_PASSWORD),
                nombre="Usuario Argos",
                rol=UserRole.EMPRESA,
                pais="colombia",
                empresa_id=empresa_colombia.id
            ),
            # Empresa Chile
            Usuario(
                email="empresa@polpaico.cl",
                password_hash=get_password_hash(EMPRESA_CHILE_PASSWORD),
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
        print("USUARIOS DE PRUEBA (passwords en storage/keys/DEV_CREDENTIALS.md)")
        print("=" * 60)
        print("\n🔹 OPERADOR FICEM: ficem@ficem.org")
        print("🔹 COORDINADOR PERÚ: coordinador@asocem.pe")
        print("🔹 EMPRESA PERÚ: empresa@cementoslima.com")
        print("🔹 COORDINADOR COLOMBIA: coordinador@asocreto.org")
        print("🔹 EMPRESA COLOMBIA: empresa@argos.com")
        print("🔹 EMPRESA CHILE: empresa@polpaico.cl")
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
