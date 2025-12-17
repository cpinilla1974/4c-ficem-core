"""
Migración: Actualizar sistema de usuarios y permisos v2
Fecha: 2025-12-10
Descripción:
  - Actualiza enum UserRole de 4 a 8 roles
  - Actualiza enum EstadoSubmission con flujo de doble aprobación
  - Agrega campo coordinador_ficem_id a procesos_mrv

Cambios de roles:
  Antes               →  Ahora
  ─────────────────────────────────
  EMPRESA             →  INFORMANTE_EMPRESA (migrado)
  COORDINADOR_PAIS    →  COORDINADOR_PAIS (sin cambio)
  OPERADOR_FICEM      →  ADMIN_PROCESO (migrado)
  (nuevo)             →  ROOT
  (nuevo)             →  VISOR_EMPRESA
  (nuevo)             →  SUPERVISOR_EMPRESA
  (nuevo)             →  EJECUTIVO_FICEM
  (nuevo)             →  AMIGO_FICEM
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from database.connection import engine


def migrate():
    """Ejecutar migración"""

    with engine.connect() as conn:
        print("=" * 60)
        print("MIGRACIÓN: Sistema de usuarios y permisos v2")
        print("=" * 60)

        # ============================================================
        # 1. AGREGAR NUEVOS VALORES AL ENUM UserRole
        # ============================================================
        print("\n[1/5] Agregando nuevos valores al enum userrole...")

        nuevos_roles = [
            'ROOT',
            'ADMIN_PROCESO',
            'EJECUTIVO_FICEM',
            'AMIGO_FICEM',
            'SUPERVISOR_EMPRESA',
            'INFORMANTE_EMPRESA',
            'VISOR_EMPRESA'
        ]

        for rol in nuevos_roles:
            try:
                conn.execute(text(f"ALTER TYPE userrole ADD VALUE IF NOT EXISTS '{rol}'"))
                print(f"  + Agregado: {rol}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  - Ya existe: {rol}")
                else:
                    print(f"  ! Error agregando {rol}: {e}")

        conn.commit()

        # ============================================================
        # 2. MIGRAR USUARIOS A NUEVOS ROLES
        # ============================================================
        print("\n[2/5] Migrando usuarios a nuevos roles...")

        # EMPRESA → INFORMANTE_EMPRESA
        result = conn.execute(text("""
            UPDATE usuarios SET rol = 'INFORMANTE_EMPRESA' WHERE rol = 'EMPRESA'
        """))
        print(f"  - EMPRESA → INFORMANTE_EMPRESA: {result.rowcount} usuarios")

        # OPERADOR_FICEM → ADMIN_PROCESO
        result = conn.execute(text("""
            UPDATE usuarios SET rol = 'ADMIN_PROCESO' WHERE rol = 'OPERADOR_FICEM'
        """))
        print(f"  - OPERADOR_FICEM → ADMIN_PROCESO: {result.rowcount} usuarios")

        conn.commit()

        # ============================================================
        # 3. CREAR ENUM EstadoSubmission Y TABLA SUBMISSIONS SI NO EXISTE
        # ============================================================
        print("\n[3/5] Verificando enum estadosubmission...")

        # Verificar si el enum existe
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'estadosubmission'
            )
        """))
        enum_exists = result.fetchone()[0]

        if not enum_exists:
            print("  - Creando enum estadosubmission...")
            conn.execute(text("""
                CREATE TYPE estadosubmission AS ENUM (
                    'BORRADOR',
                    'ENVIADO',
                    'APROBADO_EMPRESA',
                    'EN_REVISION_FICEM',
                    'APROBADO_FICEM',
                    'RECHAZADO_EMPRESA',
                    'RECHAZADO_FICEM',
                    'PUBLICADO',
                    'ARCHIVADO'
                )
            """))
            print("  + Enum estadosubmission creado")
        else:
            print("  - Enum estadosubmission ya existe, agregando valores...")
            nuevos_estados = [
                'APROBADO_EMPRESA',
                'EN_REVISION_FICEM',
                'APROBADO_FICEM',
                'RECHAZADO_EMPRESA',
                'RECHAZADO_FICEM',
                'PUBLICADO',
                'ARCHIVADO'
            ]
            for estado in nuevos_estados:
                try:
                    conn.execute(text(f"ALTER TYPE estadosubmission ADD VALUE IF NOT EXISTS '{estado}'"))
                    print(f"  + Agregado: {estado}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"  - Ya existe: {estado}")

        conn.commit()

        # ============================================================
        # 4. ACTUALIZAR SUBMISSIONS SI EXISTEN DATOS
        # ============================================================
        print("\n[4/5] Actualizando estados de submissions existentes...")

        # Verificar si la tabla submissions existe
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'submissions'
            )
        """))
        table_exists = result.fetchone()[0]

        if table_exists:
            # Migrar estados si hay datos con valores viejos
            try:
                result = conn.execute(text("""
                    UPDATE submissions SET estado_actual = 'APROBADO_FICEM'
                    WHERE estado_actual = 'APROBADO'
                """))
                if result.rowcount > 0:
                    print(f"  - APROBADO → APROBADO_FICEM: {result.rowcount}")

                result = conn.execute(text("""
                    UPDATE submissions SET estado_actual = 'RECHAZADO_FICEM'
                    WHERE estado_actual = 'RECHAZADO'
                """))
                if result.rowcount > 0:
                    print(f"  - RECHAZADO → RECHAZADO_FICEM: {result.rowcount}")

                result = conn.execute(text("""
                    UPDATE submissions SET estado_actual = 'EN_REVISION_FICEM'
                    WHERE estado_actual = 'EN_REVISION'
                """))
                if result.rowcount > 0:
                    print(f"  - EN_REVISION → EN_REVISION_FICEM: {result.rowcount}")

                print("  - Estados migrados correctamente")
            except Exception as e:
                print(f"  - No se requiere migración de estados: {e}")
        else:
            print("  - Tabla submissions no existe aún (se creará con los nuevos estados)")

        conn.commit()

        # ============================================================
        # 5. AGREGAR CAMPO COORDINADOR_FICEM_ID A PROCESOS
        # ============================================================
        print("\n[5/5] Verificando campo coordinador_ficem_id en procesos_mrv...")

        # Verificar si la tabla existe
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'procesos_mrv'
            )
        """))
        table_exists = result.fetchone()[0]

        if table_exists:
            # Verificar si la columna ya existe
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'procesos_mrv'
                AND column_name = 'coordinador_ficem_id'
            """))

            if result.fetchone() is None:
                conn.execute(text("""
                    ALTER TABLE procesos_mrv
                    ADD COLUMN coordinador_ficem_id INTEGER REFERENCES usuarios(id)
                """))
                print("  + Columna coordinador_ficem_id agregada")
            else:
                print("  - Columna coordinador_ficem_id ya existe")
        else:
            print("  - Tabla procesos_mrv no existe aún")

        conn.commit()

        print("\n" + "=" * 60)
        print("MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)

        # Resumen
        print("\nResumen de cambios:")
        print("  - Roles: EMPRESA→INFORMANTE_EMPRESA, OPERADOR_FICEM→ADMIN_PROCESO")
        print("  - Nuevos roles agregados: ROOT, EJECUTIVO_FICEM, AMIGO_FICEM,")
        print("                           SUPERVISOR_EMPRESA, VISOR_EMPRESA")
        print("  - Estados submission actualizados para flujo de doble aprobación")


def rollback():
    """Revertir migración (usar con precaución)"""
    print("⚠️  ADVERTENCIA: Esta operación revertirá los cambios de roles")
    print("    NOTA: No se pueden eliminar valores de un ENUM en PostgreSQL")
    print("          Solo se revertirán los datos de usuarios")
    confirmacion = input("Escriba 'CONFIRMAR' para continuar: ")

    if confirmacion != "CONFIRMAR":
        print("Operación cancelada")
        return

    with engine.connect() as conn:
        print("Revirtiendo cambios...")

        # Revertir roles de usuarios
        result = conn.execute(text("""
            UPDATE usuarios SET rol = 'EMPRESA'
            WHERE rol IN ('INFORMANTE_EMPRESA', 'VISOR_EMPRESA', 'SUPERVISOR_EMPRESA')
        """))
        print(f"  - Revertidos a EMPRESA: {result.rowcount}")

        result = conn.execute(text("""
            UPDATE usuarios SET rol = 'OPERADOR_FICEM'
            WHERE rol IN ('ADMIN_PROCESO', 'EJECUTIVO_FICEM', 'AMIGO_FICEM', 'ROOT')
        """))
        print(f"  - Revertidos a OPERADOR_FICEM: {result.rowcount}")

        # Eliminar columna coordinador_ficem_id
        try:
            conn.execute(text("""
                ALTER TABLE procesos_mrv DROP COLUMN IF EXISTS coordinador_ficem_id
            """))
            print("  - Columna coordinador_ficem_id eliminada")
        except:
            pass

        conn.commit()

        print("\n✅ Rollback completado")
        print("   NOTA: Los valores del ENUM no se eliminaron (limitación de PostgreSQL)")


def status():
    """Mostrar estado actual de roles y estados"""
    with engine.connect() as conn:
        print("\n=== ESTADO ACTUAL ===\n")

        # Valores del enum userrole
        print("Valores en enum userrole:")
        result = conn.execute(text("""
            SELECT enumlabel
            FROM pg_enum e
            JOIN pg_type t ON e.enumtypid = t.oid
            WHERE t.typname = 'userrole'
            ORDER BY e.enumsortorder
        """))
        for row in result:
            print(f"  - {row.enumlabel}")

        # Contar usuarios por rol
        print("\nUsuarios por rol:")
        result = conn.execute(text("""
            SELECT rol, COUNT(*) as count
            FROM usuarios
            GROUP BY rol
            ORDER BY rol
        """))
        for row in result:
            print(f"  - {row.rol}: {row.count}")

        # Verificar tabla submissions
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'submissions'
            )
        """))
        if result.fetchone()[0]:
            print("\nSubmissions por estado:")
            result = conn.execute(text("""
                SELECT estado_actual, COUNT(*) as count
                FROM submissions
                GROUP BY estado_actual
                ORDER BY estado_actual
            """))
            rows = result.fetchall()
            if rows:
                for row in rows:
                    print(f"  - {row.estado_actual}: {row.count}")
            else:
                print("  (no hay submissions)")
        else:
            print("\nTabla submissions: No existe")

        # Verificar columna coordinador_ficem_id
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'procesos_mrv'
            AND column_name = 'coordinador_ficem_id'
        """))
        if result.fetchone():
            print("\nColumna coordinador_ficem_id: ✅ Existe")
        else:
            print("\nColumna coordinador_ficem_id: ❌ No existe")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Migración de usuarios y permisos v2')
    parser.add_argument('--rollback', action='store_true', help='Revertir migración')
    parser.add_argument('--status', action='store_true', help='Mostrar estado actual')

    args = parser.parse_args()

    if args.rollback:
        rollback()
    elif args.status:
        status()
    else:
        migrate()