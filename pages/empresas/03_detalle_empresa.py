"""
Empresas - Detalle Empresa
"""
import streamlit as st

st.set_page_config(page_title="Detalle Empresa", page_icon="🏭", layout="wide")

st.title("🏭 Detalle de Empresa")
st.markdown("---")

st.header("Información detallada y historial")

st.markdown("""
**Funcionalidad:** Vista detallada de una empresa específica

Esta página mostrará:
- Información general de la empresa
- Perfil de planta(s)
- Historial de submissions
- Resultados históricos de cálculos
- Gráficos de evolución
- Acciones (editar, descargar reportes)

_Contenido en desarrollo_
""")

st.info("Seleccione una empresa desde el listado para ver su detalle")
