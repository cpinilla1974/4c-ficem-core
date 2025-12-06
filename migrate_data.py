"""
Script para migrar datos desde SQLite de ficem_bd a PostgreSQL de latam4c
"""
import sqlite3
import pandas as pd
from database import get_engine
from sqlalchemy import text

# Tablas a migrar
TABLAS = [
    'huella_concretos',
    'cementos',
    'tb_cubo',
    'indicadores',
    'entidades_m49'
]

# Path a BD SQLite origen
SQLITE_DB = '/home/cpinilla/databases/ficem_bd/data/ficem_bd.db'

def migrar_tabla(nombre_tabla, conn_sqlite, engine_pg):
    """Migra una tabla desde SQLite a PostgreSQL"""
    print(f"\n📦 Migrando tabla: {nombre_tabla}")

    try:
        # Leer datos desde SQLite
        df = pd.read_sql_query(f"SELECT * FROM {nombre_tabla}", conn_sqlite)
        print(f"  ✓ Leídos {len(df)} registros desde SQLite")

        # Escribir a PostgreSQL
        df.to_sql(nombre_tabla, engine_pg, if_exists='replace', index=False)
        print(f"  ✓ Escritos {len(df)} registros en PostgreSQL")

        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("MIGRACIÓN DE DATOS: ficem_bd (SQLite) → latam4c (PostgreSQL)")
    print("=" * 60)

    # Conectar a SQLite (origen)
    print(f"\n🔌 Conectando a SQLite: {SQLITE_DB}")
    conn_sqlite = sqlite3.connect(SQLITE_DB)

    # Conectar a PostgreSQL (destino)
    print("🔌 Conectando a PostgreSQL: latam4c_db")
    engine_pg = get_engine()

    # Migrar cada tabla
    print(f"\n📋 Migrando {len(TABLAS)} tablas...")
    exitos = 0

    for tabla in TABLAS:
        if migrar_tabla(tabla, conn_sqlite, engine_pg):
            exitos += 1

    # Cerrar conexiones
    conn_sqlite.close()
    engine_pg.dispose()

    # Resumen
    print("\n" + "=" * 60)
    print(f"✅ Migración completada: {exitos}/{len(TABLAS)} tablas migradas")
    print("=" * 60)

if __name__ == "__main__":
    main()
