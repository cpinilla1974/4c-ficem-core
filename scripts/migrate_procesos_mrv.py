"""
Migración: Crear tablas procesos_mrv y submissions
Fecha: 2025-12-10
Descripción: Sistema de motor de procesos multi-país configurable
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
        print("Creando tabla procesos_mrv...")

        # Crear tabla procesos_mrv
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS procesos_mrv (
                id VARCHAR(100) PRIMARY KEY,
                pais_iso CHAR(2) NOT NULL,
                tipo VARCHAR(50) NOT NULL,
                nombre VARCHAR(200) NOT NULL,
                descripcion TEXT,
                ciclo VARCHAR(20),
                estado VARCHAR(20) DEFAULT 'activo' NOT NULL,
                config JSONB NOT NULL,
                created_by INTEGER REFERENCES usuarios(id),
                created_at TIMESTAMP DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW() NOT NULL,

                CONSTRAINT unique_proceso_ciclo UNIQUE (pais_iso, tipo, ciclo),
                CONSTRAINT check_estado CHECK (estado IN ('borrador', 'activo', 'cerrado', 'archivado'))
            )
        """))

        # Índices para procesos_mrv
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_procesos_pais ON procesos_mrv(pais_iso)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_procesos_estado ON procesos_mrv(estado)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_procesos_tipo ON procesos_mrv(tipo)
        """))

        print("Creando tabla submissions...")

        # Crear tabla submissions
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS submissions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                proceso_id VARCHAR(100) NOT NULL REFERENCES procesos_mrv(id) ON DELETE CASCADE,
                empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                planta_id INTEGER REFERENCES plantas(id) ON DELETE SET NULL,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id),

                estado_actual VARCHAR(50) NOT NULL,
                workflow_history JSONB DEFAULT '[]'::jsonb NOT NULL,

                archivo_excel JSONB,
                datos_extraidos JSONB,
                validaciones JSONB DEFAULT '[]'::jsonb,
                comentarios JSONB DEFAULT '[]'::jsonb,
                resultados_calculos JSONB,

                created_at TIMESTAMP DEFAULT NOW() NOT NULL,
                submitted_at TIMESTAMP,
                reviewed_at TIMESTAMP,
                approved_at TIMESTAMP,

                CONSTRAINT check_estado CHECK (estado_actual IN (
                    'borrador', 'enviado', 'en_revision', 'aprobado',
                    'rechazado', 'publicado', 'archivado'
                ))
            )
        """))

        # Índices para submissions
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_submissions_proceso ON submissions(proceso_id)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_submissions_empresa ON submissions(empresa_id)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_submissions_estado ON submissions(estado_actual)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_submissions_usuario ON submissions(usuario_id)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_submissions_created ON submissions(created_at DESC)
        """))

        # Índices JSONB para búsquedas eficientes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_submissions_config_gin
            ON submissions USING gin(datos_extraidos)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_procesos_config_gin
            ON procesos_mrv USING gin(config)
        """))

        conn.commit()

        print("✅ Migración completada exitosamente")
        print("\nTablas creadas:")
        print("  - procesos_mrv (con 3 índices)")
        print("  - submissions (con 6 índices)")


def rollback():
    """Revertir migración (usar con precaución)"""
    print("⚠️  ADVERTENCIA: Esta operación eliminará las tablas procesos_mrv y submissions")
    confirmacion = input("Escriba 'CONFIRMAR' para continuar: ")

    if confirmacion != "CONFIRMAR":
        print("Operación cancelada")
        return

    with engine.connect() as conn:
        print("Eliminando tablas...")

        conn.execute(text("DROP TABLE IF EXISTS submissions CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS procesos_mrv CASCADE"))

        conn.commit()

        print("✅ Rollback completado")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Migración de Motor de Procesos MRV')
    parser.add_argument('--rollback', action='store_true', help='Revertir migración')

    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        migrate()