import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
import io
from database.connection import get_connection
# Función para descfargar un dataframe como un archivo Excel 
def descargar_excel(df, nombre_boton = 'Descargar Excel', nombre_archivo = 'datos.xlsx'):
    
    # Crear un buffer para el archivo Excel
    buffer = io.BytesIO()

    # Crear archivo Excel
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Datos')
        
    # Preparar el buffer para descarga
    buffer.seek(0)

    # Crear columna para el botón de descarga
    col_download = st.columns(1)[0]
    filename = col_download.text_input(f"Nombre del archivo {nombre_boton.replace('Descargar','')} :", nombre_archivo) 
    
    # Botón de descarga
    st.download_button(
        label=nombre_boton,
        data=buffer,
        file_name=filename,
        mime="application/vnd.ms-excel"
    )



def app():
    # Obtener conexión de session_state
    ruta_db = st.session_state.get('ruta_db')
    conn = get_connection(ruta_db)

    st.title("📋 Bandas GCCA Cementos")
    
    
    df = pd.read_sql_query("SELECT * FROM cementos", conn)
    df = df.replace({'origen': {'lomax': 'Compañía 1', 'mzma': 'Compañía 2'}})
    df = df.replace({'planta': {'Apazapan': 'Planta 1',
                                'Cerritos': 'Planta 2',
                                'Tepetzingo': 'Planta 3',
                                'Pacasmayo': 'Planta 4',
                                'Rioja': 'Planta 5',
                                'Piura': 'Planta 6',
                                }})
    st.dataframe(df)
    
        
    # Sidebar para controles
    st.sidebar.header("Parámetros de Clasificación")

    # Widget para ajustar la relación clínker/cemento
    relacion_clinker_cemento = st.sidebar.slider(
        "Relación clínker/cemento",
        min_value=0.30,
        max_value=1.0,
        value=0.706,
        step=0.001,
        format="%.3f",
        help="La relación entre clínker y cemento afecta los rangos de clasificación según GCCA"
    )

    # Función para calcular rangos basados en la relación clínker/cemento
    def calcular_rangos_gcca(CCr):
        """
        Calcula los rangos de clasificación GCCA según la fórmula oficial:
        X_i = (40 + 85 * CCr) * i
        
        Donde:
        - CCr: Relación Clínker/Cemento (Clinker to Cement ratio)
        - i: Índice de clase (1 para A, 2 para B, etc.)
        
        Basado en la metodología oficial GCCA para Global Low Carbon Ratings
        """
        # Implementación de la fórmula: X_i = (40 + 85 * CCr) * i
        # CCr = Clinker to Cement ratio (relación clínker/cemento)
        
        # Calcular los valores límite para cada clase
        rangos = {
            'AA': 0,  # Near Zero - siempre es 0
        }
        
        # Calcular X1 a X7 según la fórmula
        base = 40 + 85 * CCr
        for i in range(1, 8):
            if i == 1:
                rangos['A'] = int(base * i)
            elif i == 2:
                rangos['B'] = int(base * i)
            elif i == 3:
                rangos['C'] = int(base * i)
            elif i == 4:
                rangos['D'] = int(base * i)
            elif i == 5:
                rangos['E'] = int(base * i)
            elif i == 6:
                rangos['F'] = int(base * i)
            elif i == 7:
                rangos['G'] = int(base * i)
        
        return rangos

    # Función para determinar la clasificación basada en GWP
    def clasificar_cemento(gwp, rangos):
        """
        Clasifica un cemento basado en su GWP (kg CO2e/t) utilizando los rangos GCCA
        
        Args:
            gwp: Valor de huella de carbono en kg CO2e/t
            rangos: Diccionario con los límites para cada clase
            
        Returns:
            Clase GCCA (AA-G)
        """
        clases = list(rangos.keys())
        
        # Caso especial para AA (Near Zero)
        if gwp <= rangos['A']:
            return 'AA'
        
        # Para el resto de clases
        for i in range(1, len(clases)-1):  # Excluimos AA y G
            clase_actual = clases[i]
            clase_siguiente = clases[i+1]
            
            if rangos[clase_actual] <= gwp < rangos[clase_siguiente]:
                return clase_actual
        
        # Si es mayor o igual que el límite de F pero menor que G
        if 'G' in rangos and 'F' in rangos:
            if rangos['F'] <= gwp < rangos['G']:
                return 'F'
            elif gwp >= rangos['G']:
                return 'G'
        else:
            # Si no hay clase G, entonces F es la última
            if gwp >= rangos['F']:
                return 'F'
                
        # Por defecto (no debería llegar aquí)
        return 'F'

    # Función para obtener color según clasificación
    def obtener_color_clase(clase):
        """
        Retorna el código de color hexadecimal correspondiente a cada clase GCCA.
        Los colores siguen el esquema oficial del sistema GCCA.
        """
        colores = {
            'AA': '#00A651',  # Verde oscuro
            'A': '#39B54A',   # Verde
            'B': '#8DC63F',   # Verde claro / Cyan
            'C': '#00AEEF',   # Azul claro
            'D': '#0054A6',   # Azul oscuro
            'E': '#A7A9AC',   # Gris claro
            'F': '#6D6E71',   # Gris oscuro
            'G': '#231F20'    # Negro
        }
        return colores.get(clase, '#CCCCCC')

    # Calcular rangos basados en el valor del slider
    rangos = calcular_rangos_gcca(relacion_clinker_cemento)

    # Mostrar los rangos calculados
    st.sidebar.subheader("Rangos de Clasificación (kg CO₂e/t)")
    rangos_df = pd.DataFrame({"Clase": list(rangos.keys()), "Límite (X) kg CO₂e/t": list(rangos.values())})

    # Agregar columna con la descripción de los rangos según la imagen
    rangos_df["Rango de emisiones"] = ""
    for i, clase in enumerate(rangos_df["Clase"]):
        if clase == 'AA':
            rangos_df.loc[i, "Rango de emisiones"] = f"0 - {rangos_df.loc[rangos_df['Clase'] == 'A', 'Límite (X) kg CO₂e/t'].values[0]}"
        elif clase == 'G':
            rangos_df.loc[i, "Rango de emisiones"] = f">{rangos_df.loc[i, 'Límite (X) kg CO₂e/t']}"
        else:
            next_clase_idx = "ABCDEFG".index(clase) + 1
            next_clase = "ABCDEFG"[next_clase_idx] if next_clase_idx < len("ABCDEFG") else None
            if next_clase and next_clase in rangos_df["Clase"].values:
                rangos_df.loc[i, "Rango de emisiones"] = f"{rangos_df.loc[i, 'Límite (X) kg CO₂e/t']} - {rangos_df.loc[rangos_df['Clase'] == next_clase, 'Límite (X) kg CO₂e/t'].values[0]}"

    # Mostrar fórmula utilizada
    st.sidebar.markdown("**Fórmula utilizada:**")
    st.sidebar.latex(r"X_i = (40 + 85 \times CCr) \times i")
    st.sidebar.markdown(f"Donde CCr = {relacion_clinker_cemento} (Relación Clínker/Cemento)")

    st.sidebar.table(rangos_df[["Clase", "Límite (X) kg CO₂e/t", "Rango de emisiones"]])

    # Clasificar cada cemento
    df['clase_gcca'] = df['huella_co2_bruta'].apply(lambda x: clasificar_cemento(x, rangos))
    df['color_clase'] = df['clase_gcca'].apply(obtener_color_clase)

    # Mostrar dataframe con clasificaciones
    st.subheader("Datos con Clasificación GCCA")
    st.dataframe(df[['origen', 'planta', 'cemento', 'año', 'huella_co2_bruta', 'clase_gcca']])

    # Dividir la pantalla en columnas para los gráficos
    col1, col2 = st.columns(2)

    # Gráfico 1: Distribución de emisiones por clase GCCA
    with col1:
        st.subheader("Distribución de Emisiones por Clase GCCA")
        
        # Crear un gráfico de barras horizontales con clasificación de colores
        fig = go.Figure()
        
        # Ordenar por huella de CO2
        df_sorted = df.sort_values('huella_co2_bruta')
        
        # Añadir líneas para los límites de clasificación
        for clase, limite in rangos.items():
            if clase != 'AA':  # No dibujar línea para AA que es 0
                fig.add_shape(
                    type="line",
                    x0=limite,
                    y0=-0.5,
                    x1=limite,
                    y1=len(df_sorted) - 0.5,
                    line=dict(color="gray", width=1, dash="dash"),
                )
                fig.add_annotation(
                    x=limite,
                    y=len(df_sorted),
                    text=clase,
                    showarrow=False,
                    yshift=10,
                )
        
        # Añadir barras para cada planta
        fig.add_trace(go.Bar(
            x=df_sorted['huella_co2_bruta'],
            y=df_sorted['planta'],
            orientation='h',
            marker_color=df_sorted['color_clase'],
            text=df_sorted['clase_gcca'],
            hovertemplate="<b>%{y}</b><br>Emisiones: %{x} kg CO₂e/t<br>Clase: %{text}<extra></extra>",
        ))
        
        fig.update_layout(
            xaxis_title="Emisiones (kg CO₂e/t)",
            yaxis_title="Planta",
            height=500,
            margin=dict(l=20, r=20, t=30, b=20),
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # Gráfico 2: Gráfico de dispersión por origen y tipo de cemento
    with col2:
        st.subheader("Emisiones por Origen y Tipo de Cemento")
        
        fig = px.scatter(
            df, 
            x="cemento", 
            y="huella_co2_bruta",
            color="clase_gcca",
            size="huella_co2_bruta",
            hover_name="planta",
            color_discrete_map={clase: obtener_color_clase(clase) for clase in df['clase_gcca'].unique()},
            labels={
                "huella_co2_bruta": "Emisiones (kg CO₂e/t)",
                "cemento": "Tipo de Cemento",
                "clase_gcca": "Clase GCCA"
            },
        )
        
        # Añadir líneas horizontales para los límites de clasificación
        for clase, limite in rangos.items():
            if clase != 'AA':  # No dibujar línea para AA que es 0
                fig.add_shape(
                    type="line",
                    x0=-0.5,
                    y0=limite,
                    x1=len(df['cemento'].unique()) - 0.5,
                    y1=limite,
                    line=dict(color="gray", width=1, dash="dash"),
                )
                fig.add_annotation(
                    x=len(df['cemento'].unique()) - 0.5,
                    y=limite,
                    text=clase,
                    showarrow=False,
                    xshift=15,
                )
        
        fig.update_layout(
            height=500,
            margin=dict(l=20, r=20, t=30, b=20),
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # Gráfico 3: Mapa de calor de emisiones por origen y tipo de cemento
    st.subheader("Mapa de Calor: Emisiones por Origen y Tipo de Cemento")

    # Preparar pivot table para el mapa de calor
    pivot_df = df.pivot_table(
        values='huella_co2_bruta',
        index='origen',
        columns='cemento',
        aggfunc='mean'
    )

    # Crear una función para aplicar colores basados en las clases GCCA
    def get_custom_cmap():
        colors = [obtener_color_clase(clase) for clase in ['AA', 'A', 'B', 'C', 'D', 'E', 'F']]
        return LinearSegmentedColormap.from_list('gcca_colors', colors, N=256)

    custom_cmap = get_custom_cmap()

    # Crear el mapa de calor con anotaciones
    fig, ax = plt.subplots(figsize=(12, 7))
    heatmap = sns.heatmap(
        pivot_df,
        annot=True,
        fmt=".0f",
        cmap=custom_cmap,
        linewidths=.5,
        ax=ax,
        vmin=rangos['AA'],
        vmax=rangos['F'],
        cbar_kws={'label': 'Emisiones (kg CO₂e/t)'}
    )

    # Añadir líneas y etiquetas para los rangos en la barra de color
    cbar = ax.collections[0].colorbar
    for clase, limite in rangos.items():
        if clase != 'AA':  # No marcar AA que siempre es 0
            cbar.ax.axhline(y=(limite - rangos['AA']) / (rangos['F'] - rangos['AA']), color='black', linewidth=1)
            cbar.ax.text(
                1.5, 
                (limite - rangos['AA']) / (rangos['F'] - rangos['AA']), 
                clase, 
                ha='center', 
                va='center', 
                color='black',
                fontweight='bold'
            )

    plt.title('Emisiones Promedio por Origen y Tipo de Cemento')
    plt.tight_layout()

    st.pyplot(fig)

    # Gráfico 4: Indicador de distribución por clases
    st.subheader("Distribución de Productos por Clase GCCA")

    clase_counts = df['clase_gcca'].value_counts().reset_index()
    clase_counts.columns = ['Clase GCCA', 'Cantidad']

    # Aseguramos que todas las clases estén representadas
    todas_clases = pd.Series(['AA', 'A', 'B', 'C', 'D', 'E', 'F'])
    clase_counts = pd.DataFrame({
        'Clase GCCA': todas_clases,
        'Cantidad': [clase_counts.loc[clase_counts['Clase GCCA'] == c, 'Cantidad'].sum() if c in clase_counts['Clase GCCA'].values else 0 for c in todas_clases]
    })

    # Añadir columna de color
    clase_counts['Color'] = clase_counts['Clase GCCA'].apply(obtener_color_clase)

    # Crear un gráfico de donut para mostrar la distribución
    fig = px.pie(
        clase_counts,
        values='Cantidad',
        names='Clase GCCA',
        title='Distribución de Productos por Clase GCCA',
        color='Clase GCCA',
        color_discrete_map={row['Clase GCCA']: row['Color'] for _, row in clase_counts.iterrows()},
        hole=0.4,
    )

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>"
    )

    fig.update_layout(
        height=500,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Filtrado interactivo
    st.subheader("Filtrado Interactivo")

    col1, col2, col3 = st.columns(3)

    with col1:
        origen_seleccionado = st.multiselect(
            "Filtrar por Origen",
            options=df['origen'].unique(),
            default=df['origen'].unique()
        )

    with col2:
        cemento_seleccionado = st.multiselect(
            "Filtrar por Tipo de Cemento",
            options=df['cemento'].unique(),
            default=df['cemento'].unique()
        )

    with col3:
        clase_seleccionada = st.multiselect(
            "Filtrar por Clase GCCA",
            options=['AA', 'A', 'B', 'C', 'D', 'E', 'F'],
            default=['AA', 'A', 'B', 'C', 'D', 'E', 'F']
        )

    # Aplicar filtros
    df_filtrado = df[
        df['origen'].isin(origen_seleccionado) &
        df['cemento'].isin(cemento_seleccionado) &
        df['clase_gcca'].isin(clase_seleccionada)
    ]

    # Mostrar resultados filtrados
    if not df_filtrado.empty:
        st.dataframe(df_filtrado)
        
        # Estadísticas del filtrado
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Emisiones Promedio",
                f"{df_filtrado['huella_co2_bruta'].mean():.1f} kg CO₂e/t",
                delta=f"{df_filtrado['huella_co2_bruta'].mean() - df['huella_co2_bruta'].mean():.1f}",
                delta_color="inverse"
            )
        
        with col2:
            clase_mas_comun = df_filtrado['clase_gcca'].mode()[0]
            st.metric(
                "Clase GCCA más común",
                clase_mas_comun,
            )
        
        with col3:
            st.metric(
                "Cantidad de Productos",
                df_filtrado.shape[0],
                delta=f"{df_filtrado.shape[0] - df.shape[0]}"
            )
    else:
        st.warning("No hay datos que cumplan con los criterios de filtrado seleccionados.")

    # Descargar datos clasificados
    st.download_button(
        label="Descargar Datos Clasificados (CSV)",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="datos_cemento_clasificados.csv",
        mime="text/csv",
    )

    descargar_excel(df, 'Descargar datos clasificados', 'datos_cemento_clasificados.xlsx')


    # Información adicional
    st.markdown("""
    ---
    ### Información sobre el Sistema GCCA Global Ratings

    El sistema GCCA Global Low Carbon Ratings clasifica los productos de cemento según su Potencial de Calentamiento Global (GWP), 
    medido en CO₂e por tonelada de cemento (kg CO₂e/t).

    #### Fórmula para el cálculo de los límites:
    La fórmula oficial para calcular los valores de los límites (X) es:

    **X₁ = (40 + 85 × CCr) × i**

    Donde:
    - CCr: Relación Clínker/Cemento que elige cada país (p.ej. Alemania eligió 0.706)
    - i: Índice de clase (1 para A, 2 para B, etc.)

    #### Sistema de clasificación:
    - **AA (Near Zero)**: 0 - X₁ kg CO₂e/t
    - **A**: X₁ - X₂ kg CO₂e/t
    - **B**: X₂ - X₃ kg CO₂e/t
    - **C**: X₃ - X₄ kg CO₂e/t
    - **D**: X₄ - X₅ kg CO₂e/t
    - **E**: X₅ - X₆ kg CO₂e/t
    - **F**: X₆ - X₇ kg CO₂e/t
    - **G**: >X₇ kg CO₂e/t

    La metodología utiliza estándares EPD reconocidos internacionalmente:
    - Estándares: EN 15804+A2, PCR-001 - Cemento y cal para construcción (EN 16908)
    - Base de datos: ecoinvent
    - Alcance: de la cuna a la puerta (A1-A3)

    Para más información, visite [GCCA Global Ratings for Cement](https://gccassociation.org/lcr-cement/)
    """)