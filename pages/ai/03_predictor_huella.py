"""
Dashboard Predictor de Huella CO2
Piloto IA - FICEM BD
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go
import pandas as pd

# Agregar path para imports
sys.path.insert(0, str(Path.cwd()))

from ai_modules.ml.predictor import HuellaPredictor

def app():
    st.title("🎯 Predictor de Huella CO₂")
    st.markdown("### Prediccion basada en Machine Learning")

    # Cargar modelo
    @st.cache_resource
    def load_model():
        MODEL_PATH = "ai_modules/ml/saved_models/huella_predictor.pkl"
        return HuellaPredictor(MODEL_PATH)

    try:
        predictor = load_model()
        st.success(f"✅ Modelo cargado - R² = {predictor.stats.get('r2', 0):.3f}, RMSE = {predictor.stats.get('rmse', 0):.1f} kg CO₂/m³")
    except Exception as e:
        st.error(f"❌ Error cargando modelo: {e}")
        st.info("Asegurate de haber entrenado el modelo primero ejecutando: `python ai_modules/ml/predictor.py`")
        st.stop()

    # Expander explicativo
    with st.expander("ℹ️  ¿Cómo funciona este predictor?", expanded=False):
        st.markdown("""
        ### 🎯 Objetivo
        Este predictor utiliza **Machine Learning** para estimar la huella de carbono (kg CO₂/m³)
        de un concreto basándose en sus características técnicas y de producción.

        ### 🧠 Modelo de Predicción
        - **Algoritmo**: Gradient Boosting Regressor
        - **Datos de entrenamiento**: 255,328 remitos de concreto reales (2020-2024)
        - **Precisión**: R² = {:.4f} (excelente ajuste)
        - **Error promedio**: {:.2f} kg CO₂/m³

        ### 📊 Variables de Entrada
        El modelo considera las siguientes características:

        1. **Compañía y Año**: Patrón histórico de emisiones por productor
        2. **Resistencia (MPa)**: Resistencia a compresión del concreto
        3. **Contenido de Cemento (kg/m³)**: Principal contribuyente a la huella
        4. **Intensidades A1-A4**: Emisiones por etapa del ciclo de vida
           - **A1**: Extracción de materias primas (cemento, agregados)
           - **A2**: Transporte de materiales a planta
           - **A3**: Manufactura del concreto
           - **A4**: Transporte del concreto a obra

        ### 🔬 Proceso de Predicción

        1. **Feature Engineering**: El modelo crea variables derivadas automáticamente:
           - Intensidad total A1-A3
           - Ratios de cada etapa vs total
           - Cemento por unidad de resistencia
           - Codificación de compañía

        2. **Predicción**: El modelo entrenado estima la huella basándose en patrones
           aprendidos de miles de remitos reales

        3. **Intervalo de Confianza**: Calcula un rango de ±1.96 × MAE donde es altamente
           probable que caiga el valor real (95% de confianza)

        ### 📈 Comparación con Benchmarks
        La predicción se compara automáticamente con las **Bandas GCCA**:
        - **Banda A**: 0-150 kg CO₂/m³ (Excelente)
        - **Banda B**: 150-250 kg CO₂/m³ (Muy bueno)
        - **Banda C**: 250-350 kg CO₂/m³ (Promedio)
        - **Banda D**: 350-500 kg CO₂/m³ (Mejorable)
        - **Banda E**: >500 kg CO₂/m³ (Requiere optimización)

        ### 💡 Casos de Uso
        - **Diseño de mezclas**: Estimar huella antes de producir
        - **Optimización**: Evaluar impacto de cambios en formulación
        - **Benchmarking**: Comparar productos vs estándares internacionales
        - **Reportes**: Generar estimaciones para EPDs o reportes de sostenibilidad

        ### ⚠️ Limitaciones
        - El modelo se entrenó con datos de 2 compañías (MZMA, CEMEX)
        - Las predicciones son más precisas dentro del rango de datos históricos
        - Mezclas muy atípicas pueden tener mayor incertidumbre
        """.format(predictor.stats.get('r2', 0), predictor.stats.get('rmse', 0)))

    st.divider()

    # Sidebar con configuracion
    with st.sidebar:
        st.header("⚙️ Parametros de Prediccion")

        compania = st.selectbox(
            "Compania",
            options=["MZMA", "CEMEX"],
            help="Selecciona la compania"
        )

        año = st.number_input(
            "Año",
            min_value=2020,
            max_value=2030,
            value=2024,
            help="Año de produccion"
        )

        resistencia = st.slider(
            "Resistencia (MPa)",
            min_value=10.0,
            max_value=50.0,
            value=25.0,
            step=1.0,
            help="Resistencia a compresion del concreto"
        )

        contenido_cemento = st.slider(
            "Contenido de Cemento (kg/m³)",
            min_value=200.0,
            max_value=500.0,
            value=350.0,
            step=10.0,
            help="Cantidad de cemento en la mezcla"
        )

        st.divider()
        st.subheader("Intensidades A1-A4 (kg CO₂/m³)")

        a1_intensidad = st.number_input(
            "A1 - Extraccion de materias primas",
            min_value=0.0,
            max_value=500.0,
            value=250.0,
            step=1.0,
            help="Emisiones por extracción de cemento, agregados, etc. Rango típico: 180-300 kg CO₂/m³"
        )

        a2_intensidad = st.number_input(
            "A2 - Transporte a planta",
            min_value=0.0,
            max_value=50.0,
            value=5.0,
            step=0.5,
            help="Emisiones por transporte de materias primas a planta. Rango típico: 2-30 kg CO₂/m³"
        )

        a3_intensidad = st.number_input(
            "A3 - Manufactura del concreto",
            min_value=0.0,
            max_value=10.0,
            value=1.0,
            step=0.1,
            help="Emisiones por proceso de producción del concreto. Rango típico: 0.4-2.0 kg CO₂/m³"
        )

        a4_intensidad = st.number_input(
            "A4 - Transporte a obra",
            min_value=0.0,
            max_value=50.0,
            value=10.0,
            step=0.5,
            help="Emisiones por transporte del concreto a la obra. Rango típico: 5-25 kg CO₂/m³"
        )

    # Boton de prediccion
    if st.button("🚀 Predecir Huella CO₂", type="primary", use_container_width=True):
        features = {
            'compania': compania,
            'año': año,
            'resistencia': resistencia,
            'contenido_cemento': contenido_cemento,
            'a1_intensidad': a1_intensidad,
            'a2_intensidad': a2_intensidad,
            'a3_intensidad': a3_intensidad,
            'a4_intensidad': a4_intensidad
        }

        with st.spinner("Calculando prediccion..."):
            resultado = predictor.predict(features)

        # Mostrar resultado
        st.success("✅ Prediccion completada")

        # Metricas principales
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Huella Predicha",
                f"{resultado['prediccion']:.1f} kg CO₂/m³",
                delta=None
            )

        with col2:
            st.metric(
                "Intervalo Inferior",
                f"{resultado['ci_lower']:.1f} kg CO₂/m³",
                delta=None
            )

        with col3:
            st.metric(
                "Intervalo Superior",
                f"{resultado['ci_upper']:.1f} kg CO₂/m³",
                delta=None
            )

        st.divider()

        # Grafico de intervalos
        fig = go.Figure()

        # Barra de prediccion
        fig.add_trace(go.Bar(
            x=[resultado['prediccion']],
            y=['Prediccion'],
            orientation='h',
            name='Prediccion',
            marker=dict(color='#1f77b4'),
            text=[f"{resultado['prediccion']:.1f} kg CO₂/m³"],
            textposition='auto'
        ))

        # Intervalo de confianza
        fig.add_trace(go.Scatter(
            x=[resultado['ci_lower'], resultado['ci_upper']],
            y=['Prediccion', 'Prediccion'],
            mode='markers',
            name='IC 95%',
            marker=dict(size=12, color='red', symbol='diamond'),
            showlegend=True
        ))

        fig.update_layout(
            title="Prediccion con Intervalo de Confianza 95%",
            xaxis_title="Huella CO₂ (kg/m³)",
            yaxis_title="",
            height=250,
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # Benchmarks GCCA
        st.divider()
        st.subheader("📊 Comparacion con Benchmarks GCCA")

        # Bandas GCCA (ejemplo simplificado)
        bandas_gcca = {
            'A': (0, 150),
            'B': (150, 250),
            'C': (250, 350),
            'D': (350, 500),
            'E': (500, 1000)
        }

        # Determinar banda
        pred = resultado['prediccion']
        banda = 'E'
        for b, (min_val, max_val) in bandas_gcca.items():
            if min_val <= pred < max_val:
                banda = b
                break

        col1, col2 = st.columns([1, 2])

        with col1:
            st.metric(
                "Banda GCCA",
                banda,
                delta=None
            )

            if banda in ['A', 'B']:
                st.success("Excelente desempeño")
            elif banda == 'C':
                st.info("Desempeño promedio")
            else:
                st.warning("Oportunidad de mejora")

        with col2:
            # Grafico de bandas
            fig_bandas = go.Figure()

            colores = {'A': '#2ca02c', 'B': '#8fce00', 'C': '#ffd700', 'D': '#ff8c00', 'E': '#d62728'}

            for b, (min_val, max_val) in bandas_gcca.items():
                fig_bandas.add_trace(go.Bar(
                    x=[(min_val + max_val) / 2],
                    y=[b],
                    orientation='h',
                    name=f'Banda {b}',
                    marker=dict(color=colores[b]),
                    width=0.5,
                    showlegend=False
                ))

            # Marcar prediccion
            fig_bandas.add_trace(go.Scatter(
                x=[pred],
                y=[banda],
                mode='markers',
                name='Tu Prediccion',
                marker=dict(size=15, color='blue', symbol='star'),
                showlegend=True
            ))

            fig_bandas.update_layout(
                title="Bandas GCCA para Concreto",
                xaxis_title="Huella CO₂ (kg/m³)",
                yaxis_title="Banda",
                height=300
            )

            st.plotly_chart(fig_bandas, use_container_width=True)

        # Informacion del modelo
        st.divider()
        with st.expander("ℹ️  Informacion del Modelo"):
            st.markdown(f"""
            **Metricas del Modelo:**
            - R² Score: {resultado['r2']:.4f}
            - RMSE: {resultado['rmse']:.2f} kg CO₂/m³

            **Caracteristicas Incluidas:**
            - Resistencia a compresion
            - Contenido de cemento
            - Intensidades A1-A4
            - Compania
            - Año

            **Datos de Entrenamiento:**
            - {predictor.stats.get('n_train', 0):,} remitos de entrenamiento
            - {predictor.stats.get('n_test', 0):,} remitos de prueba
            """)

    # Footer
    st.divider()
    st.caption("🎯 Predictor de Huella - Piloto IA FICEM BD | Powered by Gradient Boosting")

if __name__ == "__main__":
    app()
