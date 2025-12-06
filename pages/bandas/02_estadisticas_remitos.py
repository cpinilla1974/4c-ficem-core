import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
import re
from datetime import datetime
from scipy import stats
from database.connection import get_connection

# Funciones cacheadas para optimizar rendimiento
@st.cache_data(ttl=600)  # Cache por 10 minutos
def cargar_metadatos(_conn):
    """Carga solo metadatos básicos de la tabla"""
    query = """
        SELECT
            COUNT(*) as total_remitos,
            MIN(fecha) as fecha_min,
            MAX(fecha) as fecha_max,
            COUNT(DISTINCT compania) as num_companias,
            SUM(volumen) as volumen_total,
            AVG(huella_co2) as huella_promedio
        FROM remitos_concretos
    """
    return pd.read_sql_query(query, _conn).iloc[0]

@st.cache_data(ttl=600)
def cargar_companias_plantas(_conn):
    """Carga lista de compañías y plantas disponibles"""
    query = """
        SELECT DISTINCT compania, planta
        FROM remitos_concretos
        ORDER BY compania, planta
    """
    df = pd.read_sql_query(query, _conn)
    return df['compania'].unique(), df

@st.cache_data(ttl=600)
def cargar_remitos_filtrados(_conn, companias, plantas, fecha_inicio, fecha_fin, res_min, res_max):
    """Carga remitos con filtros aplicados directamente en SQL"""

    # Construir filtros SQL con valores literales escapados
    filtros = []

    if companias:
        comp_list = "', '".join(str(c).replace("'", "''") for c in companias)
        filtros.append(f"compania IN ('{comp_list}')")

    if plantas:
        plant_list = "', '".join(str(p).replace("'", "''") for p in plantas)
        filtros.append(f"planta IN ('{plant_list}')")

    if fecha_inicio:
        filtros.append(f"fecha >= '{fecha_inicio}'")

    if fecha_fin:
        filtros.append(f"fecha <= '{fecha_fin}'")

    filtros.append(f"resistencia >= {res_min} AND resistencia <= {res_max}")

    where_clause = " AND ".join(filtros) if filtros else "1=1"

    query = f"""
        SELECT
            id_remito, compania, planta, fecha, año, mes, trimestre,
            formulacion, resistencia, volumen, huella_co2,
            proyecto, cliente, tipo_cemento, slump, contenido_cemento,
            a1_intensidad, a2_intensidad, a3_intensidad
        FROM remitos_concretos
        WHERE {where_clause}
        ORDER BY fecha DESC
        LIMIT 50000
    """

    df = pd.read_sql_query(query, _conn)
    df['fecha'] = pd.to_datetime(df['fecha'])
    return df

def validar_csv_remitos(df):
    """Valida que el CSV tenga las columnas obligatorias"""
    columnas_obligatorias = [
        'id_remito', 'compania', 'planta', 'fecha', 'año',
        'formulacion', 'resistencia', 'volumen', 'huella_co2'
    ]

    errores = []
    faltantes = [col for col in columnas_obligatorias if col not in df.columns]
    if faltantes:
        errores.append(f"Faltan columnas obligatorias: {', '.join(faltantes)}")

    return errores

def cargar_csv_en_db(conn, df, nombre_archivo):
    """Carga el CSV validado en la base de datos"""
    cursor = conn.cursor()

    total_original = len(df)

    # Convertir tipos
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    df['volumen'] = pd.to_numeric(df['volumen'], errors='coerce')
    df['resistencia'] = pd.to_numeric(df['resistencia'], errors='coerce')
    df['huella_co2'] = pd.to_numeric(df['huella_co2'], errors='coerce')

    # Filtrar registros con valores nulos o inválidos en campos obligatorios
    df_valido = df.dropna(subset=['resistencia', 'volumen', 'huella_co2', 'fecha']).copy()
    df_valido = df_valido[(df_valido['resistencia'] > 0) & (df_valido['volumen'] > 0)]
    registros_descartados = total_original - len(df_valido)

    if registros_descartados > 0:
        st.warning(f"⚠️ Se descartaron {registros_descartados:,} registros con valores nulos o inválidos (resistencia/volumen <= 0)")

    # Calcular mes y trimestre si no existen
    if 'mes' not in df_valido.columns or df_valido['mes'].isna().all():
        df_valido['mes'] = df_valido['fecha'].dt.month
    if 'trimestre' not in df_valido.columns or df_valido['trimestre'].isna().all():
        df_valido['trimestre'] = df_valido['fecha'].dt.quarter

    # Verificar duplicados en DB
    registros_nuevos = []
    registros_existentes = 0

    for _, row in df_valido.iterrows():
        cursor.execute(
            "SELECT COUNT(*) FROM remitos_concretos WHERE compania = ? AND id_remito = ?",
            (row['compania'], str(row['id_remito']))
        )
        if cursor.fetchone()[0] == 0:
            registros_nuevos.append(row)
        else:
            registros_existentes += 1

    if registros_nuevos:
        df_nuevos = pd.DataFrame(registros_nuevos)
        df_nuevos.to_sql('remitos_concretos', conn, if_exists='append', index=False)
        conn.commit()

    return len(registros_nuevos), registros_existentes

def app():
    st.title("📊 Estadísticas de Remitos")

    # Obtener conexión
    ruta_db = st.session_state.get('ruta_db')
    conn = get_connection(ruta_db)

    # Verificar si hay datos
    result = pd.read_sql_query("SELECT COUNT(*) as total FROM remitos_concretos", conn)
    total_remitos = result['total'].iloc[0]

    # Sección de carga en expander cerrado
    with st.expander("📥 Carga de Datos", expanded=False):
        col1, col2 = st.columns([2, 1])

        with col1:
            # Buscar archivos automáticamente
            base_path = os.getenv("COMUN_FILES_PATH")
            if base_path and st.button("🔍 Buscar archivos remitos_concretos_*.csv"):
                patron = os.path.join(base_path, "remitos_concretos_*.csv")
                archivos = glob.glob(patron)

                if not archivos:
                    st.info("No se encontraron archivos")
                else:
                    st.success(f"Se encontraron {len(archivos)} archivo(s)")

                    for archivo in archivos:
                        nombre = os.path.basename(archivo)
                        with st.expander(f"📄 {nombre}"):
                            try:
                                df = pd.read_csv(archivo)
                                st.write(f"**Registros:** {len(df):,}")

                                errores = validar_csv_remitos(df)
                                if errores:
                                    for error in errores:
                                        st.error(error)
                                else:
                                    if st.button(f"Cargar {nombre}", key=f"btn_{nombre}"):
                                        nuevos, existentes = cargar_csv_en_db(conn, df, nombre)
                                        st.success(f"✅ {nuevos:,} nuevos remitos cargados")
                                        if existentes > 0:
                                            st.info(f"ℹ️ {existentes:,} remitos ya existían")
                                        st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

        with col2:
            # Carga manual
            uploaded_file = st.file_uploader("O cargar archivo CSV", type=['csv'])
            if uploaded_file:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.write(f"**Registros:** {len(df):,}")

                    errores = validar_csv_remitos(df)
                    if errores:
                        for error in errores:
                            st.error(error)
                    else:
                        if st.button("💾 Cargar archivo"):
                            nuevos, existentes = cargar_csv_en_db(conn, df, uploaded_file.name)
                            st.success(f"✅ {nuevos:,} nuevos remitos")
                            if existentes > 0:
                                st.info(f"ℹ️ {existentes:,} ya existían")
                            st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # st.divider()

    # Si no hay datos, detener aquí
    if total_remitos == 0:
        st.info("No hay datos cargados. Utiliza la sección de carga para importar archivos CSV.")
        return

    # ==================== CARGAR METADATOS (RÁPIDO) ====================
    with st.spinner("Cargando información general..."):
        metadatos = cargar_metadatos(conn)
        companias_disponibles, df_comp_plantas = cargar_companias_plantas(conn)

    # ==================== MODO FANTASMA ====================
    modo_fantasma = st.sidebar.checkbox("👻 Modo Fantasma", value=True, key="modo_fantasma_remitos")

    # Crear mapeo de nombres reales a anónimos para COMPAÑÍAS
    companias_unicas_sorted = sorted(companias_disponibles)
    mapeo_fantasma_comp = {compania: f"Compañía {i+1}" for i, compania in enumerate(companias_unicas_sorted)}
    mapeo_inverso_comp = {v: k for k, v in mapeo_fantasma_comp.items()}

    # Crear mapeo de nombres reales a anónimos para PLANTAS (agrupadas por compañía)
    mapeo_fantasma_planta = {}
    for compania in companias_unicas_sorted:
        plantas_de_compania = sorted(df_comp_plantas[df_comp_plantas['compania'] == compania]['planta'].unique())
        for j, planta in enumerate(plantas_de_compania, 1):
            compania_anonima = mapeo_fantasma_comp[compania]
            mapeo_fantasma_planta[planta] = f"{compania_anonima} - Planta {j}"

    # Aplicar modo fantasma a la lista de compañías
    if modo_fantasma:
        companias_para_mostrar = [mapeo_fantasma_comp[c] for c in companias_unicas_sorted]
    else:
        companias_para_mostrar = list(companias_unicas_sorted)

    # Métricas generales (sin cargar todos los datos)
    st.subheader("📈 Resumen General (Base de Datos Completa)")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Remitos", f"{int(metadatos['total_remitos']):,}")
    with col2:
        st.metric("Volumen Total (m³)", f"{metadatos['volumen_total']:,.0f}")
    with col3:
        st.metric("Huella Promedio", f"{metadatos['huella_promedio']:.2f} kg/m³")
    with col4:
        st.metric("Compañías", int(metadatos['num_companias']))

    # st.divider()

    # ==================== FILTROS PARA CARGA SELECTIVA ====================
    with st.expander("🔍 Filtros de Análisis", expanded=True):
        st.info("⚡ Los filtros cargan solo los datos necesarios para mejorar el rendimiento")

        col1, col2 = st.columns(2)

        with col1:
            companias_sel_display = st.multiselect(
                "Compañías",
                options=companias_para_mostrar,
                default=companias_para_mostrar[:2] if len(companias_para_mostrar) > 1 else companias_para_mostrar
            )

            # Convertir de vuelta a nombres reales si está en modo fantasma
            if modo_fantasma:
                companias_sel = tuple([mapeo_inverso_comp[c] for c in companias_sel_display])
            else:
                companias_sel = tuple(companias_sel_display)

        with col2:
            # Filtrar plantas según compañías seleccionadas
            if companias_sel:
                plantas_disponibles_reales = df_comp_plantas[df_comp_plantas['compania'].isin(companias_sel)]['planta'].unique()

                # Aplicar modo fantasma a las plantas si está activado
                if modo_fantasma:
                    plantas_para_mostrar = [mapeo_fantasma_planta[p] for p in sorted(plantas_disponibles_reales)]
                    mapeo_inverso_planta = {v: k for k, v in mapeo_fantasma_planta.items() if k in plantas_disponibles_reales}
                else:
                    plantas_para_mostrar = sorted(plantas_disponibles_reales)

                plantas_sel_display = st.multiselect(
                    "Plantas",
                    options=plantas_para_mostrar,
                    default=plantas_para_mostrar
                )

                # Convertir de vuelta a nombres reales si está en modo fantasma
                if modo_fantasma:
                    plantas_sel = tuple([mapeo_inverso_planta[p] for p in plantas_sel_display])
                else:
                    plantas_sel = tuple(plantas_sel_display)
            else:
                plantas_sel = ()

        col3, col4 = st.columns(2)

        with col3:
            fecha_inicio = st.date_input(
                "Fecha inicio",
                value=pd.to_datetime(metadatos['fecha_min']),
                min_value=pd.to_datetime(metadatos['fecha_min']),
                max_value=pd.to_datetime(metadatos['fecha_max'])
            )

        with col4:
            fecha_fin = st.date_input(
                "Fecha fin",
                value=pd.to_datetime(metadatos['fecha_max']),
                min_value=pd.to_datetime(metadatos['fecha_min']),
                max_value=pd.to_datetime(metadatos['fecha_max'])
            )

        rango_resistencia = st.slider(
            "Rango de Resistencia (MPa)",
            0.0, 100.0, (10.0, 80.0)
        )

        # ==================== CARGAR DATOS FILTRADOS (CON CACHE) ====================
        if not companias_sel:
            st.warning("⚠️ Selecciona al menos una compañía para visualizar datos")
            return

        with st.spinner(f"Cargando datos filtrados (máximo 50,000 registros)..."):
            df_remitos = cargar_remitos_filtrados(
                conn,
                companias_sel,
                plantas_sel,
                fecha_inicio.strftime('%Y-%m-%d'),
                fecha_fin.strftime('%Y-%m-%d'),
                rango_resistencia[0],
                rango_resistencia[1]
            )

        if len(df_remitos) == 0:
            st.warning("No hay datos con los filtros seleccionados")
            return

        # Aplicar modo fantasma a los datos cargados (compañías y plantas)
        if modo_fantasma:
            df_remitos['compania'] = df_remitos['compania'].map(mapeo_fantasma_comp)
            df_remitos['planta'] = df_remitos['planta'].map(mapeo_fantasma_planta)

        if len(df_remitos) >= 50000:
            st.warning(f"⚠️ Cargados {len(df_remitos):,} remitos (límite alcanzado). Ajusta los filtros para análisis más específicos.")
        else:
            st.success(f"✅ Cargados {len(df_remitos):,} remitos para análisis")

        # El resto del código usa df_remitos que ahora está filtrado
        df_filtrado = df_remitos  # Ya viene filtrado de SQL

    # st.divider()

    # Tabs de visualización
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Nube de Puntos",
        "📈 Distribuciones",
        "📦 Box Plots",
        "📅 Evolución Temporal"
    ])

    with tab1:
        st.subheader("Resistencia vs Huella CO₂")

        # Opciones de visualización
        col1, col2, col3 = st.columns(3)
        with col1:
            color_por = st.selectbox(
                "Colorear por",
                options=['compania', 'planta', 'año'],
                index=0
            )
        with col2:
            size_por = st.selectbox(
                "Tamaño por",
                options=['volumen', 'Ninguno'],
                index=0
            )
        with col3:
            mostrar_trendline = st.checkbox("Mostrar línea de tendencia", value=True)

        # Crear gráfico scatter
        fig = px.scatter(
            df_filtrado,
            x='resistencia',
            y='huella_co2',
            color=color_por,
            size='volumen' if size_por == 'volumen' else None,
            hover_data=['id_remito', 'planta', 'formulacion', 'fecha'],
            title=f"Resistencia vs Huella CO₂ ({len(df_filtrado):,} remitos)",
            labels={
                'resistencia': 'Resistencia (MPa)',
                'huella_co2': 'Huella CO₂ (kg/m³)',
                'volumen': 'Volumen (m³)'
            },
            trendline='lowess' if mostrar_trendline else None,
            height=600
        )

        fig.update_layout(
            xaxis_title="Resistencia (MPa)",
            yaxis_title="Huella CO₂ (kg/m³)"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Estadísticas de correlación
        col1, col2, col3 = st.columns(3)
        with col1:
            from scipy import stats
            corr_pearson = stats.pearsonr(df_filtrado['resistencia'], df_filtrado['huella_co2'])[0]
            st.metric("Correlación Pearson", f"{corr_pearson:.3f}")
        with col2:
            corr_spearman = stats.spearmanr(df_filtrado['resistencia'], df_filtrado['huella_co2'])[0]
            st.metric("Correlación Spearman", f"{corr_spearman:.3f}")
        with col3:
            st.metric("N° puntos", f"{len(df_filtrado):,}")

    with tab2:
        st.subheader("Distribuciones")

        col1, col2 = st.columns(2)

        with col1:
            # Histograma de resistencias
            fig_hist_res = px.histogram(
                df_filtrado,
                x='resistencia',
                color='compania',
                nbins=30,
                title="Distribución de Resistencias",
                labels={'resistencia': 'Resistencia (MPa)', 'count': 'Cantidad de Remitos'}
            )
            st.plotly_chart(fig_hist_res, use_container_width=True)

        with col2:
            # Histograma de huellas
            fig_hist_co2 = px.histogram(
                df_filtrado,
                x='huella_co2',
                color='compania',
                nbins=30,
                title="Distribución de Huella CO₂",
                labels={'huella_co2': 'Huella CO₂ (kg/m³)', 'count': 'Cantidad de Remitos'}
            )
            st.plotly_chart(fig_hist_co2, use_container_width=True)

        # Violin plot
        fig_violin = px.violin(
            df_filtrado,
            y='huella_co2',
            x='compania',
            box=True,
            points='all',
            title="Distribución de Huella CO₂ por Compañía",
            labels={'huella_co2': 'Huella CO₂ (kg/m³)'}
        )
        st.plotly_chart(fig_violin, use_container_width=True)

    with tab3:
        st.subheader("Box Plots por Resistencia")

        # Agrupar resistencias en rangos
        df_filtrado['rango_resistencia'] = pd.cut(
            df_filtrado['resistencia'],
            bins=[0, 20, 25, 30, 35, 40, 50, 100],
            labels=['<20', '20-25', '25-30', '30-35', '35-40', '40-50', '>50']
        )

        fig_box = px.box(
            df_filtrado,
            x='rango_resistencia',
            y='huella_co2',
            color='compania',
            title="Huella CO₂ por Rangos de Resistencia",
            labels={
                'rango_resistencia': 'Rango de Resistencia (MPa)',
                'huella_co2': 'Huella CO₂ (kg/m³)'
            }
        )
        st.plotly_chart(fig_box, use_container_width=True)

        # Tabla de estadísticas por rango
        st.subheader("Estadísticas por Rango")
        stats_by_range = df_filtrado.groupby('rango_resistencia')['huella_co2'].agg([
            ('N° Remitos', 'count'),
            ('Media', 'mean'),
            ('Mediana', 'median'),
            ('Desv. Est.', 'std'),
            ('Mínimo', 'min'),
            ('Máximo', 'max')
        ]).round(2)

        st.dataframe(stats_by_range, use_container_width=True)

    with tab4:
        st.subheader("Evolución Temporal")

        # Agrupar por mes
        df_temporal = df_filtrado.copy()
        df_temporal['año_mes'] = df_temporal['fecha'].dt.to_period('M').astype(str)

        df_agrupado = df_temporal.groupby(['año_mes', 'compania']).agg({
            'huella_co2': 'mean',
            'volumen': 'sum',
            'id_remito': 'count'
        }).reset_index()

        df_agrupado.columns = ['año_mes', 'compania', 'huella_promedio', 'volumen_total', 'num_remitos']

        # Gráfico de líneas
        fig_tiempo = px.line(
            df_agrupado,
            x='año_mes',
            y='huella_promedio',
            color='compania',
            markers=True,
            title="Evolución de Huella CO₂ Promedio Mensual",
            labels={
                'año_mes': 'Mes',
                'huella_promedio': 'Huella CO₂ Promedio (kg/m³)'
            }
        )
        st.plotly_chart(fig_tiempo, use_container_width=True)

        # Gráfico de volumen
        fig_vol = px.bar(
            df_agrupado,
            x='año_mes',
            y='volumen_total',
            color='compania',
            title="Volumen Total Despachado por Mes",
            labels={
                'año_mes': 'Mes',
                'volumen_total': 'Volumen Total (m³)'
            }
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    st.divider()

    # Tabla de datos detallados
    with st.expander("📋 Ver datos detallados"):
        st.dataframe(
            df_filtrado[[
                'id_remito', 'compania', 'planta', 'fecha',
                'formulacion', 'resistencia', 'volumen', 'huella_co2'
            ]].head(500),
            use_container_width=True
        )

if __name__ == "__main__":
    app()
