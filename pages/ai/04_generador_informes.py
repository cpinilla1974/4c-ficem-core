"""
Generador de Informes
Piloto IA - FICEM BD

Interfaz para generar informes de benchmarking en PDF y Excel.
"""

import streamlit as st
import sys
from pathlib import Path
import os

# Agregar path para imports
sys.path.insert(0, str(Path.cwd()))

from ai_modules.report_generator.pdf_generator import BenchmarkingReportPDF
from ai_modules.report_generator.excel_generator import BenchmarkingReportExcel
from ai_modules.rag.sql_tool import SQLTool


def app():
    st.title("📊 Generador de Informes de Benchmarking")
    st.markdown("### Genera informes personalizados con análisis de IA")

    # Sidebar con configuración
    with st.sidebar:
        st.header("⚙️ Configuración")

        modelo_tipo = st.radio(
            "Proveedor LLM",
            options=["Ollama (Local)", "Claude (API)"],
            index=0,
            help="Modelo para generar análisis"
        )

        use_claude = modelo_tipo == "Claude (API)"

        if use_claude:
            modelo = st.selectbox(
                "Modelo Claude",
                options=[
                    "claude-sonnet-4-5-20250929",
                    "claude-3-5-sonnet-20241022",
                    "claude-3-haiku-20240307"
                ],
                index=0
            )
        else:
            modelo = st.selectbox(
                "Modelo Ollama",
                options=["qwen2.5:3b", "qwen2.5:7b", "qwen2.5:1.5b"],
                index=0
            )

        st.divider()

        formato = st.radio(
            "Formato de Salida",
            options=["PDF", "Excel", "Ambos"],
            index=0
        )

        st.divider()

        st.info("💡 Los informes incluyen:\n\n"
                "- Métricas de huella de carbono\n"
                "- Comparación con benchmarks\n"
                "- Análisis generado por IA\n"
                "- Gráficos y visualizaciones\n"
                "- Top productos por volumen")

    # Inicializar SQL tool para obtener compañías disponibles
    @st.cache_resource
    def get_sql_tool():
        return SQLTool()

    sql_tool = get_sql_tool()

    # Obtener lista de compañías desde huella_concretos (PostgreSQL)
    query_companias = """
    SELECT DISTINCT origen as compania
    FROM huella_concretos
    ORDER BY origen
    """
    result = sql_tool.execute_query(query_companias)
    companias = [row['compania'] for row in result['rows']] if result['success'] else []

    # Obtener años disponibles
    query_años = """
    SELECT DISTINCT año
    FROM huella_concretos
    WHERE año IS NOT NULL
    ORDER BY año DESC
    """
    result_años = sql_tool.execute_query(query_años)
    años = [row['año'] for row in result_años['rows']] if result_años['success'] else []

    # Formulario principal
    st.header("📋 Seleccionar Datos")

    col1, col2 = st.columns(2)

    with col1:
        compania_seleccionada = st.selectbox(
            "Compañía",
            options=companias,
            help="Selecciona la compañía para el informe"
        )

    with col2:
        año_options = ["Todos"] + [str(año) for año in años]
        año_seleccionado = st.selectbox(
            "Año",
            options=año_options,
            index=0,
            help="Selecciona el año (o 'Todos' para histórico)"
        )

    año = None if año_seleccionado == "Todos" else int(año_seleccionado)

    # Tipo de benchmark
    benchmark_type = st.selectbox(
        "Tipo de Benchmark",
        options=["GCCA", "GNR", "Regional"],
        index=0,
        help="Selecciona el tipo de benchmark para comparación"
    ).lower()

    st.divider()

    # Vista previa de datos
    st.header("👀 Vista Previa")

    if compania_seleccionada:
        result = sql_tool.get_huella_promedio_compania(compania_seleccionada, año)

        if result["success"] and result["rows"]:
            data = result["rows"][0]

            # Tarjetas con métricas
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Remitos",
                    f"{data.get('num_remitos', 0):,}"
                )

            with col2:
                st.metric(
                    "Huella CO₂",
                    f"{data.get('huella_promedio', 0):.2f}",
                    help="kg CO₂/m³"
                )

            with col3:
                st.metric(
                    "Resistencia",
                    f"{data.get('resistencia_promedio', 0):.1f}",
                    help="MPa"
                )

            with col4:
                st.metric(
                    "Volumen Total",
                    f"{data.get('volumen_total', 0):,.0f}",
                    help="m³"
                )

            st.divider()

            # Botón para generar informe
            st.header("🚀 Generar Informe")

            if st.button("📄 Generar Informe", type="primary", use_container_width=True):
                
                with st.spinner("Generando informe con IA... Esto puede tomar 1-2 minutos."):
                    try:
                        # Crear directorio de reportes si no existe
                        reports_dir = "./reports"
                        os.makedirs(reports_dir, exist_ok=True)

                        files_generated = []

                        # Generar PDF
                        if formato in ["PDF", "Ambos"]:
                            st.info("📄 Generando PDF...")
                            pdf_gen = BenchmarkingReportPDF(
                                llm_model=modelo,
                                use_claude=use_claude,
                                output_dir=reports_dir
                            )
                            pdf_path = pdf_gen.generate_company_report(
                                compania=compania_seleccionada,
                                año=año,
                                benchmark_type=benchmark_type
                            )
                            files_generated.append(("PDF", pdf_path))

                        # Generar Excel
                        if formato in ["Excel", "Ambos"]:
                            st.info("📊 Generando Excel...")
                            excel_gen = BenchmarkingReportExcel(
                                llm_model=modelo,
                                use_claude=use_claude,
                                output_dir=reports_dir
                            )
                            excel_path = excel_gen.generate_company_report(
                                compania=compania_seleccionada,
                                año=año,
                                benchmark_type=benchmark_type
                            )
                            files_generated.append(("Excel", excel_path))

                        # Mostrar éxito
                        st.success(f"✅ Informe(s) generado(s) exitosamente!")

                        # Botones de descarga
                        st.subheader("📥 Descargar Archivos")

                        for file_type, file_path in files_generated:
                            with open(file_path, "rb") as file:
                                file_name = os.path.basename(file_path)
                                mime_type = "application/pdf" if file_type == "PDF" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                
                                st.download_button(
                                    label=f"⬇️ Descargar {file_type}",
                                    data=file,
                                    file_name=file_name,
                                    mime=mime_type,
                                    use_container_width=True
                                )

                        # Mostrar ubicación de archivos
                        st.info(f"📁 Los archivos también están disponibles en: `{os.path.abspath(reports_dir)}`")

                    except Exception as e:
                        st.error(f"❌ Error al generar informe: {e}")
                        st.exception(e)
        else:
            st.warning(f"⚠️ No se encontraron datos para {compania_seleccionada}")

    # Footer
    st.divider()
    provider_name = "Claude API" if use_claude else "Ollama"
    st.caption(f"📊 Generador de Informes - Piloto IA FICEM BD | Powered by {provider_name} ({modelo})")


if __name__ == "__main__":
    app()
