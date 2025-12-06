"""
Dashboard: Remitos LATAM Consolidados
Visualización de remitos migrados de todas las empresas
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from database.connection import get_connection

st.set_page_config(page_title="Remitos LATAM", page_icon="📊", layout="wide")

# ============================================================================
# CONSULTAS - Sin cache, usando vistas materializadas
# ============================================================================

def get_resumen_general():
    """Obtiene resumen general desde vista materializada"""
    engine = get_connection()
    query = "SELECT * FROM mv_resumen_por_origen"
    return pd.read_sql_query(query, engine)


def get_evolucion_temporal():
    """Obtiene evolución temporal desde vista materializada"""
    engine = get_connection()
    query = "SELECT * FROM mv_evolucion_temporal"
    return pd.read_sql_query(query, engine)


def get_distribucion_resistencia():
    """Obtiene distribución de resistencias desde vista materializada"""
    engine = get_connection()
    query = "SELECT * FROM mv_distribucion_resistencia"
    return pd.read_sql_query(query, engine)


def get_top_plantas():
    """Obtiene top plantas desde vista materializada"""
    engine = get_connection()
    query = "SELECT * FROM mv_top_plantas"
    return pd.read_sql_query(query, engine)


def get_datos_nube_puntos(max_puntos=50000):
    """Obtiene datos para nube de puntos resistencia vs CO2 (query directa, datos aleatorios)"""
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

st.title("📊 Dashboard: Remitos LATAM Consolidados")
st.markdown("Vista consolidada de remitos de concreto de toda LATAM")

# ============================================================================
# MÉTRICAS GENERALES
# ============================================================================

df_resumen = get_resumen_general()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Remitos",
        f"{df_resumen['total_remitos'].sum():,.0f}",
        help="Total de remitos en la base de datos"
    )

with col2:
    st.metric(
        "Volumen Total",
        f"{df_resumen['volumen_total'].sum():,.0f} m³",
        help="Volumen total de concreto"
    )

with col3:
    co2_prom = df_resumen['co2_promedio'].mean()
    st.metric(
        "CO₂ Promedio",
        f"{co2_prom:.1f} kg/m³" if pd.notna(co2_prom) else "N/A",
        help="Promedio de emisiones CO₂"
    )

with col4:
    st.metric(
        "Empresas",
        len(df_resumen),
        help="Número de empresas/orígenes"
    )

st.divider()

# ============================================================================
# RESUMEN POR ORIGEN
# ============================================================================

st.subheader("📈 Resumen por Origen")

# Tabla resumen
df_display = df_resumen.copy()
df_display['volumen_total'] = df_display['volumen_total'].apply(lambda x: f"{x:,.0f}")
df_display['total_remitos'] = df_display['total_remitos'].apply(lambda x: f"{x:,.0f}")
df_display['resistencia_promedio'] = df_display['resistencia_promedio'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
df_display['co2_promedio'] = df_display['co2_promedio'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
df_display['fecha_inicio'] = pd.to_datetime(df_display['fecha_inicio']).dt.strftime('%Y-%m-%d')
df_display['fecha_fin'] = pd.to_datetime(df_display['fecha_fin']).dt.strftime('%Y-%m-%d')

st.dataframe(
    df_display,
    column_config={
        "origen": "Origen",
        "empresa": "Empresa",
        "pais": "País",
        "total_remitos": "Remitos",
        "volumen_total": "Volumen (m³)",
        "resistencia_promedio": st.column_config.NumberColumn("REST Prom (MPa)", format="%.1f"),
        "co2_promedio": st.column_config.NumberColumn("CO₂ Prom (kg/m³)", format="%.1f"),
        "fecha_inicio": "Desde",
        "fecha_fin": "Hasta"
    },
    hide_index=True,
    use_container_width=True
)

# Gráficos de distribución
col1, col2 = st.columns(2)

with col1:
    fig = px.pie(
        df_resumen,
        values='total_remitos',
        names='origen',
        title='Distribución de Remitos por Origen',
        hole=0.4
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(
        df_resumen,
        x='origen',
        y='volumen_total',
        title='Volumen Total por Origen',
        labels={'volumen_total': 'Volumen (m³)', 'origen': 'Origen'},
        color='origen'
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================================
# EVOLUCIÓN TEMPORAL
# ============================================================================

st.subheader("📅 Evolución Temporal")

df_temporal = get_evolucion_temporal()

if not df_temporal.empty:
    tab1, tab2 = st.tabs(["Número de Remitos", "Volumen"])

    with tab1:
        fig = px.line(
            df_temporal,
            x='mes',
            y='num_remitos',
            color='origen',
            title='Evolución Mensual de Remitos',
            labels={'mes': 'Mes', 'num_remitos': 'Número de Remitos', 'origen': 'Origen'}
        )
        fig.update_xaxes(dtick="M3", tickformat="%b\n%Y")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = px.area(
            df_temporal,
            x='mes',
            y='volumen_m3',
            color='origen',
            title='Evolución Mensual de Volumen',
            labels={'mes': 'Mes', 'volumen_m3': 'Volumen (m³)', 'origen': 'Origen'}
        )
        fig.update_xaxes(dtick="M3", tickformat="%b\n%Y")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay datos temporales disponibles")

st.divider()

# ============================================================================
# DISTRIBUCIÓN DE RESISTENCIAS
# ============================================================================

st.subheader("💪 Distribución de Resistencias")

df_resistencia = get_distribucion_resistencia()

if not df_resistencia.empty:
    fig = px.box(
        df_resistencia,
        x='origen',
        y='resistencia_mpa',
        title='Distribución de Resistencias por Origen',
        labels={'resistencia_mpa': 'Resistencia (MPa)', 'origen': 'Origen'},
        color='origen'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Histograma
    fig = px.histogram(
        df_resistencia,
        x='resistencia_mpa',
        color='origen',
        title='Histograma de Resistencias',
        labels={'resistencia_mpa': 'Resistencia (MPa)'},
        nbins=50,
        barmode='overlay',
        opacity=0.7
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay datos de resistencia disponibles")

st.divider()

# ============================================================================
# TOP PLANTAS
# ============================================================================

st.subheader("🏭 Top 20 Plantas por Volumen")

df_plantas = get_top_plantas()

if not df_plantas.empty:
    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.bar(
            df_plantas.head(20),
            x='volumen_total',
            y='planta',
            color='origen',
            title='Top 20 Plantas por Volumen',
            labels={'volumen_total': 'Volumen Total (m³)', 'planta': 'Planta'},
            orientation='h'
        )
        fig.update_yaxes(categoryorder='total ascending')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(
            df_plantas[['planta', 'origen', 'num_remitos', 'volumen_total']].head(10),
            column_config={
                "planta": "Planta",
                "origen": "Origen",
                "num_remitos": st.column_config.NumberColumn("Remitos", format="%d"),
                "volumen_total": st.column_config.NumberColumn("Volumen (m³)", format="%.0f")
            },
            hide_index=True,
            use_container_width=True
        )
else:
    st.info("No hay datos de plantas disponibles")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption(f"📊 Dashboard actualizado: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
