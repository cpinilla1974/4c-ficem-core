import streamlit as st
import pandas as pd
import io
from services.explora_data_utils import descargar_excel
from database.connection import get_connection


def app():
    # Obtener conexión de session_state
    ruta_db = st.session_state.get('ruta_db')
    conn = get_connection(ruta_db)

    st.title("📋 Cubo Completo")

    boton_cargar_cubo_completo = st.button("Preparar 'Cubo Completo' para descarga")
    if boton_cargar_cubo_completo:
        df_cubo = pd.read_sql_query("SELECT * FROM cubo_expandido", conn)
        df_cubo = df_cubo[df_cubo['codigo_indicador'].notnull()]
        st.write(f"Número de filas: {df_cubo.shape[0]}")
        st.dataframe(df_cubo, use_container_width=True)
        descargar_excel(df_cubo, 'Descargar cubo completo',  'cubo_completo.xlsx')


# Run the app
app()