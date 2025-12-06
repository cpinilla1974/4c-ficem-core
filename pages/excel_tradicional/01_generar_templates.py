"""
Excel Tradicional - Generar Templates
"""
import streamlit as st

st.set_page_config(page_title="Generar Templates", page_icon="📋", layout="wide")

st.title("📋 Generar Templates Excel")
st.markdown("---")

st.header("Generación de plantillas personalizadas")

st.markdown("""
**Funcionalidad:** Crear Excel personalizado según perfil de planta

**Características del template:**
- Hojas específicas según perfil (integrada/molienda/concreto)
- Validaciones Excel integradas (rangos, listas desplegables)
- Instrucciones contextuales en cada hoja
- Formato consistente para procesamiento automático
- Ejemplos y valores por defecto

**Perfiles de planta:**
1. **Integrada**: Clinker + Cemento (incluye horno)
2. **Molienda**: Solo Cemento (compra clinker)
3. **Concreto**: Solo productos de concreto

_Contenido en desarrollo_
""")

col1, col2 = st.columns(2)

with col1:
    perfil = st.selectbox(
        "Perfil de Planta",
        ["Integrada", "Molienda", "Concreto"],
        help="Seleccione el tipo de planta para generar template apropiado"
    )

with col2:
    pais = st.selectbox(
        "País",
        ["Colombia", "Perú", "Chile", "México", "Argentina", "Brasil"],
        help="Factores de emisión específicos del país"
    )

if st.button("Generar Template Excel", type="primary"):
    st.info("Funcionalidad en desarrollo - Se generará archivo Excel personalizado")
