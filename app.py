"""
Calculadora País 4C - Sistema de Huella de Carbono
Etapa 1: Operador Centralizado FICEM
"""
import streamlit as st
from database import init_db

# Configuración de página
st.set_page_config(
    page_title="4C Perú",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Agregar título en sidebar al inicio (antes que todo lo demás)
with st.sidebar:
    st.title("4C Perú")
    st.divider()

# Inicializar base de datos en session_state
if 'db_engine' not in st.session_state:
    st.session_state.db_engine = init_db()

# Para compatibilidad con código migrado de ficem_bd
if 'ruta_db' not in st.session_state:
    st.session_state.ruta_db = 'data/latam4c.db'  # Path simbólico para SQLite nativo

# Definir páginas con navegación colapsable
pages = {
    "📊 Dashboard": [
        st.Page("pages/dashboard/01_remitos_latam.py", title="Remitos LATAM", icon="📊"),
        st.Page("pages/dashboard/02_nube_puntos.py", title="Nube de Puntos", icon="🌌"),
    ],
    "🏭 Empresas": [
        st.Page("pages/empresas/01_listado_empresas.py", title="Listado Empresas", icon="🏭"),
        st.Page("pages/empresas/02_registro_empresa.py", title="Registro Nueva Empresa", icon="🏭"),
        st.Page("pages/empresas/03_detalle_empresa.py", title="Detalle Empresa", icon="🏭"),
    ],
    "📋 Excel Tradicional": [
        st.Page("pages/excel_tradicional/01_generar_templates.py", title="Generar Templates", icon="📋"),
        st.Page("pages/excel_tradicional/02_cargar_excel.py", title="Cargar Excel Manual", icon="📋"),
        st.Page("pages/excel_tradicional/03_corregir_errores.py", title="Corregir Errores", icon="📋"),
        st.Page("pages/excel_tradicional/04_procesar.py", title="Procesar", icon="📋"),
    ],
    "🔍 Explora Data": [
        st.Page("pages/explora_data/01_plantas_cemento.py", title="Plantas de Cemento", icon="🏭"),
        st.Page("pages/explora_data/02_explorador_datos.py", title="Explorador de Datos", icon="🔍"),
        st.Page("pages/explora_data/03_cubo_completo.py", title="Cubo Completo", icon="📊"),
    ],
    "📊 Bandas GCCA": [
        st.Page("pages/bandas/01_estadisticas_concretos.py", title="Estadísticas Concretos", icon="📈"),
        st.Page("pages/bandas/02_estadisticas_remitos.py", title="Estadísticas Remitos", icon="📋"),
        st.Page("pages/bandas/03_bandas_concretos.py", title="Bandas GCCA Concretos", icon="📊"),
        st.Page("pages/bandas/04_bandas_cemento.py", title="Bandas GCCA Cementos", icon="📊"),
    ],
    "🤖 Piloto IA": [
        st.Page("pages/ai/02_chat_benchmarking.py", title="Chat Benchmarking", icon="💬"),
        st.Page("pages/ai/03_predictor_huella.py", title="Predictor Huella CO₂", icon="🔮"),
        st.Page("pages/ai/04_generador_informes.py", title="Generador Informes", icon="📝"),
        st.Page("pages/ai/06_modelos_ml.py", title="Modelos ML", icon="🧠"),
        st.Page("pages/ai/09_analisis_gcca.py", title="Análisis GCCA", icon="📊"),
        st.Page("pages/ai/10_generador_analisis.py", title="Generador de Análisis", icon="🤖"),
    ],
    "📈 Análisis": [
        st.Page("pages/analisis/05_explorar_data.py", title="Explorador de Datos", icon="📈"),
    ],
    "📄 Reportes": [
        st.Page("pages/reportes/01_reporte_individual.py", title="Reporte Individual", icon="📄"),
        st.Page("pages/reportes/02_reporte_consolidado.py", title="Reporte Consolidado País", icon="📄"),
        st.Page("pages/reportes/03_exportar_datos.py", title="Exportar Datos", icon="📄"),
    ],
}

# Crear navegación con secciones colapsables
pg = st.navigation(pages, position="sidebar", expanded=False)

# Información de versión en sidebar
with st.sidebar:
    st.markdown("---")
    st.caption("**4C Perú**")
    st.caption("Versión 1.0 - Etapa 1")
    st.caption("© 2025 FICEM")

# Ejecutar página seleccionada
pg.run()
