"""
Script para crear usuarios y empresas de prueba para Argentina
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from database.models import Empresa, Usuario, UserRole
from api.services.auth_service import get_password_hash

def seed_argentina():
    db = SessionLocal()

    try:
        # Contraseña por defecto para todos los usuarios de prueba
        default_password = "demo123"
        password_hash = get_password_hash(default_password)

        print("\n" + "=" * 80)
        print("CREANDO DATOS DE PRUEBA PARA ARGENTINA")
        print("=" * 80)

        # 1. Crear empresas argentinas
        empresas_data = [
            {
                "nombre": "Holcim Argentina",
                "pais": "argentina",
                "perfil_planta": "integrada",
                "email": "contacto@holcim.com.ar",
                "contacto": "Holcim Argentina S.A."
            },
            {
                "nombre": "Loma Negra",
                "pais": "argentina",
                "perfil_planta": "integrada",
                "email": "contacto@lomanegra.com",
                "contacto": "Loma Negra C.I.A.S.A."
            },
            {
                "nombre": "Avellaneda",
                "pais": "argentina",
                "perfil_planta": "molienda",
                "email": "contacto@avellaneda.com",
                "contacto": "Cementos Avellaneda S.A."
            },
            {
                "nombre": "Petroquímica Comodoro Rivadavia",
                "pais": "argentina",
                "perfil_planta": "integrada",
                "email": "contacto@pcr.com.ar",
                "contacto": "PCR S.A."
            }
        ]

        empresas_creadas = {}

        for emp_data in empresas_data:
            # Verificar si ya existe
            existing = db.query(Empresa).filter(Empresa.nombre == emp_data["nombre"]).first()

            if existing:
                print(f"\n✓ Empresa ya existe: {emp_data['nombre']} (ID: {existing.id})")
                empresas_creadas[emp_data["nombre"]] = existing
            else:
                empresa = Empresa(**emp_data)
                db.add(empresa)
                db.flush()
                print(f"\n✓ Empresa creada: {emp_data['nombre']} (ID: {empresa.id})")
                empresas_creadas[emp_data["nombre"]] = empresa

        db.commit()

        # 2. Crear usuarios para cada empresa
        usuarios_data = [
            # Holcim Argentina
            {
                "email": "informante@holcim.com.ar",
                "nombre": "Juan Pérez - Informante Holcim",
                "rol": UserRole.INFORMANTE_EMPRESA,
                "pais": "argentina",
                "empresa": "Holcim Argentina"
            },
            {
                "email": "supervisor@holcim.com.ar",
                "nombre": "María García - Supervisor Holcim",
                "rol": UserRole.SUPERVISOR_EMPRESA,
                "pais": "argentina",
                "empresa": "Holcim Argentina"
            },
            {
                "email": "visor@holcim.com.ar",
                "nombre": "Carlos López - Visor Holcim",
                "rol": UserRole.VISOR_EMPRESA,
                "pais": "argentina",
                "empresa": "Holcim Argentina"
            },

            # Loma Negra
            {
                "email": "informante@lomanegra.com",
                "nombre": "Ana Martínez - Informante Loma Negra",
                "rol": UserRole.INFORMANTE_EMPRESA,
                "pais": "argentina",
                "empresa": "Loma Negra"
            },
            {
                "email": "supervisor@lomanegra.com",
                "nombre": "Roberto Sánchez - Supervisor Loma Negra",
                "rol": UserRole.SUPERVISOR_EMPRESA,
                "pais": "argentina",
                "empresa": "Loma Negra"
            },
            {
                "email": "visor@lomanegra.com",
                "nombre": "Laura Fernández - Visor Loma Negra",
                "rol": UserRole.VISOR_EMPRESA,
                "pais": "argentina",
                "empresa": "Loma Negra"
            },

            # Avellaneda
            {
                "email": "informante@avellaneda.com",
                "nombre": "Diego Torres - Informante Avellaneda",
                "rol": UserRole.INFORMANTE_EMPRESA,
                "pais": "argentina",
                "empresa": "Avellaneda"
            },
            {
                "email": "supervisor@avellaneda.com",
                "nombre": "Patricia Romero - Supervisor Avellaneda",
                "rol": UserRole.SUPERVISOR_EMPRESA,
                "pais": "argentina",
                "empresa": "Avellaneda"
            },

            # PCR
            {
                "email": "informante@pcr.com.ar",
                "nombre": "Martín González - Informante PCR",
                "rol": UserRole.INFORMANTE_EMPRESA,
                "pais": "argentina",
                "empresa": "Petroquímica Comodoro Rivadavia"
            },
            {
                "email": "supervisor@pcr.com.ar",
                "nombre": "Silvia Ramírez - Supervisor PCR",
                "rol": UserRole.SUPERVISOR_EMPRESA,
                "pais": "argentina",
                "empresa": "Petroquímica Comodoro Rivadavia"
            },

            # Coordinador AFCP (Asociación Argentina)
            {
                "email": "coordinador@afcp.org.ar",
                "nombre": "Coordinador AFCP Argentina",
                "rol": UserRole.COORDINADOR_PAIS,
                "pais": "argentina",
                "empresa": None
            },
        ]

        print("\n" + "-" * 80)
        print("CREANDO USUARIOS")
        print("-" * 80)

        usuarios_creados = 0

        for usr_data in usuarios_data:
            # Verificar si ya existe
            existing = db.query(Usuario).filter(Usuario.email == usr_data["email"]).first()

            if existing:
                print(f"  • Usuario ya existe: {usr_data['email']}")
                continue

            # Obtener ID de empresa si corresponde
            empresa_id = None
            if usr_data["empresa"]:
                empresa_id = empresas_creadas[usr_data["empresa"]].id

            # Crear usuario
            usuario = Usuario(
                email=usr_data["email"],
                password_hash=password_hash,
                nombre=usr_data["nombre"],
                rol=usr_data["rol"],
                pais=usr_data["pais"],
                empresa_id=empresa_id,
                activo=True
            )

            db.add(usuario)
            usuarios_creados += 1
            print(f"  ✓ Creado: {usr_data['email']:40} | Rol: {usr_data['rol'].value}")

        db.commit()

        print("\n" + "=" * 80)
        print(f"RESUMEN:")
        print(f"  • Empresas en BD: {len(empresas_creadas)}")
        print(f"  • Usuarios creados: {usuarios_creados}")
        print(f"  • Contraseña para todos: {default_password}")
        print("=" * 80)
        print("\nUSUARIOS DE PRUEBA CREADOS:")
        print("-" * 80)

        # Listar todos los usuarios de Argentina
        usuarios_arg = db.query(Usuario).filter(Usuario.pais == "argentina").all()

        for u in usuarios_arg:
            empresa_nombre = ""
            if u.empresa_id:
                empresa = db.query(Empresa).filter(Empresa.id == u.empresa_id).first()
                empresa_nombre = f" ({empresa.nombre})" if empresa else ""

            print(f"  Email: {u.email:40} | Rol: {u.rol.value:25}{empresa_nombre}")

        print("-" * 80)
        print("\n✓ Script completado exitosamente\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_argentina()
