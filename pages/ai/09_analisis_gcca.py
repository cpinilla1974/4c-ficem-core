"""
Análisis GCCA - Comparación de Datos con Benchmarks
Piloto IA - FICEM BD
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# Agregar path para imports
sys.path.insert(0, str(Path.cwd()))

from ai_modules.rag.rag_chain import RAGChain
from ai_modules.rag.sql_tool import SQLTool

def app():
    st.title("📊 Análisis GCCA - Benchmarking de Concreto")
    st.markdown("### Comparación de Datos Reales con Métricas GCCA GNR Concrete Pilot Project")

    st.divider()

    # Selector de modelo en sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")

        modelo_tipo = st.radio(
            "Proveedor LLM",
            options=["Ollama (Local)", "Claude (API)"],
            index=0,
            help="Selecciona el proveedor del modelo de lenguaje"
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
                index=0,
                help="Modelo de Claude a usar"
            )
        else:
            modelo = st.selectbox(
                "Modelo Ollama",
                options=["qwen2.5:3b", "qwen2.5:7b", "qwen2.5:1.5b"],
                index=0,
                help="Modelo local de Ollama"
            )

        st.divider()

    # Inicializar herramientas
    @st.cache_resource
    def get_tools(_modelo, _use_claude):
        rag = RAGChain(llm_model=_modelo, temperature=0.1, top_k=5, use_claude=_use_claude)
        sql_tool = SQLTool()
        return rag, sql_tool

    try:
        rag, sql_tool = get_tools(modelo, use_claude)
        provider_name = "Claude API" if use_claude else "Ollama Local"
        st.success(f"✅ Sistema listo ({provider_name}: {modelo})")
    except Exception as e:
        st.error(f"❌ Error inicializando sistema: {e}")
        if use_claude:
            st.info("Verifica que tengas ANTHROPIC_API_KEY en tu archivo .env")
        else:
            st.info("Verifica que Ollama esté corriendo: `ollama list`")
        st.stop()

    # Sección principal
    st.subheader("🎯 Datos de la Base de Datos")

    # Obtener datos agregados de huella_concretos
    col1, col2 = st.columns(2)

    with col1:
        # Selector de compañía
        query_companias = """
        SELECT DISTINCT origen as compania
        FROM huella_concretos
        WHERE origen IS NOT NULL
        ORDER BY origen
        """
        result = sql_tool.execute_query(query_companias)

        if result["success"] and result["rows"]:
            companias = [row["compania"] for row in result["rows"]]
            compania_seleccionada = st.selectbox("Seleccionar Compañía", companias)
        else:
            st.warning("No se encontraron compañías")
            compania_seleccionada = None

    with col2:
        # Selector de año
        query_años = """
        SELECT DISTINCT año
        FROM huella_concretos
        WHERE año IS NOT NULL
        ORDER BY año DESC
        """
        result = sql_tool.execute_query(query_años)

        if result["success"] and result["rows"]:
            años = [row["año"] for row in result["rows"]]
            año_seleccionado = st.selectbox("Seleccionar Año", años)
        else:
            st.warning("No se encontraron años")
            año_seleccionado = None

    st.divider()

    # Botón para analizar
    if st.button("🔍 Analizar con Métricas GCCA", type="primary", use_container_width=True):
        if not compania_seleccionada or not año_seleccionado:
            st.warning("⚠️ Selecciona una compañía y un año")
            st.stop()

        with st.spinner("Obteniendo datos de la base de datos..."):
            # Obtener datos de la compañía
            result = sql_tool.get_huella_promedio_compania(compania_seleccionada, año_seleccionado)

            if not result["success"] or not result["rows"]:
                st.error("❌ No se encontraron datos para la compañía y año seleccionados")
                st.stop()

            # Extraer datos
            data = result["rows"][0]
            num_remitos = data.get('num_remitos', 0) or 0
            huella_promedio = data.get('huella_promedio') or 0
            resistencia_promedio = data.get('resistencia_promedio') or 0
            cemento_promedio = data.get('cemento_promedio') or 0
            volumen_total = data.get('volumen_total') or 0

            # Mostrar datos básicos
            st.subheader(f"📋 Datos de {compania_seleccionada} ({año_seleccionado})")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Remitos", f"{num_remitos:,}")
            with col2:
                st.metric("Huella Promedio", f"{huella_promedio:.2f} kg CO₂/m³")
            with col3:
                st.metric("Resistencia", f"{resistencia_promedio:.1f} MPa")
            with col4:
                st.metric("Volumen Total", f"{volumen_total:,.0f} m³")

            st.divider()

        with st.spinner("Consultando documento GCCA GNR y analizando..."):
            # Construir contexto de datos
            contexto_datos = f"""
Datos reales de {compania_seleccionada} en {año_seleccionado}:
- Número de entregas/remitos: {num_remitos:,}
- Huella de carbono promedio: {huella_promedio:.2f} kg CO₂/m³
- Resistencia a la compresión promedio: {resistencia_promedio:.1f} MPa
- Volumen anual total: {volumen_total:,.0f} m³

IMPORTANTE: Busca información específica del documento '20200702 GCCA GNR Concrete Pilot Project' sobre:
1. Rangos de huella de carbono típicos o benchmarks para concreto
2. Metodología de medición y reporte
3. Bandas de clasificación por niveles de huella
4. Métricas clave del proyecto piloto
5. Comparación con estándares internacionales
"""

            # Consulta dirigida al RAG
            pregunta = f"""
Basándote EXCLUSIVAMENTE en el documento '20200702 GCCA GNR Concrete Pilot Project', analiza los siguientes datos reales de {compania_seleccionada}:

- Huella de carbono promedio: {huella_promedio:.2f} kg CO₂/m³
- Resistencia promedio: {resistencia_promedio:.1f} MPa
- Volumen anual: {volumen_total:,.0f} m³

Por favor proporciona:

1. **Clasificación según GCCA**: ¿En qué banda o nivel se ubicaría esta huella?
2. **Comparación con benchmarks**: ¿Cómo se compara con los valores típicos mencionados en el documento?
3. **Contexto metodológico**: ¿Qué aspectos de la metodología GCCA GNR son relevantes para esta medición?
4. **Oportunidades identificadas**: Según las mejores prácticas del documento, ¿qué oportunidades de mejora existen?
5. **Métricas clave**: ¿Cuáles son los números o rangos específicos mencionados en el documento GCCA GNR que sirven de referencia?

FUNDAMENTAL: Cita SOLO información del documento GCCA GNR Concrete Pilot Project. Si algo no está en ese documento específico, indícalo claramente.
"""

            # Ejecutar consulta RAG
            try:
                result_rag = rag.query(pregunta)

                st.subheader("🎯 Análisis con Métricas GCCA GNR")

                # Mostrar respuesta
                st.markdown(result_rag["answer"])

                # Mostrar fuentes consultadas
                if result_rag.get("sources"):
                    with st.expander(f"📚 Fuentes consultadas ({len(result_rag['sources'])})"):
                        for i, source in enumerate(result_rag["sources"], 1):
                            st.markdown(f"""
                            **{i}. {source['source']}**
                            - Tipo: {source['document_type']}
                            - Chunk: {source['chunk_id']}
                            - Preview: {source['text_preview'][:200]}...
                            """)

            except Exception as e:
                st.error(f"❌ Error durante el análisis: {e}")
                st.info("Verifica que el sistema RAG esté funcionando correctamente")

    # Información adicional en sidebar
    with st.sidebar:
        st.header("📚 Información")
        st.markdown("""
        **Documento Base:**
        - GCCA GNR Concrete Pilot Project (2020)

        **Análisis:**
        - Compara datos reales de base de datos
        - Consulta documento tokenizado en vector store
        - Usa RAG para extraer métricas relevantes
        - Proporciona contexto y recomendaciones
        """)

        st.divider()

        st.markdown("""
        **Métricas Típicas:**
        - Huella de carbono (kg CO₂/m³)
        - Resistencia a compresión (MPa)
        - Volumen producido (m³)
        """)

    # Footer
    st.divider()
    provider_name = "Claude API" if use_claude else "Ollama"
    st.caption(f"📊 Análisis GCCA - Piloto IA FICEM BD | Powered by {provider_name} ({modelo})")


# Run the app
app()
