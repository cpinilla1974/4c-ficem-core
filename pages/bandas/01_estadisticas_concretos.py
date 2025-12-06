import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
from scipy import stats
from io import BytesIO
from database.connection import get_connection

def generar_excel_estadisticas(df_stats, df_por_resistencia, df_por_origen):
    """
    Genera un archivo Excel con estadísticas completas
    """
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_stats.to_excel(writer, sheet_name='Estadísticas Generales', index=True)
        df_por_resistencia.to_excel(writer, sheet_name='Por Resistencia', index=False)
        df_por_origen.to_excel(writer, sheet_name='Por Origen', index=False)

    output.seek(0)
    return output

def app():
    # Obtener conexión de session_state
    ruta_db = st.session_state.get('ruta_db')
    conn = get_connection(ruta_db)

    # Cargar datos desde la base de datos
    df = pd.read_sql_query("SELECT * FROM huella_concretos", conn)

    # Verificar que hay datos
    if df.empty:
        st.warning("No hay datos disponibles en la tabla huella_concretos")
        st.stop()

    # ==================== MODO FANTASMA ====================
    st.sidebar.header("👻 Modo Fantasma")
    modo_fantasma = st.sidebar.checkbox("Modo Fantasma", value=True)

    # Crear mapeo de nombres reales a anónimos
    origenes_unicos = sorted(df['origen'].unique())
    mapeo_fantasma = {origen: f"Compañía {i+1}" for i, origen in enumerate(origenes_unicos)}

    # Aplicar modo fantasma si está activado
    if modo_fantasma:
        df['origen'] = df['origen'].map(mapeo_fantasma)

    # Crear columna de serie (año + origen)
    df["serie"] = df["año"].astype(str) + " - " + df["origen"]

    # ==================== FILTROS ====================
    st.sidebar.header("🔍 Filtros")

    # Filtro por año
    años_disponibles = sorted(df['año'].unique())
    años_seleccionados = st.sidebar.multiselect(
        "Selecciona año(s):",
        options=años_disponibles,
        default=años_disponibles
    )

    # Filtro por origen
    origenes_disponibles = sorted(df['origen'].unique())
    origenes_seleccionados = st.sidebar.multiselect(
        "Selecciona compañía(s):",
        options=origenes_disponibles,
        default=origenes_disponibles
    )

    # Filtro por rango de resistencia
    rest_min = int(df['REST'].min())
    rest_max = int(df['REST'].max())

    rango_resistencia = st.sidebar.slider(
        "Rango de resistencia (MPa):",
        min_value=rest_min,
        max_value=rest_max,
        value=(rest_min, rest_max)
    )

    # Aplicar filtros
    df_filtrado = df[
        (df['año'].isin(años_seleccionados)) &
        (df['origen'].isin(origenes_seleccionados)) &
        (df['REST'] >= rango_resistencia[0]) &
        (df['REST'] <= rango_resistencia[1])
    ]

    if df_filtrado.empty:
        st.warning("No hay datos disponibles con los filtros seleccionados")
        st.stop()

    # ==================== MÉTRICAS PRINCIPALES ====================
    st.header("Estadísticas de Concretos")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if 'num_remitos' in df_filtrado.columns:
            total_remitos = df_filtrado['num_remitos'].sum()
            st.metric("Total Remitos", f"{total_remitos:,}")
        else:
            total_registros = len(df_filtrado)
            st.metric("Total Registros", f"{total_registros:,}")

    with col2:
        huella_promedio = df_filtrado['huella_co2'].mean()
        st.metric("Huella CO₂ Promedio", f"{huella_promedio:.2f} kg/m³")

    with col3:
        if 'volumen' in df_filtrado.columns:
            volumen_total = df_filtrado['volumen'].sum()
            st.metric("Volumen Total", f"{volumen_total:,.0f} m³")
        else:
            st.metric("Volumen Total", "N/A")

    with col4:
        resistencias_unicas = df_filtrado['REST'].nunique()
        st.metric("Resistencias Únicas", f"{resistencias_unicas}")

    st.divider()

    # ==================== TABS DE ANÁLISIS ====================
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Resumen Estadístico",
        "📈 Distribuciones",
        "🔍 Análisis por Resistencia",
        "🏢 Análisis por Compañía",
        "📉 Curvas por Compañía",
        "📅 Análisis Temporal"
    ])

    # ==================== TAB 1: RESUMEN ESTADÍSTICO ====================
    with tab1:
        st.subheader("Estadísticas Descriptivas - Huella CO₂")

        # Calcular estadísticas
        stats = df_filtrado['huella_co2'].describe()

        # Agregar estadísticas adicionales
        stats['coef_variacion'] = (df_filtrado['huella_co2'].std() / df_filtrado['huella_co2'].mean()) * 100
        stats['mediana'] = df_filtrado['huella_co2'].median()
        stats['rango'] = df_filtrado['huella_co2'].max() - df_filtrado['huella_co2'].min()

        # Mostrar en columnas
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Mínimo", f"{stats['min']:.2f} kg/m³")
            st.metric("Percentil 25%", f"{stats['25%']:.2f} kg/m³")
            st.metric("Mediana", f"{stats['mediana']:.2f} kg/m³")

        with col2:
            st.metric("Media", f"{stats['mean']:.2f} kg/m³")
            st.metric("Percentil 75%", f"{stats['75%']:.2f} kg/m³")
            st.metric("Máximo", f"{stats['max']:.2f} kg/m³")

        with col3:
            st.metric("Desviación Estándar", f"{stats['std']:.2f} kg/m³")
            st.metric("Coef. Variación", f"{stats['coef_variacion']:.2f}%")
            st.metric("Rango", f"{stats['rango']:.2f} kg/m³")

        st.divider()

        # Boxplot interactivo
        st.subheader("Diagrama de Caja - Huella CO₂")

        fig_box = go.Figure()

        for origen in df_filtrado['origen'].unique():
            df_origen = df_filtrado[df_filtrado['origen'] == origen]
            fig_box.add_trace(go.Box(
                y=df_origen['huella_co2'],
                name=origen,
                boxmean='sd'  # Mostrar media y desviación estándar
            ))

        fig_box.update_layout(
            title="Distribución de Huella CO₂ por Compañía",
            yaxis_title="Huella CO₂ (kg/m³)",
            showlegend=True,
            height=500
        )

        st.plotly_chart(fig_box, use_container_width=True)

    # ==================== TAB 2: DISTRIBUCIONES ====================
    with tab2:
        st.subheader("Distribuciones de Variables")

        # Histograma de huella CO₂
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Histograma - Huella CO₂")

            bins = st.slider("Número de bins:", 10, 100, 30, key="bins_huella")

            fig_hist = px.histogram(
                df_filtrado,
                x='huella_co2',
                nbins=bins,
                title='Distribución de Huella CO₂',
                labels={'huella_co2': 'Huella CO₂ (kg/m³)', 'count': 'Frecuencia'},
                color_discrete_sequence=['#1f77b4']
            )

            fig_hist.update_layout(
                showlegend=False,
                height=400
            )

            st.plotly_chart(fig_hist, use_container_width=True)

        with col2:
            st.markdown("### Histograma - Resistencia")

            bins_rest = st.slider("Número de bins:", 10, 100, 20, key="bins_rest")

            fig_hist_rest = px.histogram(
                df_filtrado,
                x='REST',
                nbins=bins_rest,
                title='Distribución de Resistencias',
                labels={'REST': 'Resistencia (MPa)', 'count': 'Frecuencia'},
                color_discrete_sequence=['#2ca02c']
            )

            fig_hist_rest.update_layout(
                showlegend=False,
                height=400
            )

            st.plotly_chart(fig_hist_rest, use_container_width=True)

        st.divider()

        # Gráfico de densidad
        st.markdown("### Gráfico de Densidad - Huella CO₂ por Compañía")

        fig_density = go.Figure()

        for origen in df_filtrado['origen'].unique():
            df_origen = df_filtrado[df_filtrado['origen'] == origen]

            fig_density.add_trace(go.Violin(
                y=df_origen['huella_co2'],
                name=origen,
                box_visible=True,
                meanline_visible=True
            ))

        fig_density.update_layout(
            title="Distribución de Densidad por Compañía",
            yaxis_title="Huella CO₂ (kg/m³)",
            height=500
        )

        st.plotly_chart(fig_density, use_container_width=True)

    # ==================== TAB 3: ANÁLISIS POR RESISTENCIA ====================
    with tab3:
        st.subheader("Análisis por Resistencia")

        # Agrupar por resistencia
        df_por_resistencia = df_filtrado.groupby('REST').agg({
            'huella_co2': ['mean', 'std', 'min', 'max', 'count'],
            'volumen': 'sum' if 'volumen' in df_filtrado.columns else 'count'
        }).reset_index()

        df_por_resistencia.columns = ['Resistencia (MPa)', 'Media CO₂', 'Desv. Std CO₂',
                                       'Min CO₂', 'Max CO₂', 'Registros', 'Volumen Total']

        # Gráfico de dispersión con barras de error
        fig_scatter = go.Figure()

        fig_scatter.add_trace(go.Scatter(
            x=df_por_resistencia['Resistencia (MPa)'],
            y=df_por_resistencia['Media CO₂'],
            error_y=dict(
                type='data',
                array=df_por_resistencia['Desv. Std CO₂'],
                visible=True
            ),
            mode='markers+lines',
            name='Media ± Desv. Std',
            marker=dict(size=10, color='#1f77b4'),
            line=dict(width=2)
        ))

        fig_scatter.update_layout(
            title="Huella CO₂ Media por Resistencia (con desviación estándar)",
            xaxis_title="Resistencia (MPa)",
            yaxis_title="Huella CO₂ (kg/m³)",
            height=500
        )

        st.plotly_chart(fig_scatter, use_container_width=True)

        st.divider()

        # Tabla resumen
        st.markdown("### Tabla Resumen por Resistencia")

        st.dataframe(
            df_por_resistencia.style.format({
                'Media CO₂': '{:.2f}',
                'Desv. Std CO₂': '{:.2f}',
                'Min CO₂': '{:.2f}',
                'Max CO₂': '{:.2f}',
                'Volumen Total': '{:,.0f}'
            }),
            use_container_width=True,
            hide_index=True
        )

        # Heatmap de correlación si hay suficientes resistencias
        if df_filtrado['REST'].nunique() > 5:
            st.divider()
            st.markdown("### Correlación Resistencia vs Huella CO₂")

            # Opciones de configuración
            col_config1, col_config2 = st.columns(2)

            with col_config1:
                tipo_corr = st.selectbox(
                    "Tipo de Correlación",
                    options=['Pearson (lineal)', 'Spearman (no lineal)', 'Kendall (ordinal)'],
                    index=0
                )

            with col_config2:
                tipo_modelo = st.selectbox(
                    "Modelo de Regresión",
                    options=['Lineal', 'Polinomio grado 2', 'Polinomio grado 3', 'Logarítmico', 'Exponencial'],
                    index=0
                )

            # Calcular correlación según el tipo seleccionado
            if 'Pearson' in tipo_corr:
                correlacion = df_filtrado[['REST', 'huella_co2']].corr(method='pearson').iloc[0, 1]
                metodo = 'Pearson'
            elif 'Spearman' in tipo_corr:
                correlacion = df_filtrado[['REST', 'huella_co2']].corr(method='spearman').iloc[0, 1]
                metodo = 'Spearman'
            else:  # Kendall
                correlacion = df_filtrado[['REST', 'huella_co2']].corr(method='kendall').iloc[0, 1]
                metodo = 'Kendall'

            col1, col2 = st.columns([2, 1])

            with col1:
                # Crear el scatter plot base
                fig_corr = px.scatter(
                    df_filtrado,
                    x='REST',
                    y='huella_co2',
                    title=f'Correlación {metodo}: {correlacion:.3f}',
                    labels={'REST': 'Resistencia (MPa)', 'huella_co2': 'Huella CO₂ (kg/m³)'}
                )

                # Agregar línea de tendencia según el modelo seleccionado
                import numpy as np
                from scipy import stats

                x = df_filtrado['REST'].values
                y = df_filtrado['huella_co2'].values
                x_sorted = np.sort(x)

                if tipo_modelo == 'Lineal':
                    z = np.polyfit(x, y, 1)
                    p = np.poly1d(z)
                    y_pred = p(x_sorted)
                    r2 = 1 - (np.sum((y - p(x))**2) / np.sum((y - np.mean(y))**2))
                    modelo_texto = f'y = {z[0]:.2f}x + {z[1]:.2f}, R² = {r2:.3f}'

                elif 'grado 2' in tipo_modelo:
                    z = np.polyfit(x, y, 2)
                    p = np.poly1d(z)
                    y_pred = p(x_sorted)
                    r2 = 1 - (np.sum((y - p(x))**2) / np.sum((y - np.mean(y))**2))
                    modelo_texto = f'y = {z[0]:.2f}x² + {z[1]:.2f}x + {z[2]:.2f}, R² = {r2:.3f}'

                elif 'grado 3' in tipo_modelo:
                    z = np.polyfit(x, y, 3)
                    p = np.poly1d(z)
                    y_pred = p(x_sorted)
                    r2 = 1 - (np.sum((y - p(x))**2) / np.sum((y - np.mean(y))**2))
                    modelo_texto = f'Polinomio grado 3, R² = {r2:.3f}'

                elif tipo_modelo == 'Logarítmico':
                    # Evitar log(0) filtrando valores <= 0
                    mask = x > 0
                    x_log = x[mask]
                    y_log = y[mask]
                    z = np.polyfit(np.log(x_log), y_log, 1)
                    y_pred = z[0] * np.log(x_sorted[x_sorted > 0]) + z[1]
                    x_sorted = x_sorted[x_sorted > 0]
                    r2 = 1 - (np.sum((y_log - (z[0] * np.log(x_log) + z[1]))**2) / np.sum((y_log - np.mean(y_log))**2))
                    modelo_texto = f'y = {z[0]:.2f}·ln(x) + {z[1]:.2f}, R² = {r2:.3f}'

                else:  # Exponencial
                    # Evitar log(0) o valores negativos
                    mask = y > 0
                    x_exp = x[mask]
                    y_exp = y[mask]
                    z = np.polyfit(x_exp, np.log(y_exp), 1)
                    y_pred = np.exp(z[1]) * np.exp(z[0] * x_sorted)
                    r2 = 1 - (np.sum((y_exp - np.exp(z[1]) * np.exp(z[0] * x_exp))**2) / np.sum((y_exp - np.mean(y_exp))**2))
                    modelo_texto = f'y = {np.exp(z[1]):.2f}·e^({z[0]:.4f}x), R² = {r2:.3f}'

                # Agregar la línea de tendencia al gráfico
                fig_corr.add_scatter(
                    x=x_sorted,
                    y=y_pred,
                    mode='lines',
                    name=modelo_texto,
                    line=dict(color='red', width=2)
                )

                st.plotly_chart(fig_corr, use_container_width=True)

            with col2:
                st.metric("Coeficiente de Correlación", f"{correlacion:.3f}")

                if abs(correlacion) < 0.3:
                    st.info("Correlación débil")
                elif abs(correlacion) < 0.7:
                    st.info("Correlación moderada")
                else:
                    st.info("Correlación fuerte")

                # Información sobre el método seleccionado
                st.markdown("---")
                if 'Pearson' in tipo_corr:
                    st.caption("**Pearson**: Mide relación lineal entre variables")
                elif 'Spearman' in tipo_corr:
                    st.caption("**Spearman**: Mide relación monotónica (lineal o no lineal)")
                else:
                    st.caption("**Kendall**: Mide concordancia ordinal entre variables")

    # ==================== TAB 4: ANÁLISIS POR COMPAÑÍA ====================
    with tab4:
        st.subheader("Análisis Comparativo por Compañía")

        # Agrupar por origen
        df_por_origen = df_filtrado.groupby('origen').agg({
            'huella_co2': ['mean', 'std', 'min', 'max', 'count'],
            'volumen': 'sum' if 'volumen' in df_filtrado.columns else 'count',
            'REST': ['min', 'max']
        }).reset_index()

        df_por_origen.columns = ['Compañía', 'Media CO₂', 'Desv. Std CO₂',
                                  'Min CO₂', 'Max CO₂', 'Registros', 'Volumen Total',
                                  'Rest Min', 'Rest Max']

        # Gráfico de barras comparativo
        fig_bar = go.Figure()

        fig_bar.add_trace(go.Bar(
            name='Media CO₂',
            x=df_por_origen['Compañía'],
            y=df_por_origen['Media CO₂'],
            error_y=dict(type='data', array=df_por_origen['Desv. Std CO₂']),
            marker_color='#1f77b4'
        ))

        fig_bar.update_layout(
            title="Huella CO₂ Media por Compañía",
            xaxis_title="Compañía",
            yaxis_title="Huella CO₂ (kg/m³)",
            height=500
        )

        st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        # Tabla comparativa
        st.markdown("### Tabla Comparativa por Compañía")

        st.dataframe(
            df_por_origen.style.format({
                'Media CO₂': '{:.2f}',
                'Desv. Std CO₂': '{:.2f}',
                'Min CO₂': '{:.2f}',
                'Max CO₂': '{:.2f}',
                'Volumen Total': '{:,.0f}'
            }),
            use_container_width=True,
            hide_index=True
        )

        # Gráfico de participación
        if 'volumen' in df_filtrado.columns:
            st.divider()
            st.markdown("### Participación de Volumen por Compañía")

            fig_pie = px.pie(
                df_por_origen,
                values='Volumen Total',
                names='Compañía',
                title='Distribución del Volumen Total',
                hole=0.4
            )

            st.plotly_chart(fig_pie, use_container_width=True)

    # ==================== TAB 5: CURVAS POR COMPAÑÍA ====================
    with tab5:
        st.subheader("Curvas CO₂ vs Resistencia por Compañía")

        # Configuración
        col_config1, col_config2 = st.columns(2)

        with col_config1:
            tipo_modelo_curvas = st.selectbox(
                "Modelo de Regresión para Curvas",
                options=['Lineal', 'Polinomio grado 2', 'Polinomio grado 3', 'Logarítmico'],
                index=1,
                key='modelo_curvas'
            )

        with col_config2:
            mostrar_bandas_confianza = st.checkbox("Mostrar bandas de confianza (percentiles 25-75)", value=False)

        # Selector de compañías a mostrar
        companias_disponibles = df_filtrado['origen'].unique().tolist()
        companias_seleccionadas = st.multiselect(
            "Selecciona compañías a mostrar",
            options=companias_disponibles,
            default=companias_disponibles
        )

        if not companias_seleccionadas:
            st.warning("Selecciona al menos una compañía")
        else:
            df_curvas = df_filtrado[df_filtrado['origen'].isin(companias_seleccionadas)]

            # ===== GRÁFICO PRINCIPAL: TODAS LAS CURVAS SUPERPUESTAS =====
            st.markdown("### Comparación de Curvas")

            fig_curvas = go.Figure()

            # Paleta de colores
            colores_companias = px.colors.qualitative.Set2

            # Diccionario para almacenar resultados
            resultados_modelos = {}

            for idx, compania in enumerate(companias_seleccionadas):
                df_comp = df_curvas[df_curvas['origen'] == compania]

                if len(df_comp) < 3:
                    continue

                x = df_comp['REST'].values
                y = df_comp['huella_co2'].values
                color = colores_companias[idx % len(colores_companias)]

                # Agregar scatter
                fig_curvas.add_scatter(
                    x=x,
                    y=y,
                    mode='markers',
                    name=f'{compania} (datos)',
                    marker=dict(color=color, size=6, opacity=0.5),
                    showlegend=True
                )

                # Calcular modelo
                x_sorted = np.linspace(x.min(), x.max(), 100)

                if tipo_modelo_curvas == 'Lineal':
                    z = np.polyfit(x, y, 1)
                    p = np.poly1d(z)
                    y_pred = p(x_sorted)
                    r2 = 1 - (np.sum((y - p(x))**2) / np.sum((y - np.mean(y))**2))
                    resultados_modelos[compania] = {
                        'coef': z,
                        'r2': r2,
                        'ecuacion': f'y = {z[0]:.2f}x + {z[1]:.2f}'
                    }

                elif 'grado 2' in tipo_modelo_curvas:
                    z = np.polyfit(x, y, 2)
                    p = np.poly1d(z)
                    y_pred = p(x_sorted)
                    r2 = 1 - (np.sum((y - p(x))**2) / np.sum((y - np.mean(y))**2))
                    resultados_modelos[compania] = {
                        'coef': z,
                        'r2': r2,
                        'ecuacion': f'y = {z[0]:.3f}x² + {z[1]:.2f}x + {z[2]:.2f}'
                    }

                elif 'grado 3' in tipo_modelo_curvas:
                    z = np.polyfit(x, y, 3)
                    p = np.poly1d(z)
                    y_pred = p(x_sorted)
                    r2 = 1 - (np.sum((y - p(x))**2) / np.sum((y - np.mean(y))**2))
                    resultados_modelos[compania] = {
                        'coef': z,
                        'r2': r2,
                        'ecuacion': f'Polinomio grado 3'
                    }

                else:  # Logarítmico
                    mask = x > 0
                    x_log = x[mask]
                    y_log = y[mask]
                    z = np.polyfit(np.log(x_log), y_log, 1)
                    y_pred = z[0] * np.log(x_sorted[x_sorted > 0]) + z[1]
                    x_sorted = x_sorted[x_sorted > 0]
                    r2 = 1 - (np.sum((y_log - (z[0] * np.log(x_log) + z[1]))**2) / np.sum((y_log - np.mean(y_log))**2))
                    resultados_modelos[compania] = {
                        'coef': z,
                        'r2': r2,
                        'ecuacion': f'y = {z[0]:.2f}·ln(x) + {z[1]:.2f}'
                    }

                # Agregar línea de tendencia
                fig_curvas.add_scatter(
                    x=x_sorted,
                    y=y_pred,
                    mode='lines',
                    name=f'{compania} (R²={r2:.3f})',
                    line=dict(color=color, width=3)
                )

                # Bandas de confianza
                if mostrar_bandas_confianza:
                    # Calcular percentiles por bins de resistencia
                    bins = np.linspace(x.min(), x.max(), 10)
                    df_comp_copy = df_comp.copy()
                    df_comp_copy['bin'] = pd.cut(df_comp_copy['REST'], bins=bins)
                    percentiles = df_comp_copy.groupby('bin')['huella_co2'].quantile([0.25, 0.75]).unstack()

                    if len(percentiles) > 0:
                        bin_centers = [(interval.left + interval.right) / 2 for interval in percentiles.index]
                        q25 = percentiles[0.25].values
                        q75 = percentiles[0.75].values

                        fig_curvas.add_scatter(
                            x=bin_centers + bin_centers[::-1],
                            y=list(q75) + list(q25[::-1]),
                            fill='toself',
                            fillcolor=color,
                            opacity=0.1,
                            line=dict(width=0),
                            showlegend=False,
                            name=f'{compania} (P25-P75)'
                        )

            fig_curvas.update_layout(
                title='Comparación de Curvas CO₂ vs Resistencia',
                xaxis_title='Resistencia (MPa)',
                yaxis_title='Huella CO₂ (kg/m³)',
                height=600,
                hovermode='closest'
            )

            st.plotly_chart(fig_curvas, use_container_width=True)

            # ===== TABLA DE COEFICIENTES Y R² =====
            st.divider()
            st.markdown("### Coeficientes de los Modelos")

            if resultados_modelos:
                df_resultados = pd.DataFrame([
                    {
                        'Compañía': comp,
                        'Ecuación': res['ecuacion'],
                        'R²': res['r2']
                    }
                    for comp, res in resultados_modelos.items()
                ])

                st.dataframe(
                    df_resultados.style.format({'R²': '{:.3f}'}),
                    use_container_width=True,
                    hide_index=True
                )

            # ===== TABLA COMPARATIVA POR RESISTENCIAS ESTÁNDAR =====
            st.divider()
            st.markdown("### Predicciones por Resistencia Estándar")

            resistencias_estandar = [20, 25, 30, 35, 40, 50]
            predicciones = []

            for compania, res in resultados_modelos.items():
                row = {'Compañía': compania}
                z = res['coef']

                for rest in resistencias_estandar:
                    if tipo_modelo_curvas == 'Lineal':
                        pred = z[0] * rest + z[1]
                    elif 'grado 2' in tipo_modelo_curvas:
                        pred = z[0] * rest**2 + z[1] * rest + z[2]
                    elif 'grado 3' in tipo_modelo_curvas:
                        pred = z[0] * rest**3 + z[1] * rest**2 + z[2] * rest + z[3]
                    else:  # Logarítmico
                        pred = z[0] * np.log(rest) + z[1]

                    row[f'{rest} MPa'] = pred

                predicciones.append(row)

            if predicciones:
                df_predicciones = pd.DataFrame(predicciones)

                # Aplicar formato con colores
                def color_scale(val):
                    if pd.isna(val):
                        return ''
                    # Verde para valores bajos, rojo para altos
                    if val < 200:
                        return 'background-color: #90EE90'
                    elif val < 250:
                        return 'background-color: #FFFFE0'
                    elif val < 300:
                        return 'background-color: #FFD700'
                    else:
                        return 'background-color: #FFA07A'

                styled_df = df_predicciones.style.format(
                    {col: '{:.1f}' for col in df_predicciones.columns if 'MPa' in col}
                ).applymap(
                    color_scale,
                    subset=[col for col in df_predicciones.columns if 'MPa' in col]
                )

                st.dataframe(styled_df, use_container_width=True, hide_index=True)

            # ===== GRÁFICOS INDIVIDUALES POR COMPAÑÍA =====
            st.divider()
            st.markdown("### Gráficos Individuales por Compañía")

            for compania in companias_seleccionadas:
                df_comp = df_curvas[df_curvas['origen'] == compania]

                if len(df_comp) < 3:
                    st.warning(f"No hay suficientes datos para {compania}")
                    continue

                with st.expander(f"📊 {compania}"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        x = df_comp['REST'].values
                        y = df_comp['huella_co2'].values

                        fig_ind = px.scatter(
                            df_comp,
                            x='REST',
                            y='huella_co2',
                            title=f'{compania} - CO₂ vs Resistencia',
                            labels={'REST': 'Resistencia (MPa)', 'huella_co2': 'Huella CO₂ (kg/m³)'}
                        )

                        # Agregar línea de tendencia
                        if compania in resultados_modelos:
                            x_sorted = np.linspace(x.min(), x.max(), 100)
                            z = resultados_modelos[compania]['coef']

                            if tipo_modelo_curvas == 'Lineal':
                                p = np.poly1d(z)
                                y_pred = p(x_sorted)
                            elif 'grado 2' in tipo_modelo_curvas:
                                p = np.poly1d(z)
                                y_pred = p(x_sorted)
                            elif 'grado 3' in tipo_modelo_curvas:
                                p = np.poly1d(z)
                                y_pred = p(x_sorted)
                            else:  # Logarítmico
                                x_sorted = x_sorted[x_sorted > 0]
                                y_pred = z[0] * np.log(x_sorted) + z[1]

                            fig_ind.add_scatter(
                                x=x_sorted,
                                y=y_pred,
                                mode='lines',
                                name='Tendencia',
                                line=dict(color='red', width=2)
                            )

                        st.plotly_chart(fig_ind, use_container_width=True)

                    with col2:
                        if compania in resultados_modelos:
                            res = resultados_modelos[compania]
                            st.metric("R²", f"{res['r2']:.3f}")
                            st.markdown(f"**Ecuación:**\n\n`{res['ecuacion']}`")

                            # Estadísticas
                            st.markdown("---")
                            st.markdown("**Estadísticas:**")
                            st.metric("N° observaciones", len(df_comp))
                            st.metric("Resistencia Media", f"{df_comp['REST'].mean():.1f} MPa")
                            st.metric("CO₂ Medio", f"{df_comp['huella_co2'].mean():.1f} kg/m³")

    # ==================== TAB 6: ANÁLISIS TEMPORAL ====================
    with tab6:
        st.subheader("Análisis Temporal")

        if len(df_filtrado['año'].unique()) > 1:
            # Evolución temporal
            agg_dict = {
                'huella_co2': 'mean',
                'volumen': 'sum' if 'volumen' in df_filtrado.columns else 'count'
            }
            if 'num_remitos' in df_filtrado.columns:
                agg_dict['num_remitos'] = 'sum'

            df_temporal = df_filtrado.groupby(['año', 'origen']).agg(agg_dict).reset_index()

            # Gráfico de líneas
            fig_temporal = px.line(
                df_temporal,
                x='año',
                y='huella_co2',
                color='origen',
                markers=True,
                title='Evolución Temporal de Huella CO₂ Media',
                labels={'año': 'Año', 'huella_co2': 'Huella CO₂ (kg/m³)', 'origen': 'Compañía'}
            )

            fig_temporal.update_layout(height=500)

            st.plotly_chart(fig_temporal, use_container_width=True)

            st.divider()

            # Tabla temporal
            st.markdown("### Datos por Año y Compañía")

            if 'num_remitos' in df_temporal.columns:
                pivot_temporal = df_temporal.pivot(index='año', columns='origen', values='num_remitos')
                st.dataframe(
                    pivot_temporal.style.format('{:,.0f}'),
                    use_container_width=True
                )
            else:
                pivot_temporal = df_temporal.pivot(index='año', columns='origen', values='huella_co2')
                st.dataframe(
                    pivot_temporal.style.format('{:.2f}'),
                    use_container_width=True
                )

            # Gráfico de volumen si está disponible
            if 'volumen' in df_filtrado.columns:
                st.divider()
                st.markdown("### Evolución del Volumen de Producción")

                fig_volumen = px.bar(
                    df_temporal,
                    x='año',
                    y='volumen',
                    color='origen',
                    barmode='group',
                    title='Volumen de Producción por Año',
                    labels={'año': 'Año', 'volumen': 'Volumen (m³)', 'origen': 'Compañía'}
                )

                fig_volumen.update_layout(height=500)

                st.plotly_chart(fig_volumen, use_container_width=True)

            # Gráfico de número de remitos si está disponible
            if 'num_remitos' in df_filtrado.columns:
                st.divider()
                st.markdown("### Evolución del Número de Remitos")

                # Agrupar por año y origen para remitos
                df_temporal_remitos = df_filtrado.groupby(['año', 'origen']).agg({
                    'num_remitos': 'sum'
                }).reset_index()

                fig_remitos = px.bar(
                    df_temporal_remitos,
                    x='año',
                    y='num_remitos',
                    color='origen',
                    barmode='group',
                    title='Número de Remitos por Año',
                    labels={'año': 'Año', 'num_remitos': 'Número de Remitos', 'origen': 'Compañía'}
                )

                fig_remitos.update_layout(height=500)

                st.plotly_chart(fig_remitos, use_container_width=True)
        else:
            st.info("Se requieren datos de múltiples años para el análisis temporal.")

    # ==================== EXPORTACIÓN ====================
    st.divider()
    st.header("📥 Exportar Datos")

    # Preparar datos para exportación
    stats_export = pd.DataFrame(df_filtrado['huella_co2'].describe()).T
    stats_export['coef_variacion'] = (df_filtrado['huella_co2'].std() / df_filtrado['huella_co2'].mean()) * 100
    stats_export['mediana'] = df_filtrado['huella_co2'].median()

    # Generar Excel
    excel_data = generar_excel_estadisticas(stats_export, df_por_resistencia, df_por_origen)

    st.download_button(
        label="📥 Descargar Estadísticas Completas (Excel)",
        data=excel_data,
        file_name="estadisticas_concretos_completo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    app()
