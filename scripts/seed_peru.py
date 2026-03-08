"""
Script para crear usuarios y empresas de Perú

Basado en: config/countries/peru.yaml
Fuente original: 4c-peru/docs/REQUISITOS_PERU.md

Mejoras sobre seed_argentina_users.py:
- Lee configuración desde YAML
- Genera reporte de credenciales automáticamente
- Mejor manejo de errores
- Soporte para dry-run
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from database.connection import SessionLocal
from database.models import Empresa, Usuario, UserRole, PerfilPlanta
from api.services.auth_service import get_password_hash


# Mapeo de strings a enums
ROLE_MAP = {
    "INFORMANTE_EMPRESA": UserRole.INFORMANTE_EMPRESA,
    "SUPERVISOR_EMPRESA": UserRole.SUPERVISOR_EMPRESA,
    "VISOR_EMPRESA": UserRole.VISOR_EMPRESA,
    "COORDINADOR_PAIS": UserRole.COORDINADOR_PAIS,
}

PERFIL_MAP = {
    "integrada": PerfilPlanta.INTEGRADA,
    "molienda": PerfilPlanta.MOLIENDA,
    "concreto": PerfilPlanta.CONCRETO,
}


def load_config(country_code: str) -> dict:
    """Cargar configuración YAML del país"""
    config_path = Path(__file__).parent.parent / "config" / "countries" / f"{country_code}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"No existe configuración: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_credentials_report(config: dict, usuarios_info: list, output_path: Path):
    """Generar archivo markdown con credenciales"""
    pais = config["pais"]

    content = f"""# Credenciales - {pais['nombre']}

> Generado automáticamente: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
>
> **IMPORTANTE**: Este archivo contiene credenciales. NO subir a Git.

---

## Coordinador de País

| Campo | Valor |
|-------|-------|
| Email | `{config['coordinador']['email']}` |
| Password | `{config['coordinador']['password']}` |
| Rol | COORDINADOR_PAIS |
| Organización | {config['coordinador']['organizacion']} |

---

## Usuarios por Empresa

"""

    for empresa in config["empresas"]:
        content += f"### {empresa['nombre']}\n\n"
        content += "| Email | Password | Rol |\n"
        content += "|-------|----------|-----|\n"

        for usuario in empresa["usuarios"]:
            content += f"| `{usuario['email']}` | `{usuario['password']}` | {usuario['rol']} |\n"

        content += "\n"

    content += f"""---

## Resumen

- **País**: {pais['nombre']} (`{pais['codigo']}`)
- **Empresas**: {len(config['empresas'])}
- **Usuarios totales**: {sum(len(e['usuarios']) for e in config['empresas']) + 1}

---

## Notas

1. Todas las contraseñas son para **desarrollo/pruebas**
2. En producción, generar contraseñas seguras
3. El coordinador puede ver todos los datos de {pais['nombre']}
4. Los usuarios de empresa solo ven datos de su empresa

---

**Generado por**: `scripts/seed_peru.py`
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def seed_peru(dry_run: bool = False):
    """
    Ejecutar seed de Perú

    Args:
        dry_run: Si True, solo muestra qué haría sin crear nada
    """
    # Cargar configuración
    config = load_config("peru")
    pais = config["pais"]

    print("\n" + "=" * 80)
    print(f"{'[DRY RUN] ' if dry_run else ''}CREANDO DATOS PARA {pais['nombre'].upper()}")
    print("=" * 80)

    if dry_run:
        print("\nModo DRY RUN: No se creará nada en la base de datos\n")

    db = SessionLocal()
    usuarios_info = []

    try:
        # Password hash común para usuarios de prueba
        default_hash = get_password_hash("demo123")

        # =====================================================================
        # 1. CREAR EMPRESAS
        # =====================================================================
        print("\n" + "-" * 80)
        print("EMPRESAS")
        print("-" * 80)

        empresas_creadas = {}

        for emp_data in config["empresas"]:
            nombre = emp_data["nombre"]

            # Verificar si existe
            existing = db.query(Empresa).filter(
                Empresa.nombre == nombre,
                Empresa.pais == pais["codigo"]
            ).first()

            if existing:
                print(f"  [EXISTS] {nombre} (ID: {existing.id})")
                empresas_creadas[nombre] = existing
            else:
                if not dry_run:
                    empresa = Empresa(
                        nombre=nombre,
                        pais=pais["codigo"],
                        perfil_planta=PERFIL_MAP[emp_data["perfil_planta"]],
                        email=emp_data.get("email"),
                        contacto=emp_data.get("contacto"),
                        activo=True
                    )
                    db.add(empresa)
                    db.flush()
                    empresas_creadas[nombre] = empresa
                    print(f"  [CREATE] {nombre} (ID: {empresa.id})")
                else:
                    print(f"  [WOULD CREATE] {nombre}")
                    empresas_creadas[nombre] = None

        if not dry_run:
            db.commit()

        # =====================================================================
        # 2. CREAR COORDINADOR DE PAÍS
        # =====================================================================
        print("\n" + "-" * 80)
        print("COORDINADOR DE PAÍS")
        print("-" * 80)

        coord = config["coordinador"]
        existing_coord = db.query(Usuario).filter(Usuario.email == coord["email"]).first()

        if existing_coord:
            print(f"  [EXISTS] {coord['email']}")
        else:
            if not dry_run:
                coord_hash = get_password_hash(coord["password"])
                coordinador = Usuario(
                    email=coord["email"],
                    password_hash=coord_hash,
                    nombre=coord["nombre"],
                    rol=UserRole.COORDINADOR_PAIS,
                    pais=pais["codigo"],
                    empresa_id=None,
                    activo=True
                )
                db.add(coordinador)
                db.flush()
                print(f"  [CREATE] {coord['email']} | {coord['nombre']}")
            else:
                print(f"  [WOULD CREATE] {coord['email']} | COORDINADOR_PAIS")

        usuarios_info.append({
            "email": coord["email"],
            "password": coord["password"],
            "rol": "COORDINADOR_PAIS",
            "empresa": coord["organizacion"]
        })

        # =====================================================================
        # 3. CREAR USUARIOS DE EMPRESAS
        # =====================================================================
        print("\n" + "-" * 80)
        print("USUARIOS DE EMPRESAS")
        print("-" * 80)

        usuarios_creados = 0

        for emp_data in config["empresas"]:
            empresa_nombre = emp_data["nombre"]
            empresa_obj = empresas_creadas.get(empresa_nombre)
            empresa_id = empresa_obj.id if empresa_obj else None

            print(f"\n  {empresa_nombre}:")

            for usr in emp_data["usuarios"]:
                existing_usr = db.query(Usuario).filter(Usuario.email == usr["email"]).first()

                if existing_usr:
                    print(f"    [EXISTS] {usr['email']}")
                else:
                    if not dry_run:
                        usr_hash = get_password_hash(usr["password"])
                        usuario = Usuario(
                            email=usr["email"],
                            password_hash=usr_hash,
                            nombre=usr["nombre"],
                            rol=ROLE_MAP[usr["rol"]],
                            pais=pais["codigo"],
                            empresa_id=empresa_id,
                            activo=True
                        )
                        db.add(usuario)
                        usuarios_creados += 1
                        print(f"    [CREATE] {usr['email']:40} | {usr['rol']}")
                    else:
                        print(f"    [WOULD CREATE] {usr['email']:40} | {usr['rol']}")

                usuarios_info.append({
                    "email": usr["email"],
                    "password": usr["password"],
                    "rol": usr["rol"],
                    "empresa": empresa_nombre
                })

        if not dry_run:
            db.commit()

        # =====================================================================
        # 4. GENERAR REPORTE DE CREDENCIALES
        # =====================================================================
        if not dry_run:
            output_path = Path(__file__).parent.parent / "storage" / "keys" / f"CREDENTIALS_{pais['codigo'].upper()}.md"
            generate_credentials_report(config, usuarios_info, output_path)
            print(f"\n  Credenciales guardadas en: {output_path}")

        # =====================================================================
        # RESUMEN
        # =====================================================================
        print("\n" + "=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"  País: {pais['nombre']} ({pais['codigo']})")
        print(f"  Empresas: {len(config['empresas'])}")
        print(f"  Coordinador: {coord['email']}")
        print(f"  Usuarios empresa: {sum(len(e['usuarios']) for e in config['empresas'])}")
        print(f"  Total usuarios: {sum(len(e['usuarios']) for e in config['empresas']) + 1}")

        if dry_run:
            print("\n  [DRY RUN] No se realizaron cambios en la base de datos")
        else:
            print(f"\n  Usuarios nuevos creados: {usuarios_creados + (0 if existing_coord else 1)}")

        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed de datos para Perú")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar qué se crearía sin hacer cambios"
    )

    args = parser.parse_args()
    seed_peru(dry_run=args.dry_run)