"""
SQL Tool para RAG
Piloto IA - FICEM BD

Permite al LLM consultar la base de datos PostgreSQL.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Agregar path para imports
sys.path.insert(0, str(Path.cwd()))

from database.connection import get_connection

load_dotenv()


class SQLTool:
    """
    Herramienta para consultar la base de datos desde el RAG.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa la conexión a la base de datos PostgreSQL.

        Args:
            db_path: Parámetro legacy, ignorado (PostgreSQL usa variables de entorno)
        """
        # Obtener engine de PostgreSQL
        self.conn = get_connection()

        # Cargar schema de tablas relevantes
        self.schema = self._get_schema()

    def _get_schema(self) -> str:
        """
        Obtiene el schema de las tablas principales desde PostgreSQL.

        Returns:
            String con descripción del schema
        """
        import pandas as pd

        # Tablas relevantes para el piloto IA
        tables = [
            "huella_concretos",
            "cementos",
            "plantas_latam",
            "tb_cubo",
            "indicadores",
            "entidades_m49"
        ]

        schema_parts = []

        for table in tables:
            try:
                # Obtener info de columnas desde PostgreSQL
                query = f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
                """
                df = pd.read_sql_query(query, self.conn)

                if not df.empty:
                    col_info = []
                    for _, row in df.iterrows():
                        col_name = row['column_name']
                        col_type = row['data_type']
                        col_info.append(f"  - {col_name} ({col_type})")

                    schema_parts.append(f"\n**{table}**:\n" + "\n".join(col_info))

            except Exception as e:
                # Tabla no existe o error de consulta
                print(f"Warning: No se pudo obtener schema de {table}: {e}")
                continue

        return "\n".join(schema_parts)

    def get_schema_description(self) -> str:
        """
        Retorna descripción del schema para el LLM.

        Returns:
            Descripción legible del schema
        """
        return f"""
Base de datos FICEM BD - Schema disponible:

{self.schema}

**Notas importantes**:
- remitos_concretos: Contiene 255,328 remitos con huella CO2, resistencia, intensidades A1-A5
- huella_concretos: Datos agregados de huella por año/origen
- cementos: Huellas CO2 de cemento por planta/año
- gnr_data: Datos de benchmarking de GCBA (Getting the Numbers Right)
- GCCA_EPD_5_1: Bandas de clasificación GCCA por producto
- plantas_latam: Plantas geolocalizadas en LATAM
"""

    def execute_query(self, query: str, max_rows: int = 100) -> Dict[str, Any]:
        """
        Ejecuta una consulta SQL y retorna resultados.

        Args:
            query: Query SQL a ejecutar
            max_rows: Máximo número de filas a retornar

        Returns:
            Diccionario con resultados y metadata
        """
        import pandas as pd

        try:
            # Validar que sea SELECT (seguridad)
            query_upper = query.strip().upper()
            if not query_upper.startswith("SELECT"):
                return {
                    "success": False,
                    "error": "Solo se permiten consultas SELECT",
                    "query": query
                }

            # Ejecutar query con pandas (compatible con PostgreSQL engine)
            df = pd.read_sql_query(query, self.conn)

            # Limitar filas si es necesario
            if len(df) > max_rows:
                df = df.head(max_rows)

            # Convertir a lista de diccionarios
            results = df.to_dict('records')
            columns = df.columns.tolist()

            return {
                "success": True,
                "query": query,
                "row_count": len(results),
                "rows": results,
                "columns": columns
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    def get_statistics(self, table: str, column: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas básicas de una columna.

        Args:
            table: Nombre de la tabla
            column: Nombre de la columna

        Returns:
            Diccionario con estadísticas
        """
        query = f"""
        SELECT
            COUNT({column}) as count,
            AVG({column}) as avg,
            MIN({column}) as min,
            MAX({column}) as max
        FROM {table}
        WHERE {column} IS NOT NULL
        """

        result = self.execute_query(query, max_rows=1)

        if result["success"] and result["rows"]:
            return result["rows"][0]
        else:
            return {"error": result.get("error", "No data")}

    def get_huella_promedio_compania(
        self,
        compania: str,
        año: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Obtiene huella promedio de una compañía desde huella_concretos (PostgreSQL).

        Args:
            compania: Nombre de la compañía (origen)
            año: Año (opcional)

        Returns:
            Diccionario con estadísticas
        """
        where_clause = f"WHERE LOWER(origen) = LOWER('{compania}')"
        if año:
            where_clause += f" AND año = {año}"

        query = f"""
        SELECT
            origen as compania,
            año,
            SUM(num_remitos) as num_remitos,
            AVG(huella_co2) as huella_promedio,
            AVG("REST") as resistencia_promedio,
            AVG(volumen) as cemento_promedio,
            SUM(volumen) as volumen_total
        FROM huella_concretos
        {where_clause}
        GROUP BY origen, año
        ORDER BY año DESC
        """

        return self.execute_query(query)

    def get_top_productos_huella(self, limit: int = 10) -> Dict[str, Any]:
        """
        Obtiene los productos con mayor huella de carbono desde huella_concretos (PostgreSQL).

        Args:
            limit: Número de productos a retornar

        Returns:
            Diccionario con resultados
        """
        query = f"""
        SELECT
            origen as compania,
            "REST" as resistencia,
            SUM(num_remitos) as num_remitos,
            AVG(huella_co2) as huella_promedio,
            AVG(volumen) as cemento_promedio,
            SUM(volumen) as volumen_total
        FROM huella_concretos
        WHERE huella_co2 IS NOT NULL
        GROUP BY origen, "REST"
        ORDER BY huella_promedio DESC
        LIMIT {limit}
        """

        return self.execute_query(query)

    def close(self):
        """Cierra la conexión a la base de datos."""
        # No necesitamos cerrar el engine de SQLAlchemy
        pass


# Funciones helper para usar desde LangChain
def get_huella_data(compania: str, año: Optional[int] = None) -> str:
    """
    Función helper para obtener datos de huella.

    Args:
        compania: Nombre de la compañía
        año: Año (opcional)

    Returns:
        String formateado con resultados
    """
    sql_tool = SQLTool()
    result = sql_tool.get_huella_promedio_compania(compania, año)
    sql_tool.close()

    if result["success"] and result["rows"]:
        data = result["rows"][0]
        return f"""
Datos de {compania} {f'en {año}' if año else ''}:
- Número de remitos: {data['num_remitos']:,}
- Huella promedio: {data['huella_promedio']:.2f} kg CO₂/m³
- Resistencia promedio: {data['resistencia_promedio']:.1f} MPa
- Contenido cemento promedio: {data['cemento_promedio']:.0f} kg/m³
- Volumen total: {data['volumen_total']:,.0f} m³
"""
    else:
        return f"No se encontraron datos para {compania}"


def execute_sql(query: str) -> str:
    """
    Ejecuta una consulta SQL y retorna resultados formateados.

    Args:
        query: Query SQL

    Returns:
        String con resultados
    """
    sql_tool = SQLTool()
    result = sql_tool.execute_query(query)
    sql_tool.close()

    if result["success"]:
        if result["rows"]:
            # Formatear primeras 10 filas
            output = f"Query ejecutado exitosamente. {result['row_count']} filas.\n\n"
            for i, row in enumerate(result["rows"][:10], 1):
                output += f"{i}. {row}\n"

            if result['row_count'] > 10:
                output += f"\n... y {result['row_count'] - 10} filas más."

            return output
        else:
            return "Query ejecutado exitosamente. 0 filas."
    else:
        return f"Error: {result['error']}"


# Ejemplo de uso
if __name__ == "__main__":
    sql_tool = SQLTool()

    print("=" * 70)
    print("TEST DE SQL TOOL")
    print("=" * 70)

    # Test 1: Schema
    print("\n1. Schema de la base de datos:")
    print(sql_tool.get_schema_description())

    # Test 2: Huella promedio por compañía
    print("\n2. Huella promedio MZMA 2024:")
    result = sql_tool.get_huella_promedio_compania("MZMA", 2024)
    if result["success"]:
        for row in result["rows"]:
            print(f"  - {row}")

    # Test 3: Top productos
    print("\n3. Top 5 productos con mayor huella:")
    result = sql_tool.get_top_productos_huella(5)
    if result["success"]:
        for i, row in enumerate(result["rows"], 1):
            print(f"  {i}. {row['compania']} - {row['resistencia']} MPa: {row['huella_promedio']:.2f} kg CO₂/m³")

    sql_tool.close()
    print("\n✅ Tests completados")
