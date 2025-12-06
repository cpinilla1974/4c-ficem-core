import streamlit as st
import pandas as pd
from database.connection import get_connection
from services.explora_data_utils import (
    descargar_excel,
    get_indicadores_dict,
    get_entidades_dict,
    select_entidades_dialog,
    select_indicadores_dialog
)


def app():
    # Obtener conexión de session_state
    ruta_db = st.session_state.get('ruta_db')
    conn = get_connection(ruta_db)


    if 'entidades_seleccionadas' not in st.session_state:
        st.session_state.entidades_seleccionadas = []

    if 'indicadores_seleccionados' not in st.session_state:
        st.session_state.indicadores_seleccionados = []

    entidades_dict = get_entidades_dict(conn)
    entidades_dict_inv = dict(zip(entidades_dict.values(), entidades_dict.keys()))
    indicadores_dict = get_indicadores_dict(conn)
    indicadores_dict_inv = dict(zip(indicadores_dict.values(), indicadores_dict.keys()))

    st.title('Explora Data')

    st.write(f"---")

    df_cubo = pd.read_sql_query("SELECT * FROM tb_cubo", conn)



    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    # Filtrar por fuente - Simple multiselect
    lista_fuentes = pd.read_sql_query("SELECT distinct fuente FROM tb_cubo", conn)
    lista_fuentes = lista_fuentes['fuente'].tolist()
    fuentes_selected = col1.multiselect("📂 Fuente", lista_fuentes)
    if fuentes_selected:
        df_cubo = df_cubo[df_cubo['fuente'].isin(fuentes_selected)]
    else:
        fuentes_selected = lista_fuentes  # Para el diálogo de indicadores

    # Filtrar por indicadores - Solo botón con diálogo
    with col2:
        st.write("📊 Indicadores")
        indicadores_count = len(st.session_state.indicadores_seleccionados)
        if indicadores_count > 0:
            st.caption(f"{indicadores_count} seleccionados")
        if st.button("🔍 Seleccionar", use_container_width=True, key='btn_indicadores'):
            select_indicadores_dialog(fuentes_selected)

    # Aplicar filtro de indicadores si hay selección
    if st.session_state.indicadores_seleccionados:
        df_cubo = df_cubo[df_cubo['codigo_indicador'].isin(st.session_state.indicadores_seleccionados)]

    # Filtrar por años - Simple multiselect
    lista_años = df_cubo['año'].unique().tolist()
    lista_años.sort()
    años_selected = col3.multiselect("📅 Años", lista_años)
    if años_selected:
        df_cubo = df_cubo[df_cubo['año'].isin(años_selected)]

    # Filtrar por entidades - Solo botón con diálogo
    with col4:
        st.write("🌍 Entidades")
        entidades_count = len(st.session_state.entidades_seleccionadas)
        if entidades_count > 0:
            st.caption(f"{entidades_count} seleccionadas")
        if st.button("🔍 Seleccionar", use_container_width=True, key='btn_entidades'):
            select_entidades_dialog()

    # Aplicar filtro de entidades si hay selección
    if st.session_state.entidades_seleccionadas:
        df_cubo = df_cubo[df_cubo['iso_3'].isin(st.session_state.entidades_seleccionadas)]


    st.write(f"---")

    df_cubo['indicador'] = df_cubo['codigo_indicador'].map(indicadores_dict)
    df_cubo['entidad'] = df_cubo['iso_3'].map(entidades_dict)

    df_pivot = df_cubo.pivot_table(
        index=["fuente", "entidad", "indicador"],
        columns=["año"],
        values="valor",
        aggfunc=sum
    )

    # st.dataframe(df_cubo, use_container_width=True)
    st.dataframe(df_pivot, use_container_width=True)


    def create_suggested_filename(fuentes_selected, indicadores_count, años_selected, entidades_count):
        parts = []
        if fuentes_selected:
            parts.append(f"{fuentes_selected[0][:3]}")
        if indicadores_count > 0:
            parts.append(f"{indicadores_count}ind")
        if años_selected:
            parts.append(f"{min(años_selected)}-{max(años_selected)}")
        if entidades_count > 0:
            parts.append(f"{entidades_count}ent")

        base_name = '_'.join(parts) if parts else "datos"
        return f"{base_name}.xlsx"


            # Sugerir nombre de archivo basado en filtros
    suggested_filename = create_suggested_filename(
            fuentes_selected,
            len(st.session_state.indicadores_seleccionados),
            años_selected,
            len(st.session_state.entidades_seleccionadas)
        )

    col1, col2 = st.columns([1, 1])


    descargar_excel(df_pivot, 'Descargar datos seleccionados',  suggested_filename)


# Run the app
app()
