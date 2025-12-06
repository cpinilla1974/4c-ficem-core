# streamlit/services/indicadores.py
import sqlite3
import json
import pandas as pd
import streamlit as st
from collections import defaultdict
import re
import os
import os.path
from dotenv import load_dotenv
from database.connection import get_connection_indicadores

load_dotenv()


def get_indicadores_dict_completo():
    conn = get_connection_indicadores()
    query = "SELECT codigo_indicador, nombre_indicador, unidad FROM indicadores"
    df = pd.read_sql_query(query, conn)
    # No necesitamos cerrar el engine de SQLAlchemy
    indicadores_dict = {}
    for index, row in df.iterrows():
        if not  pd.isna(row['unidad']):
            indicadores_dict[row['codigo_indicador']] = row['nombre_indicador'] + " (" + row['unidad'] + ")"

    return indicadores_dict


def get_indicadores_totales():
    estructura_indicadores = get_indicadores_json()
    indicadores_dict = {}
    for supergrupo_nombre, supergrupo in estructura_indicadores["supergrupos"].items():
        for grupo_nombre, grupo in supergrupo["grupos"].items():
            for indicador in grupo["indicadores"]:
                codigo_indicador = indicador.get('codigo_indicador', 'Sin codigo')
                nombre_indicador = indicador.get('nombre_indicador', 'Sin nombre')
                unidad = indicador.get('unidad', 'Sin unidad')
                indicador_str = f"{nombre_indicador} ({unidad})"
                # st.write(indicador_str)
                indicadores_dict[codigo_indicador] = indicador_str
    
    return indicadores_dict



def cargar_indicadores():
    # Inicializar la estructura si no existe
    if 'estructura_indicadores' not in st.session_state:
        st.session_state.estructura_indicadores = None
    
    # Obtener rutas desde variables de entorno y configuración del proyecto
    json_path = os.getenv("INDICADORES_JSON_PATH")
    
    # st.subheader("Cargar desde JSON")
    # st.text(f"Archivo JSON origen: {json_path}")
    try:
        # Verificar si el archivo existe
        if not os.path.exists(json_path):
            st.warning(f"El archivo {json_path} no existe. Primero debes exportar los indicadores.")
        else:
            st.session_state.estructura_indicadores = leer_indicadores_estructurados(json_path)
            # if st.session_state.estructura_indicadores:
            #     st.success(f"✅ {st.session_state.estructura_indicadores['metadata']['total_indicadores']} indicadores cargados")
                
    except Exception as e:
        st.error(f"❌ Error durante la importación: {e}")    

def get_indicadores_json():
    json_path = os.getenv("INDICADORES_JSON_PATH")
    try:
        if not os.path.exists(json_path):
            st.warning(f"El archivo {json_path} no existe. Primero debes exportar los indicadores.")
            return None
        else:
            estructura_indicadores = leer_indicadores_estructurados(json_path)
            return estructura_indicadores
            
    except Exception as e:
        st.error(f"❌ Error durante la importación: {e}")    
        return None



# Función para exportar la tabla a JSON con estructura jerárquica
def exportar_indicadores_estructurados(db_path, json_path):
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    
    # Consultar todos los indicadores
    query = "SELECT * FROM indicadores"
    df = pd.read_sql_query(query, conn)

    # Crear estructura jerárquica
    estructura = {
        "metadata": {
            "total_indicadores": len(df),
            "ultimo_codigo": "",
            "codigos_usados": [],
            "fecha_generacion": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "supergrupos": {}
    }
    
    # Recopilar todos los códigos para control
    todos_codigos = df['codigo_indicador'].tolist()
    estructura["metadata"]["codigos_usados"] = todos_codigos
    
    # Determinar el último código (asumiendo formato como IND-001, IND-002, etc.)
    # Extraer números y encontrar el máximo
    numeros_codigos = []
    for codigo in todos_codigos:
        if isinstance(codigo, str):
            matches = re.findall(r'\d+', codigo)
            if matches:
                numeros_codigos.extend([int(match) for match in matches])
    
    if numeros_codigos:
        estructura["metadata"]["ultimo_codigo"] = max(numeros_codigos)
    
    # Organizar por supergrupo y grupo
    for _, row in df.iterrows():
        supergrupo = row['nombre_supergrupo']
        grupo = row['nombre_grupo']
        
        # Convertir fila a diccionario
        indicador_dict = row.to_dict()
        
        # Crear supergrupo si no existe
        if supergrupo not in estructura["supergrupos"]:
            estructura["supergrupos"][supergrupo] = {
                "nombre": supergrupo,
                "grupos": {}
            }
        
        # Crear grupo si no existe
        if grupo not in estructura["supergrupos"][supergrupo]["grupos"]:
            estructura["supergrupos"][supergrupo]["grupos"][grupo] = {
                "nombre": grupo,
                "id_grupo": indicador_dict.get('id_grupo'),
                "indicadores": []
            }
        
        # Añadir indicador al grupo
        estructura["supergrupos"][supergrupo]["grupos"][grupo]["indicadores"].append(indicador_dict)
    
    # Guardar como JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(estructura, f, ensure_ascii=False, indent=4)
    
    return len(df), estructura["metadata"]["ultimo_codigo"]

# Función para leer el archivo JSON estructurado
def leer_indicadores_estructurados(json_path):
    try:
        if not os.path.exists(json_path):
            return None
            
        with open(json_path, 'r', encoding='utf-8') as f:
            estructura = json.load(f)
        return estructura
    except Exception as e:
        st.error(f"Error al leer el archivo JSON: {e}")
        return None

# Función para obtener un listado plano de todos los indicadores
def obtener_indicadores_planos(estructura):
    indicadores = []
    
    for supergrupo_nombre, supergrupo in estructura["supergrupos"].items():
        for grupo_nombre, grupo in supergrupo["grupos"].items():
            for indicador in grupo["indicadores"]:
                indicadores.append(indicador)
    
    return indicadores

# Función para generar un nuevo código único de indicador
def generar_codigo_indicador(estructura, prefijo=""):
    ultimo_numero = estructura["metadata"]["ultimo_codigo"]
    nuevo_numero = int(ultimo_numero) + 1
    # nuevo_codigo = f"{prefijo}{nuevo_numero:03d}"
    nuevo_codigo = f"{nuevo_numero:03d}"
    # Verifica que no exista ya
    while nuevo_codigo in estructura["metadata"]["codigos_usados"]:
        nuevo_numero += 1
        nuevo_codigo = f"{nuevo_numero:03d}"
    
    return nuevo_codigo

# Función para añadir un nuevo indicador
def agregar_indicador(estructura, indicador_nuevo):

    supergrupo = indicador_nuevo['nombre_supergrupo']
    grupo = indicador_nuevo['nombre_grupo']
    
    # Generar código único si no tiene
    if not indicador_nuevo.get('codigo_indicador'):
        indicador_nuevo['codigo_indicador'] = generar_codigo_indicador(estructura)
    
    # Actualizar metadatos
    estructura["metadata"]["total_indicadores"] += 1
    estructura["metadata"]["codigos_usados"].append(indicador_nuevo['codigo_indicador'])
    
    # Actualizar último código si aplica
    matches = re.findall(r'\d+', indicador_nuevo['codigo_indicador'])
    if matches:
        num_codigo = int(matches[0])
        if num_codigo > int(estructura["metadata"]["ultimo_codigo"]):
            estructura["metadata"]["ultimo_codigo"] = num_codigo
    
    # Crear supergrupo si no existe
    if supergrupo not in estructura["supergrupos"]:
        estructura["supergrupos"][supergrupo] = {
            "nombre": supergrupo,
            "grupos": {}
        }
    
    # Crear grupo si no existe
    if grupo not in estructura["supergrupos"][supergrupo]["grupos"]:
        estructura["supergrupos"][supergrupo]["grupos"][grupo] = {
            "nombre": grupo,
            "id_grupo": indicador_nuevo.get('id_grupo', 0),
            "indicadores": []
        }
    
    # Añadir indicador al grupo
    estructura["supergrupos"][supergrupo]["grupos"][grupo]["indicadores"].append(indicador_nuevo)
    
    return estructura

# Función para guardar la estructura actualizada
def guardar_estructura(estructura, json_path):
    # Actualizar fecha de generación
    estructura["metadata"]["fecha_generacion"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Guardar como JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(estructura, f, ensure_ascii=False, indent=4)


# Componente de Streamlit para gestionar indicadores
def mostrar_gestor_indicadores():
    st.header("Gestor de Indicadores")
    
    # Inicializar la estructura si no existe
    if 'estructura_indicadores' not in st.session_state:
        st.session_state.estructura_indicadores = None
    
    # Obtener rutas desde variables de entorno y configuración del proyecto
    json_path = os.getenv("INDICADORES_JSON_PATH")
    
    st.subheader("Cargar desde JSON")
    st.text(f"Archivo JSON origen: {json_path}")
    
    if st.button("Cargar Indicadores"):
        try:
            # Verificar si el archivo existe
            if not os.path.exists(json_path):
                st.warning(f"El archivo {json_path} no existe. Primero debes exportar los indicadores.")
            else:
                st.session_state.estructura_indicadores = leer_indicadores_estructurados(json_path)
                if st.session_state.estructura_indicadores:
                    st.success(f"✅ {st.session_state.estructura_indicadores['metadata']['total_indicadores']} indicadores cargados")
                    st.rerun()
        except Exception as e:
            st.error(f"❌ Error durante la importación: {e}")
    
        
    # Si hay datos cargados
    if hasattr(st.session_state, 'estructura_indicadores') and st.session_state.estructura_indicadores is not None:
        estructura = st.session_state.estructura_indicadores
        
        # Sección de exploración
        with st.expander("Explorar Indicadores", expanded=True):
            # Selector de supergrupo
            supergrupos = list(estructura["supergrupos"].keys())
            col1, col2, col3 = st.columns([1, 1, 1])
            supergrupo_seleccionado = col1.selectbox("Seleccionar Supergrupo", supergrupos)
            
            if supergrupo_seleccionado:
                # Selector de grupo
                grupos = list(estructura["supergrupos"][supergrupo_seleccionado]["grupos"].keys())
                grupo_seleccionado = col2.selectbox("Seleccionar Grupo", grupos)
                
                if grupo_seleccionado:
                    # Mostrar indicadores del grupo
                    indicadores = estructura["supergrupos"][supergrupo_seleccionado]["grupos"][grupo_seleccionado]["indicadores"]
                    df_indicadores = pd.DataFrame(indicadores)
                    
                    unidades = list(set(df_indicadores['unidad'].unique()))
                    unidad_seleccionada = col3.selectbox("Seleccionar Unidad", unidades)
                    
                    if unidad_seleccionada:
                        df_indicadores = df_indicadores[df_indicadores['unidad'] == unidad_seleccionada]
                    
                    
                    colu1, colu2 = st.columns([4, 1])
                    # Mostrar tabla de indicadores
                    st.write(f"Número de indicadores: {len(df_indicadores)}")
                    # colu1.dataframe(df_indicadores, width = 1000, hide_index=True)
                    colu1.dataframe(df_indicadores[['nombre_indicador',
                                                    'codigo_indicador',
                                                    'nombre_objeto_principal',
                                                    'tipo_objeto_principal',
                                                    'nombre_objeto_secundario',
                                                    'tipo_objeto_secundario']])
                

                    with colu2:
                        nombre_indicador = st.text_input("Nombre del Indicador")
                        nombre_objeto_principal = st.text_input("Nombre Objeto Principal")
                        tipo_objeto_principal = st.text_input("Tipo Objeto Principal")
                        nombre_objeto_secundario = st.text_input("Nombre Objeto Secundario")
                        tipo_objeto_secundario = st.text_input("Tipo Objeto Secundario")
                        nuevo_indicador = {
                            "nombre_supergrupo": supergrupo_seleccionado,
                            "nombre_grupo": grupo_seleccionado,
                            "nombre_indicador": nombre_indicador,
                            "codigo_indicador": "",  # Se generará automáticamente
                            "unidad": unidad_seleccionada,
                            "nombre_objeto_principal": nombre_objeto_principal, 
                            "tipo_objeto_principal": tipo_objeto_principal,
                            "nombre_objeto_secundario": nombre_objeto_secundario,
                            "tipo_objeto_secundario": tipo_objeto_secundario,
                            "creador": "app_streamlit",
                            "id_grupo": estructura["supergrupos"].get(supergrupo_seleccionado, {}).get("grupos", {}).get(grupo_seleccionado, {}).get("id_grupo", 0),
                            "orden": 0,
                            "alcance": ""
                        }
                        boton_guardar_indicador = st.button("Guardar indicador")
                        if boton_guardar_indicador:
                            # Añadir a la estructura
                            estructura = agregar_indicador(estructura, nuevo_indicador)
                    
                            # Guardar en session_state
                            st.session_state.estructura_indicadores = estructura
                    
                            st.success(f"✅ Indicador añadido con código: {nuevo_indicador['codigo_indicador']}")




        # Sección para añadir nuevo indicador
        with st.expander("Añadir Nuevo Indicador"):
            with st.form("nuevo_indicador"):
                st.subheader("Datos del Nuevo Indicador")
                
                # Supergrupo (existente o nuevo)
                nuevo_supergrupo = st.text_input("Nombre del Supergrupo")
                
                # Grupo (existente o nuevo)
                nuevo_grupo = st.text_input("Nombre del Grupo")
                
                # Datos del indicador
                nuevo_nombre = st.text_input("Nombre del Indicador")
                nueva_unidad = st.text_input("Unidad")
                nuevo_alcance = st.text_input("Alcance")
                
                # Otros campos
                nuevo_objeto_principal = st.text_input("Nombre Objeto Principal", "")
                nuevo_tipo_objeto_principal = st.text_input("Tipo Objeto Principal", "")
                
                submitted = st.form_submit_button("Añadir Indicador")
                
                if submitted and nuevo_supergrupo and nuevo_grupo and nuevo_nombre:
                    # Crear nuevo indicador
                    nuevo_indicador = {
                        "nombre_supergrupo": nuevo_supergrupo,
                        "nombre_grupo": nuevo_grupo,
                        "nombre_indicador": nuevo_nombre,
                        "codigo_indicador": "",  # Se generará automáticamente
                        "unidad": nueva_unidad,
                        "nombre_objeto_principal": nuevo_objeto_principal,
                        "tipo_objeto_principal": nuevo_tipo_objeto_principal,
                        "nombre_objeto_secundario": "",
                        "tipo_objeto_secundario": "",
                        "creador": "app_streamlit",
                        "id_grupo": estructura["supergrupos"].get(nuevo_supergrupo, {}).get("grupos", {}).get(nuevo_grupo, {}).get("id_grupo", 0),
                        "orden": 0,
                        "alcance": nuevo_alcance
                    }
                    
                    # Añadir a la estructura
                    estructura = agregar_indicador(estructura, nuevo_indicador)
                    
                    # Guardar en session_state
                    st.session_state.estructura_indicadores = estructura
                    
                    st.success(f"✅ Indicador añadido con código: {nuevo_indicador['codigo_indicador']}")
        
        # Sección para guardar cambios
        if st.button("Guardar Cambios al JSON"):
            try:
                # INDICADORES_JSON_PATH="C:/Users/cpini/PROD/FILE_DATABASE/comun/indicadores.json"
                json_path = os.path.join(os.environ.get('INDICADORES_JSON_PATH', './files/indicadores.json'))
                
                guardar_estructura(estructura, json_path)
                st.success(f"✅ Cambios guardados exitosamente en {json_path}")
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")

