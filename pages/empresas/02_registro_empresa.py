"""
Empresas - Registro Nueva Empresa
"""
import streamlit as st

st.set_page_config(page_title="Registro Empresa", page_icon="🏭", layout="wide")

st.title("🏭 Registro Nueva Empresa")
st.markdown("---")

st.header("Formulario de registro")

st.markdown("""
**Funcionalidad:** Formulario para registrar nuevas empresas cementeras/concreteras

Campos:
- Nombre de la empresa
- País
- Perfil de planta (integrada/molienda/concreto)
- Contacto principal
- Email
- Teléfono
- Dirección

_Contenido en desarrollo_
""")

with st.form("registro_empresa"):
    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Nombre de la Empresa *")
        st.selectbox("País *", ["Colombia", "Perú", "Chile", "México", "Argentina"])
        st.selectbox("Perfil Planta *", ["Integrada", "Molienda", "Concreto"])

    with col2:
        st.text_input("Contacto Principal")
        st.text_input("Email")
        st.text_input("Teléfono")

    submitted = st.form_submit_button("Registrar Empresa")

    if submitted:
        st.info("Funcionalidad en desarrollo")
