"""
Excel Tradicional - Cargar Excel Manual
"""
import streamlit as st

st.set_page_config(page_title="Cargar Excel", page_icon="📋", layout="wide")

st.title("📋 Cargar Excel Manual")
st.markdown("---")

st.header("Upload y validación de plantilla completada")

st.markdown("""
**Funcionalidad:** Carga de archivo Excel completado por empresa

**Proceso:**
1. Empresa completa template descargado
2. FICEM carga archivo en esta página
3. Sistema valida automáticamente:
   - Estructura (hojas y columnas requeridas)
   - Formato (tipos de datos correctos)
   - Coherencia (composiciones, balances, rangos)
4. Resultado: Datos válidos o lista de errores

**Validaciones automáticas:**
- Composiciones de cemento suman 100%
- Balance de masa clinker (producido + comprado = consumido + vendido)
- Densidades concreto vs volúmenes consistentes
- Valores en rangos técnicos razonables
- Campos requeridos completos

_Contenido en desarrollo_
""")

uploaded_file = st.file_uploader(
    "Seleccione archivo Excel completado",
    type=['xlsx'],
    help="Template Excel completado por la empresa"
)

if uploaded_file:
    st.success(f"Archivo cargado: {uploaded_file.name}")

    with st.expander("Información del archivo"):
        st.write(f"Tamaño: {uploaded_file.size} bytes")
        st.write(f"Tipo: {uploaded_file.type}")

    if st.button("Validar Archivo", type="primary"):
        st.info("Funcionalidad de validación en desarrollo")
