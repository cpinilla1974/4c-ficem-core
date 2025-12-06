"""
Dashboard: Nube de Puntos - Resistencia vs CO₂
Visualización masiva de relación entre resistencia y huella de carbono
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from database.connection import get_connection

st.set_page_config(page_title="Nube de Puntos", page_icon="🌌", layout="wide")

# ============================================================================
# CONSULTAS
# ============================================================================

def get_datos_nube_puntos(max_puntos=50000):
    """Obtiene datos para nube de puntos resistencia vs CO2"""
    engine = get_connection()
    query = """
    SELECT
        origen,
        empresa,
        planta,
        resistencia_mpa,
        co2_kg_m3,
        volumen
    FROM remitos
    WHERE resistencia_mpa IS NOT NULL
        AND resistencia_mpa > 0
        AND co2_kg_m3 IS NOT NULL
        AND co2_kg_m3 > 0
    ORDER BY RANDOM()
    LIMIT %s
    """ % max_puntos
    return pd.read_sql_query(query, engine)


# ============================================================================
# HEADER
# ============================================================================

st.title("🌌 Nube de Puntos: Resistencia vs Huella CO₂")
st.markdown("Visualización masiva de la relación entre resistencia del concreto y su huella de carbono")

# Controles
col1, col2 = st.columns([3, 1])
with col1:
    st.info("⚠️ Esta visualización puede tardar unos segundos en cargar debido al volumen de datos")
with col2:
    max_puntos = st.selectbox(
        "Puntos a visualizar",
        options=[10000, 25000, 50000, 100000],
        index=2
    )

st.divider()

# ============================================================================
# NUBE DE PUNTOS MASIVA
# ============================================================================

with st.spinner("Cargando datos..."):
    df_nube = get_datos_nube_puntos(max_puntos=max_puntos)

if not df_nube.empty:
    # Crear figura con nube de puntos
    fig = go.Figure()

    # Nube masiva por origen
    for origen in df_nube['origen'].unique():
        df_origen = df_nube[df_nube['origen'] == origen]

        fig.add_trace(
            go.Scatter(
                x=df_origen['resistencia_mpa'],
                y=df_origen['co2_kg_m3'],
                mode='markers',
                name=origen.upper(),
                marker=dict(
                    size=5,
                    opacity=0.6,
                    line=dict(width=0.5, color='white')
                ),
                text=[f"<b>{row['origen'].upper()}</b><br>" +
                      f"Resistencia: {row['resistencia_mpa']:.1f} MPa<br>" +
                      f"CO₂: {row['co2_kg_m3']:.1f} kg/m³<br>" +
                      f"Volumen: {row['volumen']:.1f} m³<br>" +
                      f"Planta: {row['planta']}"
                      for _, row in df_origen.iterrows()],
                hovertemplate='%{text}<extra></extra>'
            )
        )

    # Línea de tendencia general
    z = np.polyfit(df_nube['resistencia_mpa'], df_nube['co2_kg_m3'], 2)
    p = np.poly1d(z)
    x_trend = np.linspace(df_nube['resistencia_mpa'].min(), df_nube['resistencia_mpa'].max(), 200)
    y_trend = p(x_trend)

    fig.add_trace(
        go.Scatter(
            x=x_trend,
            y=y_trend,
            mode='lines',
            name='Tendencia',
            line=dict(color='red', width=3, dash='dash'),
            hovertemplate='Tendencia: %{y:.0f} kg CO₂/m³<extra></extra>'
        )
    )

    # Layout
    fig.update_layout(
        title=f'<b>Análisis Masivo: {len(df_nube):,} Remitos</b>',
        xaxis=dict(
            title='<b>Resistencia (MPa)</b>',
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        yaxis=dict(
            title='<b>Huella CO₂ (kg/m³)</b>',
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        hovermode='closest',
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='black',
            borderwidth=1
        ),
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)

    # Estadísticas de la muestra
    st.subheader("📊 Estadísticas de la Muestra")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Puntos Visualizados", f"{len(df_nube):,}")

    with col2:
        corr = df_nube['resistencia_mpa'].corr(df_nube['co2_kg_m3'])
        st.metric("Correlación", f"{corr:.3f}")

    with col3:
        st.metric(
            "Rango Resistencia",
            f"{df_nube['resistencia_mpa'].min():.0f} - {df_nube['resistencia_mpa'].max():.0f} MPa"
        )

    with col4:
        st.metric(
            "Rango CO₂",
            f"{df_nube['co2_kg_m3'].min():.0f} - {df_nube['co2_kg_m3'].max():.0f} kg/m³"
        )

    # Distribución por origen
    st.divider()
    st.subheader("📈 Distribución por Origen")

    col1, col2 = st.columns(2)

    with col1:
        df_stats = df_nube.groupby('origen').agg({
            'resistencia_mpa': ['mean', 'std'],
            'co2_kg_m3': ['mean', 'std'],
            'volumen': 'count'
        }).round(2)

        st.dataframe(
            df_stats,
            column_config={
                "origen": "Origen"
            },
            use_container_width=True
        )

    with col2:
        # Box plot por origen
        import plotly.express as px
        fig_box = px.box(
            df_nube,
            x='origen',
            y='co2_kg_m3',
            color='origen',
            title='Distribución de Huella CO₂ por Origen',
            labels={'co2_kg_m3': 'Huella CO₂ (kg/m³)', 'origen': 'Origen'}
        )
        st.plotly_chart(fig_box, use_container_width=True)

else:
    st.error("No hay datos disponibles para generar la nube de puntos")

# Footer
st.divider()
st.caption(f"📊 Visualización actualizada: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
