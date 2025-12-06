import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from database.connection import get_connection

def app():
    # Obtener conexión de session_state
    ruta_db = st.session_state.get('ruta_db')
    conn = get_connection(ruta_db)

    st.title("📋 Plantas de cemento")
    
    # Cargar datos
    df_plantas = pd.read_sql_query("SELECT * FROM plantas_latam", conn)
    
    # Información general
    st.write(f"**Número total de plantas:** {len(df_plantas)}")
    
    # Crear columnas para la interfaz
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Filtros")
        
        # Selectores
        paises = ["Todos"] + sorted(df_plantas["pais"].unique().tolist())
        pais_seleccionado = st.selectbox("País", paises)
        
        tipos_planta = ["Todos"] + sorted(df_plantas["tipo_planta_cemento"].unique().tolist())
        tipo_seleccionado = st.selectbox("Tipo de planta", tipos_planta)
        
        grupos = ["Todos"] + sorted(df_plantas["grupo"].unique().tolist())
        grupo_seleccionado = st.selectbox("Grupo empresarial", grupos)
        
        # Aplicar filtros
        df_filtrado = df_plantas.copy()
        
        if pais_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["pais"] == pais_seleccionado]
            
        if tipo_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["tipo_planta_cemento"] == tipo_seleccionado]
            
        if grupo_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["grupo"] == grupo_seleccionado]
        
        st.write(f"**Plantas filtradas:** {len(df_filtrado)}")
        
        # Mostrar capacidad total instalada
        if not df_filtrado.empty and "capacidad_instalada" in df_filtrado.columns:
            capacidad_total = df_filtrado["capacidad_instalada"].sum()
            st.metric("Capacidad instalada total (Mt/año)", f"{capacidad_total:,.2f}")
    
    with col2:
        st.subheader("Mapa de plantas")
        
        # Verificar si hay datos filtrados
        if df_filtrado.empty:
            st.warning("No hay plantas que coincidan con los filtros seleccionados.")
        else:
            # Crear mapa con PyDeck
            view_state = pdk.ViewState(
                latitude=df_filtrado["lat"].mean(),
                longitude=df_filtrado["lon"].mean(),
                zoom=3,
                pitch=0
            )
            
            # Crear capa de puntos con tamaño basado en capacidad
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df_filtrado,
                get_position=["lon", "lat"],
                get_radius=["capacidad_instalada * 100"] if "capacidad_instalada" in df_filtrado.columns else 2000,
                get_fill_color=[255, 140, 0, 140],  # Color naranja semi-transparente
                pickable=True,
                auto_highlight=True
            )
            
            # Crear tooltip para mostrar información al pasar el mouse
            tooltip = {
                "html": "<b>{planta}</b><br>"
                        "Compañía: {compania}<br>"
                        "Grupo: {grupo}<br>"
                        "Tipo: {tipo_planta_cemento}<br>"
                        "Capacidad: {capacidad_instalada} Mt/año",
                "style": {"backgroundColor": "steelblue", "color": "white"}
            }
            
            # Renderizar mapa
            st.pydeck_chart(pdk.Deck(
                map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                initial_view_state=view_state,
                layers=[layer],
                tooltip=tooltip
            ))
    
    # Visualizaciones adicionales
    st.subheader("Análisis de datos")
    
    # Pestañas para diferentes visualizaciones
    tab1, tab2, tab3 = st.tabs(["Capacidad por país", "Distribución por tipo", "Top empresas"])
    
    with tab1:
        if not df_filtrado.empty and "capacidad_instalada" in df_filtrado.columns:
            # Agrupar por país y sumar capacidad
            df_por_pais = df_filtrado.groupby("pais")["capacidad_instalada"].sum().reset_index()
            df_por_pais = df_por_pais.sort_values("capacidad_instalada", ascending=False)
            
            # Crear gráfico de barras
            fig = px.bar(
                df_por_pais,
                x="pais",
                y="capacidad_instalada",
                title="Capacidad instalada por país (Mt/año)",
                labels={"capacidad_instalada": "Capacidad (Mt/año)", "pais": "País"},
                color="capacidad_instalada",
                color_continuous_scale=px.colors.sequential.Oranges
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        if not df_filtrado.empty and "tipo_planta_cemento" in df_filtrado.columns:
            # Contar tipos de planta
            df_por_tipo = df_filtrado["tipo_planta_cemento"].value_counts().reset_index()
            df_por_tipo.columns = ["tipo_planta_cemento", "count"]
            
            # Crear gráfico de torta
            fig = px.pie(
                df_por_tipo,
                values="count",
                names="tipo_planta_cemento",
                title="Distribución por tipo de planta",
                hole=0.4,  # Donut chart
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        if not df_filtrado.empty:
            # Selector para el tipo de visualización
            metrica_seleccionada = st.radio(
                "Seleccione métrica para visualizar:",
                ["Número de plantas", "Capacidad instalada (Mt/año)"],
                horizontal=True
            )
            
            if metrica_seleccionada == "Número de plantas":
                # Top 10 empresas por cantidad de plantas
                df_por_empresa = df_filtrado["compania"].value_counts().reset_index()
                df_por_empresa.columns = ["compania", "count"]
                df_por_empresa = df_por_empresa.head(10)
                
                # Crear gráfico de barras horizontales
                fig = px.bar(
                    df_por_empresa,
                    y="compania",
                    x="count",
                    title="Top 10 empresas por número de plantas",
                    labels={"count": "Número de plantas", "compania": "Compañía"},
                    orientation="h",
                    color="count",
                    color_continuous_scale=px.colors.sequential.Blues
                )
            else:
                # Top 10 empresas por capacidad instalada
                df_por_empresa_cap = df_filtrado.groupby("compania")["capacidad_instalada"].sum().reset_index()
                df_por_empresa_cap = df_por_empresa_cap.sort_values("capacidad_instalada", ascending=False).head(10)
                
                # Crear gráfico de barras horizontales
                fig = px.bar(
                    df_por_empresa_cap,
                    y="compania",
                    x="capacidad_instalada",
                    title="Top 10 empresas por capacidad instalada",
                    labels={"capacidad_instalada": "Capacidad instalada (Mt/año)", "compania": "Compañía"},
                    orientation="h",
                    color="capacidad_instalada",
                    color_continuous_scale=px.colors.sequential.Oranges
                )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de datos
    with st.expander("Ver datos detallados"):
        st.dataframe(
            df_filtrado,
            column_config={
                "planta": "Planta",
                "codigo_planta": "Código",
                "tipo_planta_cemento": "Tipo",
                "capacidad_instalada": st.column_config.NumberColumn("Capacidad (Mt/año)", format="%.2f"),
                "pais": "País",
                "ciudad": "Ciudad",
                "compania": "Compañía",
                "grupo": "Grupo"
            },
            hide_index=True
        )


# Run the app
app()
