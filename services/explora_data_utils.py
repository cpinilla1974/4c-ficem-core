"""
Utilidades para módulo Explora Data
Funciones compartidas entre páginas de exploración de datos
"""
import streamlit as st
import pandas as pd
import io


def descargar_excel(df, nombre_boton='Descargar Excel', nombre_archivo='datos.xlsx'):
    """
    Crea un botón para descargar un DataFrame como archivo Excel

    Args:
        df: DataFrame a descargar
        nombre_boton: Texto del botón de descarga
        nombre_archivo: Nombre sugerido para el archivo
    """
    # Crear un buffer para el archivo Excel
    buffer = io.BytesIO()

    # Crear archivo Excel
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Datos')

    # Preparar el buffer para descarga
    buffer.seek(0)

    # Crear columna para el botón de descarga
    col_download = st.columns(1)[0]
    filename = col_download.text_input(
        f"Nombre del archivo {nombre_boton.replace('Descargar','')} :",
        nombre_archivo
    )

    # Botón de descarga
    st.download_button(
        label=nombre_boton,
        data=buffer,
        file_name=filename,
        mime="application/vnd.ms-excel"
    )


def get_indicadores_dict(conn):
    """
    Obtiene un diccionario de indicadores desde la base de datos

    Args:
        conn: Conexión a la base de datos

    Returns:
        Dict con código_indicador como clave y "nombre (unidad)" como valor
    """
    df_indicadores = pd.read_sql_query("SELECT * FROM indicadores", conn)

    indicadores_dict = {}
    for index, row in df_indicadores.iterrows():
        if not pd.isna(row['nombre_indicador']) and not pd.isna(row['unidad']):
            indicadores_dict[row['codigo_indicador']] = (
                row['nombre_indicador'] + " (" + row['unidad'] + ")"
            )

    return indicadores_dict


def get_entidades_dict(conn):
    """
    Obtiene un diccionario de entidades desde la base de datos

    Args:
        conn: Conexión a la base de datos

    Returns:
        Dict con iso_3 como clave y nombre del país como valor
    """
    df_entidades = pd.read_sql_query("SELECT iso_3, country FROM entidades_m49", conn)
    entidades_dict = dict(zip(df_entidades['iso_3'], df_entidades['country']))
    return entidades_dict


@st.dialog("Seleccionar entidades", width='large')
def select_entidades_dialog():
    """
    Diálogo para seleccionar entidades (países) con filtros por región y subregión
    Guarda la selección en st.session_state.entidades_seleccionadas
    """
    ruta_db = st.session_state['ruta_db']
    from database.connection import get_connection
    conn = get_connection(ruta_db)

    lista_entidades = pd.read_sql_query("SELECT distinct iso_3 FROM tb_cubo", conn)
    lista_entidades = lista_entidades['iso_3'].tolist()
    query_entidades = f"SELECT region_name, sub_region_name, country, iso_3 FROM entidades_m49 WHERE iso_3 IN ({','.join(['?']*len(lista_entidades))})"
    df_entidades = pd.read_sql_query(query_entidades, conn, params=lista_entidades)

    # Obtener entidades actualmente seleccionadas
    entidades_actuales = st.session_state.get('entidades_seleccionadas', [])

    # Obtener valores para preselección si hay entidades guardadas
    regiones_default = []
    subregiones_default = []
    paises_default = []

    if entidades_actuales:
        df_preseleccion = df_entidades[df_entidades['iso_3'].isin(entidades_actuales)]
        regiones_default = df_preseleccion['region_name'].unique().tolist()
        subregiones_default = df_preseleccion['sub_region_name'].unique().tolist()
        paises_default = df_preseleccion['country'].unique().tolist()

    col1, col2, col3 = st.columns([1, 1, 1])
    lista_regiones = df_entidades['region_name'].unique().tolist()
    lista_regiones.sort()
    regiones_seleccionadas = st.multiselect("Seleccionar región", lista_regiones, default=regiones_default)
    if regiones_seleccionadas:
        df_entidades = df_entidades[df_entidades['region_name'].isin(regiones_seleccionadas)]

    lista_subregiones = df_entidades['sub_region_name'].unique().tolist()
    lista_subregiones.sort()
    # Filtrar defaults para que solo incluya subregiones disponibles
    subregiones_default_filtradas = [s for s in subregiones_default if s in lista_subregiones]
    subregiones_seleccionadas = st.multiselect("Seleccionar subregión", lista_subregiones, default=subregiones_default_filtradas)
    if subregiones_seleccionadas:
        df_entidades = df_entidades[df_entidades['sub_region_name'].isin(subregiones_seleccionadas)]

    lista_paises = df_entidades['country'].unique().tolist()
    lista_paises.sort()
    # Filtrar defaults para que solo incluya países disponibles
    paises_default_filtrados = [p for p in paises_default if p in lista_paises]
    paises_seleccionadas = st.multiselect("Seleccionar país", lista_paises, default=paises_default_filtrados)
    if paises_seleccionadas:
        df_entidades = df_entidades[df_entidades['country'].isin(paises_seleccionadas)]

    lista_iso_3 = df_entidades['iso_3'].unique().tolist()

    # Mostrar contador de entidades seleccionadas
    st.info(f"📍 {len(lista_iso_3)} entidades seleccionadas")

    col1, col2 = st.columns(2)
    boton_aplicar = col1.button("✓ Aplicar filtros", type="primary", use_container_width=True)
    boton_limpiar = col2.button("🗑️ Limpiar selección", use_container_width=True)

    if boton_aplicar:
        st.session_state.entidades_seleccionadas = lista_iso_3
        st.rerun()

    if boton_limpiar:
        st.session_state.entidades_seleccionadas = []
        st.rerun()


@st.dialog("Seleccionar indicadores", width='large')
def select_indicadores_dialog(fuentes_selected):
    """
    Diálogo para seleccionar indicadores con filtros jerárquicos
    Guarda la selección en st.session_state.indicadores_seleccionados

    Args:
        fuentes_selected: Lista de fuentes seleccionadas para filtrar indicadores
    """
    from database.connection import get_connection
    from services.indicadores import get_indicadores_dict_completo

    ruta_db = st.session_state['ruta_db']
    conn = get_connection(ruta_db)
    indicadores_dict = get_indicadores_dict_completo()
    indicadores_dict_inv = dict(zip(indicadores_dict.values(), indicadores_dict.keys()))

    # Obtener lista actual de indicadores si existe en session_state
    indicadores_actuales = st.session_state.get('indicadores_seleccionados', [])

    fuentes_selected_sql = f"WHERE fuente IN ({','.join(['?']*len(fuentes_selected))})"
    lista_codigo_indicadores = pd.read_sql_query(
        f"SELECT distinct codigo_indicador FROM tb_cubo {fuentes_selected_sql}",
        conn,
        params=fuentes_selected
    )

    lista_codigo_indicadores = lista_codigo_indicadores['codigo_indicador'].tolist()

    # Filtrar indicadores actuales para asegurar que estén dentro de las fuentes seleccionadas
    indicadores_actuales_filtrados = [ind for ind in indicadores_actuales if ind in lista_codigo_indicadores]

    query_indicadores = f"""
    SELECT
        supergrupo,
        grupo,
        subgrupo,
        nombre_indicador,
        codigo_indicador,
        unidad,
        objeto,
        tipo_objeto
    FROM indicadores
    WHERE codigo_indicador
        IN ({','.join(['?']*len(lista_codigo_indicadores))})"""

    df_indicadores = pd.read_sql_query(query_indicadores, conn, params=lista_codigo_indicadores)
    df_indicadores['supergrupo'] = df_indicadores['supergrupo'].fillna('nada')
    df_indicadores['grupo'] = df_indicadores['grupo'].fillna('nada')
    df_indicadores['subgrupo'] = df_indicadores['subgrupo'].fillna('nada')

    # Obtener valores únicos para los selectores
    lista_supergrupos = df_indicadores['supergrupo'].unique().tolist()
    lista_supergrupos.sort()

    # Si hay indicadores preseleccionados, obtener sus supergrupos
    supergrupos_preseleccionados = []
    if indicadores_actuales_filtrados:
        supergrupos_preseleccionados = df_indicadores[df_indicadores['codigo_indicador'].isin(indicadores_actuales_filtrados)]['supergrupo'].unique().tolist()

    supergrupos_seleccionados = st.multiselect("Seleccionar supergrupos", lista_supergrupos, default=supergrupos_preseleccionados)

    # Filtrar df_indicadores según supergrupos seleccionados
    if supergrupos_seleccionados:
        df_filtrado_supergrupos = df_indicadores[df_indicadores['supergrupo'].isin(supergrupos_seleccionados)]
    else:
        df_filtrado_supergrupos = df_indicadores.copy()

    # Obtener grupos y preseleccionar los que corresponden a indicadores actuales
    lista_grupos = df_filtrado_supergrupos['grupo'].unique().tolist()
    lista_grupos.sort()

    grupos_preseleccionados = []
    if indicadores_actuales_filtrados:
        grupos_preseleccionados = df_indicadores[df_indicadores['codigo_indicador'].isin(indicadores_actuales_filtrados)]['grupo'].unique().tolist()
        # Filtrar por supergrupos seleccionados
        grupos_preseleccionados = [g for g in grupos_preseleccionados if g in lista_grupos]

    grupos_seleccionados = st.multiselect("Seleccionar grupos", lista_grupos, default=grupos_preseleccionados)

    # Filtrar df_indicadores según grupos seleccionados
    if grupos_seleccionados:
        df_filtrado_grupos = df_filtrado_supergrupos[df_filtrado_supergrupos['grupo'].isin(grupos_seleccionados)]
    else:
        df_filtrado_grupos = df_filtrado_supergrupos.copy()

    # Obtener subgrupos y preseleccionar
    lista_subgrupos = df_filtrado_grupos['subgrupo'].unique().tolist()
    lista_subgrupos.sort()

    subgrupos_preseleccionados = []
    if indicadores_actuales_filtrados:
        subgrupos_preseleccionados = df_indicadores[df_indicadores['codigo_indicador'].isin(indicadores_actuales_filtrados)]['subgrupo'].unique().tolist()
        # Filtrar por grupos seleccionados
        subgrupos_preseleccionados = [s for s in subgrupos_preseleccionados if s in lista_subgrupos]

    subgrupos_seleccionados = st.multiselect("Seleccionar subgrupos", lista_subgrupos, default=subgrupos_preseleccionados)

    # Filtrar df_indicadores según subgrupos seleccionados
    if subgrupos_seleccionados:
        df_filtrado_subgrupos = df_filtrado_grupos[df_filtrado_grupos['subgrupo'].isin(subgrupos_seleccionados)]
    else:
        df_filtrado_subgrupos = df_filtrado_grupos.copy()

    # Obtener unidades y preseleccionar
    lista_unidades = df_filtrado_subgrupos['unidad'].unique().tolist()
    lista_unidades.sort()

    unidades_preseleccionadas = []
    if indicadores_actuales_filtrados:
        unidades_preseleccionadas = df_indicadores[df_indicadores['codigo_indicador'].isin(indicadores_actuales_filtrados)]['unidad'].unique().tolist()
        # Filtrar por subgrupos seleccionados
        unidades_preseleccionadas = [u for u in unidades_preseleccionadas if u in lista_unidades]

    unidades_seleccionadas = st.multiselect("Seleccionar unidades", lista_unidades, default=unidades_preseleccionadas)

    # Filtrar df_indicadores según unidades seleccionadas
    if unidades_seleccionadas:
        df_filtrado_unidades = df_filtrado_subgrupos[df_filtrado_subgrupos['unidad'].isin(unidades_seleccionadas)]
    else:
        df_filtrado_unidades = df_filtrado_subgrupos.copy()

    # Obtener indicadores y preseleccionar los que están en la lista actual
    lista_codigos_indicadores = df_filtrado_unidades['codigo_indicador'].unique().tolist()
    lista_indicadores = list(map(indicadores_dict.get, lista_codigos_indicadores))
    lista_indicadores.sort()

    # Preseleccionar indicadores que estén en los filtros actuales y en la lista original
    indicadores_preseleccionados = [ind for ind in indicadores_actuales_filtrados if ind in lista_indicadores]

    # Convertir códigos actuales a nombres para preselección
    nombres_preseleccionados = []
    if indicadores_actuales_filtrados:
        nombres_preseleccionados = [indicadores_dict.get(cod) for cod in indicadores_actuales_filtrados if indicadores_dict.get(cod) in lista_indicadores]

    indicadores_seleccionados = st.multiselect("Seleccionar indicadores", lista_indicadores, default=nombres_preseleccionados)
    indicadores_codigos_seleccionados = [indicadores_dict_inv.get(ind) for ind in indicadores_seleccionados]

    # Filtrar df_indicadores según indicadores seleccionados
    if indicadores_codigos_seleccionados:
        lista_codigo_indicadores = indicadores_codigos_seleccionados
    else:
        lista_codigo_indicadores = df_filtrado_unidades['codigo_indicador'].unique().tolist()

    # Mostrar contador de indicadores seleccionados
    st.info(f"📊 {len(lista_codigo_indicadores)} indicadores seleccionados")

    col1, col2 = st.columns(2)
    boton_aplicar = col1.button("✓ Aplicar filtros", type="primary", use_container_width=True)
    boton_limpiar = col2.button("🗑️ Limpiar selección", use_container_width=True)

    if boton_aplicar:
        st.session_state.indicadores_seleccionados = lista_codigo_indicadores
        st.rerun()

    if boton_limpiar:
        st.session_state.indicadores_seleccionados = []
        st.rerun()
