import streamlit as st
import pandas as pd
import io
from database.connection import get_connection, get_connection_indicadores
from services.indicadores import get_indicadores_dict_completo


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
    




def get_indicadores_dict(conn):
    df_indicadores = pd.read_sql_query("SELECT * FROM indicadores", conn)
    
    indicadores_dict = {}
    for index, row in df_indicadores.iterrows():
        if not pd.isna(row['nombre_indicador']) and not pd.isna(row['unidad']): 
            indicadores_dict[row['codigo_indicador']] = row['nombre_indicador'] + " (" + row['unidad'] + ")"
    
    return indicadores_dict


@st.dialog("Seleccionar entidades", width='large')
def select_entidades_dialog():
    
    ruta_db = st.session_state['ruta_db']
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
        
    

# Función obsoleta - mantener por compatibilidad pero no usar
def select_entidades(conn, df):
    return df
        



@st.dialog("Seleccionar indicadores", width='large')
def select_indicadores_dialog(fuentes_selected):
    # conn_aux = get_connection_indicadores()
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

        

# Función obsoleta - mantener por compatibilidad pero no usar
def select_indicadores(conn, df_cubo):
    return df_cubo
     
     
# Funciones obsoletas - mantener por compatibilidad pero no usar
def select_fuente(conn, df):
    return df

def select_años(conn, df):
    return df

def get_entidades_dict(conn):
    df_entidades = pd.read_sql_query("SELECT iso_3, country FROM entidades_m49", conn)
    entidades_dict = dict(zip(df_entidades['iso_3'], df_entidades['country']))
    return entidades_dict


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
    
    
