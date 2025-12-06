"""
Reportes - Reporte Individual
"""
import streamlit as st

st.set_page_config(page_title="Reporte Individual", page_icon="📄", layout="wide")

st.title("📄 Reporte Individual")
st.markdown("---")

st.header("Generación de reporte por empresa")

st.markdown("""
**Funcionalidad:** PDF personalizado para cada empresa con resultados y benchmarking

**Contenido del reporte:**

### 1. Información General
- Nombre de la empresa
- País y perfil de planta
- Período de reporte
- Fecha de generación

### 2. Resultados por Producto

**Clinker:**
- Emisiones totales A1-A3 (kg CO₂e/ton)
- Desglose por alcance

**Cemento(s):**
- Por cada tipo de cemento producido
- Emisiones A1-A3 (kg CO₂e/ton)
- Banda GCCA (A-G)
- Posición vs percentiles país

**Concreto(s):**
- Por cada diseño de mezcla
- Emisiones A1-A3 (kg CO₂e/m³)
- Banda GCCA (AA-F) según resistencia
- Posición en curva CO₂ vs resistencia

### 3. Benchmarking Anónimo
- Comparativa con promedio país
- Posición en distribución regional
- Ranking anónimo

### 4. Recomendaciones
- Oportunidades de mejora identificadas
- Mejores prácticas aplicables

_Contenido en desarrollo_
""")

empresa_id = st.selectbox("Seleccione Empresa", ["Empresa 1", "Empresa 2", "Empresa 3"])
periodo = st.selectbox("Período", ["2024", "2023", "2022"])

if st.button("Generar Reporte PDF", type="primary"):
    st.info("Funcionalidad en desarrollo")
