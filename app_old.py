"""
Calculadora País 4C - Sistema de Huella de Carbono
Etapa 1: Operador Centralizado FICEM
"""
import streamlit as st
from database import init_db

# Configuración de página
st.set_page_config(
    page_title="Calculadora 4C País Perú",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar base de datos en session_state
if 'db_engine' not in st.session_state:
    st.session_state.db_engine = init_db()

# Para compatibilidad con código migrado de ficem_bd
if 'ruta_db' not in st.session_state:
    st.session_state.ruta_db = 'data/latam4c.db'  # Path simbólico para SQLite nativo

# Definir páginas con navegación colapsable
pages = {
    "📊 Dashboard": [
        st.Page("pages/dashboard/01_resumen_consolidado.py", title="Resumen Consolidado", icon="📊"),
        st.Page("pages/dashboard/02_distribucion_bandas_gcca.py", title="Distribución Bandas GCCA", icon="📊"),
        st.Page("pages/dashboard/03_historico_timeline.py", title="Histórico Timeline", icon="📊"),
    ],
    "🏭 Empresas": [
        st.Page("pages/empresas/01_listado_empresas.py", title="Listado Empresas", icon="🏭"),
        st.Page("pages/empresas/02_registro_empresa.py", title="Registro Nueva Empresa", icon="🏭"),
        st.Page("pages/empresas/03_detalle_empresa.py", title="Detalle Empresa", icon="🏭"),
    ],
    "🔧 Calculadoras 3C": [
        st.Page("pages/calculadoras_3c/01_importar_3c.py", title="Importar desde 3C", icon="🔧"),
        st.Page("pages/calculadoras_3c/02_validar_importacion.py", title="Validar Importación", icon="🔧"),
        st.Page("pages/calculadoras_3c/03_calcular.py", title="Calcular", icon="🔧"),
        st.Page("pages/calculadoras_3c/04_resultados_3c.py", title="Resultados 3C", icon="🔧"),
    ],
    "📋 Excel Tradicional": [
        st.Page("pages/excel_tradicional/01_generar_templates.py", title="Generar Templates", icon="📋"),
        st.Page("pages/excel_tradicional/02_cargar_excel.py", title="Cargar Excel Manual", icon="📋"),
        st.Page("pages/excel_tradicional/03_corregir_errores.py", title="Corregir Errores", icon="📋"),
        st.Page("pages/excel_tradicional/04_procesar.py", title="Procesar", icon="📋"),
    ],
    "📈 Análisis": [
        st.Page("pages/analisis/01_curvas_co2_resistencia.py", title="Curvas CO₂ vs Resistencia", icon="📈"),
        st.Page("pages/analisis/02_comparativa_pais.py", title="Comparativa por País", icon="📈"),
        st.Page("pages/analisis/03_analisis_bandas.py", title="Análisis por Bandas", icon="📈"),
        st.Page("pages/analisis/04_tendencias_temporales.py", title="Tendencias Temporales", icon="📈"),
        st.Page("pages/analisis/05_explorar_data.py", title="Explorar Data", icon="🔍"),
        st.Page("pages/analisis/06_bandas_cemento.py", title="Bandas GCCA Cementos", icon="📊"),
        st.Page("pages/analisis/07_bandas_concreto.py", title="Bandas GCCA Concretos", icon="📊"),
    ],
    "📄 Reportes": [
        st.Page("pages/reportes/01_reporte_individual.py", title="Reporte Individual", icon="📄"),
        st.Page("pages/reportes/02_reporte_consolidado.py", title="Reporte Consolidado País", icon="📄"),
        st.Page("pages/reportes/03_exportar_datos.py", title="Exportar Datos", icon="📄"),
    ],
    "🛣️ Hoja de Ruta": [
        st.Page("pages/hoja_ruta/01_estado_implementacion.py", title="Estado Implementación", icon="🛣️"),
        st.Page("pages/hoja_ruta/02_checklist_entregables.py", title="Checklist Entregables", icon="🛣️"),
        st.Page("pages/hoja_ruta/03_empresas_piloto.py", title="Empresas Piloto", icon="🛣️"),
    ],
}

# Crear navegación con secciones colapsables
pg = st.navigation(pages, position="sidebar", expanded=True)

# Información de versión en sidebar
with st.sidebar:
    st.markdown("---")
    st.caption("**Calculadora 4C País Perú**")
    st.caption("Versión 1.0 - Etapa 1")
    st.caption("© 2025 FICEM")

# Ejecutar página seleccionada
pg.run()
