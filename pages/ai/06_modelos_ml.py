"""
Modelos de Machine Learning
Piloto IA - FICEM BD
"""

import streamlit as st
from PIL import Image
from pathlib import Path
import pandas as pd

def app():
    st.title("🤖 Modelos de Machine Learning")
    st.markdown("### Predictor de Huella de Carbono")

    st.divider()

    # COMPARACIÓN DE MODELOS
    st.header("📊 Comparación de Modelos")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🏆 Random Forest", "R² = 0.9999", delta="Mejor modelo")

    with col2:
        st.metric("XGBoost", "R² = 0.9999", delta="Segundo mejor")

    with col3:
        st.metric("Linear Regression", "R² = 0.9978", delta="Baseline")

    # Tabla comparativa
    modelos_data = {
        "Modelo": ["Random Forest 🏆", "XGBoost", "Linear Regression"],
        "RMSE (kg CO₂/m³)": [0.43, 0.61, 3.80],
        "MAE (kg CO₂/m³)": [0.07, 0.33, 2.65],
        "R² Score": [0.9999, 0.9999, 0.9978]
    }

    df_modelos = pd.DataFrame(modelos_data)
    st.dataframe(df_modelos, use_container_width=True, hide_index=True)

    st.success("🏆 **Random Forest** - Precisión casi perfecta (RMSE = 0.43 kg CO₂/m³)")

    st.divider()

    # GRÁFICOS
    graficos = [
        ("resultados_comparacion_modelos.png", "Comparación de Modelos"),
        ("resultados_mejor_modelo_analisis.png", "Análisis Random Forest"),
        ("resultados_feature_importance.png", "Importancia de Features")
    ]

    for img_file, titulo in graficos:
        st.subheader(titulo)
        img_path = Path(img_file)
        if img_path.exists():
            img = Image.open(img_path)
            st.image(img, use_container_width=True)
        else:
            st.warning(f"⚠️ Gráfico no encontrado: {img_file}")
        st.divider()

    # FEATURE IMPORTANCE
    st.header("🔍 Feature Importance")
    st.markdown("""
    **Hallazgo principal:** La intensidad total (A1+A2+A3) explica **99.66%** de la variabilidad.

    | Ranking | Feature | Importancia |
    |---------|---------|-------------|
    | 1 🥇 | intensidad_total_a1_a3 | **99.66%** |
    | 2 🥈 | año | 0.22% |
    | 3 🥉 | a3_intensidad | 0.04% |
    """)

    st.markdown("---")
    st.caption("🤖 Modelos ML - Piloto IA FICEM BD | Random Forest R² = 0.9999")


# Run the app
app()
