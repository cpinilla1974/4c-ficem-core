"""
Aplicación Streamlit para Administración FICEM CORE
Gestión de usuarios y monitoreo de procesos MRV
"""
import streamlit as st
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Admin FICEM CORE",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session():
    """Inicializar variables de sesión"""
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'user' not in st.session_state:
        st.session_state.user = None


def login_form():
    """Formulario de login"""
    st.title("🔐 Login - Admin FICEM CORE")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="usuario@ejemplo.com")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar Sesión")

        if submit:
            try:
                response = requests.post(
                    f"{API_URL}/api/v1/auth/login",
                    json={"email": email, "password": password}
                )

                if response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data["access_token"]

                    # Obtener datos del usuario
                    user_response = requests.get(
                        f"{API_URL}/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )

                    if user_response.status_code == 200:
                        st.session_state.user = user_response.json()
                        st.success(f"Bienvenido {st.session_state.user['nombre']}")
                        st.rerun()
                else:
                    st.error("Credenciales incorrectas")
            except Exception as e:
                st.error(f"Error de conexión: {str(e)}")


def logout():
    """Cerrar sesión"""
    st.session_state.token = None
    st.session_state.user = None
    st.rerun()


def get_headers():
    """Obtener headers con token JWT"""
    return {"Authorization": f"Bearer {st.session_state.token}"}


def main_app():
    """Aplicación principal después del login"""

    # Sidebar
    with st.sidebar:
        st.title("⚙️ Admin FICEM CORE")
        st.write(f"**Usuario:** {st.session_state.user['nombre']}")
        st.write(f"**Rol:** {st.session_state.user['rol']}")
        st.write(f"**País:** {st.session_state.user['pais']}")

        st.divider()

        menu = st.radio(
            "Menú",
            ["📊 Dashboard", "👥 Usuarios", "🔄 Procesos MRV", "📤 Submissions"]
        )

        st.divider()

        if st.button("🚪 Cerrar Sesión"):
            logout()

    # Contenido principal según menú
    if menu == "📊 Dashboard":
        show_dashboard()
    elif menu == "👥 Usuarios":
        show_usuarios()
    elif menu == "🔄 Procesos MRV":
        show_procesos()
    elif menu == "📤 Submissions":
        show_submissions()


def show_dashboard():
    """Dashboard principal con estadísticas"""
    st.title("📊 Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Usuarios", "N/A", help="Próximamente")

    with col2:
        st.metric("Procesos Activos", "N/A", help="Próximamente")

    with col3:
        st.metric("Submissions Pendientes", "N/A", help="Próximamente")

    st.divider()

    st.info("Dashboard en desarrollo. Próximamente se agregarán estadísticas en tiempo real.")


def show_usuarios():
    """Gestión de usuarios"""
    st.title("👥 Gestión de Usuarios")

    tab1, tab2 = st.tabs(["Lista de Usuarios", "Crear Usuario"])

    with tab1:
        st.subheader("Usuarios Registrados")

        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            filter_pais = st.selectbox(
                "Filtrar por país",
                ["Todos", "PERU", "COLOMBIA", "CHILE", "MEXICO"],
                key="filter_pais_usuarios"
            )

        with col2:
            filter_rol = st.selectbox(
                "Filtrar por rol",
                ["Todos", "ROOT", "ADMIN_PROCESO", "COORDINADOR_PAIS", "SUPERVISOR_EMPRESA"],
                key="filter_rol_usuarios"
            )

        if st.button("🔄 Cargar Usuarios"):
            try:
                # Construir query params
                params = {}
                if filter_pais != "Todos":
                    params["pais"] = filter_pais
                if filter_rol != "Todos":
                    params["rol"] = filter_rol

                response = requests.get(
                    f"{API_URL}/api/v1/usuarios",
                    headers=get_headers(),
                    params=params
                )

                if response.status_code == 200:
                    usuarios = response.json()

                    if len(usuarios) == 0:
                        st.warning("No se encontraron usuarios con los filtros aplicados")
                    else:
                        # Formatear datos para tabla
                        data = {
                            "ID": [u["id"] for u in usuarios],
                            "Email": [u["email"] for u in usuarios],
                            "Nombre": [u["nombre"] for u in usuarios],
                            "Rol": [u["rol"] for u in usuarios],
                            "País": [u["pais"] for u in usuarios],
                            "Activo": ["✅" if u["activo"] else "❌" for u in usuarios]
                        }

                        st.dataframe(data, use_container_width=True)
                        st.caption(f"Total: {len(usuarios)} usuario(s)")
                elif response.status_code == 403:
                    st.error("No tiene permisos para ver usuarios")
                else:
                    st.error(f"Error al cargar usuarios: {response.status_code}")
            except Exception as e:
                st.error(f"Error de conexión: {str(e)}")

    with tab2:
        st.subheader("Crear Nuevo Usuario")

        with st.form("create_user_form"):
            email = st.text_input("Email *")
            nombre = st.text_input("Nombre completo *")

            col1, col2 = st.columns(2)
            with col1:
                rol = st.selectbox(
                    "Rol *",
                    ["ROOT", "ADMIN_PROCESO", "EJECUTIVO_FICEM", "COORDINADOR_PAIS",
                     "SUPERVISOR_EMPRESA", "INFORMANTE_EMPRESA", "VISOR_EMPRESA"]
                )

            with col2:
                pais = st.selectbox(
                    "País *",
                    ["LATAM", "PERU", "COLOMBIA", "CHILE", "MEXICO", "ARGENTINA"]
                )

            password = st.text_input("Contraseña temporal *", type="password")

            submit = st.form_submit_button("✅ Crear Usuario")

            if submit:
                if email and nombre and password:
                    try:
                        response = requests.post(
                            f"{API_URL}/api/v1/usuarios",
                            headers=get_headers(),
                            json={
                                "email": email,
                                "nombre": nombre,
                                "password": password,
                                "rol": rol,
                                "pais": pais,
                                "activo": True
                            }
                        )

                        if response.status_code == 201:
                            st.success(f"✅ Usuario {nombre} creado exitosamente")
                            st.info(f"Email: {email}\nContraseña temporal: {password}")
                        elif response.status_code == 400:
                            error = response.json()
                            st.error(f"Error: {error.get('detail', 'Error desconocido')}")
                        elif response.status_code == 403:
                            st.error("No tiene permisos para crear usuarios")
                        else:
                            st.error(f"Error al crear usuario: {response.status_code}")
                    except Exception as e:
                        st.error(f"Error de conexión: {str(e)}")
                else:
                    st.error("Por favor complete todos los campos obligatorios")


def show_procesos():
    """Gestión de procesos MRV"""
    st.title("🔄 Procesos MRV")

    tab1, tab2 = st.tabs(["Procesos Activos", "Crear Proceso"])

    with tab1:
        st.subheader("Procesos MRV Configurados")

        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_pais = st.selectbox(
                "País",
                ["Todos", "PE", "CO", "CL", "MX"],
                key="filter_pais_procesos"
            )

        with col2:
            filter_tipo = st.selectbox(
                "Tipo",
                ["Todos", "PRODUCE", "MRV_HR", "4C_NACIONAL"],
                key="filter_tipo_procesos"
            )

        with col3:
            filter_estado = st.selectbox(
                "Estado",
                ["Todos", "ACTIVO", "BORRADOR", "CERRADO"],
                key="filter_estado_procesos"
            )

        if st.button("🔄 Cargar Procesos"):
            st.info("Endpoint /procesos pendiente de implementar en la API")

            # Placeholder de datos
            st.dataframe({
                "ID": ["produce-peru-2024", "mrv-colombia-2024"],
                "País": ["PE", "CO"],
                "Tipo": ["PRODUCE", "MRV_HR"],
                "Nombre": ["PRODUCE Perú 2024", "MRV Colombia 2024"],
                "Estado": ["ACTIVO", "ACTIVO"],
                "Ciclo": ["2024", "2024"]
            })

    with tab2:
        st.subheader("Crear Nuevo Proceso MRV")

        with st.form("create_proceso_form"):
            proceso_id = st.text_input(
                "ID del proceso *",
                placeholder="produce-peru-2025",
                help="Formato: tipo-pais-año"
            )

            col1, col2 = st.columns(2)
            with col1:
                pais_iso = st.selectbox(
                    "País *",
                    ["PE", "CO", "CL", "MX", "AR"]
                )

            with col2:
                tipo = st.selectbox(
                    "Tipo de proceso *",
                    ["PRODUCE", "MRV_HR", "4C_NACIONAL", "OTRO"]
                )

            nombre = st.text_input("Nombre del proceso *")
            descripcion = st.text_area("Descripción")
            ciclo = st.text_input("Ciclo *", placeholder="2025")

            st.subheader("Configuración")

            template_version = st.text_input(
                "Versión de template",
                placeholder="produce_peru_v2.1.xlsx"
            )

            deadline_envio = st.date_input("Deadline envío")
            deadline_revision = st.date_input("Deadline revisión")

            submit = st.form_submit_button("✅ Crear Proceso")

            if submit:
                if proceso_id and nombre and ciclo:
                    st.info("Endpoint /procesos POST pendiente de implementar en la API")
                    st.success(f"Proceso {proceso_id} creado exitosamente (simulado)")
                else:
                    st.error("Por favor complete todos los campos obligatorios")


def show_submissions():
    """Monitoreo de submissions"""
    st.title("📤 Submissions")

    st.subheader("Envíos Recientes")

    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_proceso = st.selectbox(
            "Proceso",
            ["Todos", "produce-peru-2024", "mrv-colombia-2024"],
            key="filter_proceso_submissions"
        )

    with col2:
        filter_estado = st.selectbox(
            "Estado",
            ["Todos", "BORRADOR", "ENVIADO", "EN_REVISION_FICEM", "APROBADO_FICEM"],
            key="filter_estado_submissions"
        )

    with col3:
        filter_empresa = st.text_input("Empresa", key="filter_empresa_submissions")

    if st.button("🔄 Cargar Submissions"):
        st.info("Endpoint /submissions pendiente de implementar en la API")

        # Placeholder de datos
        st.dataframe({
            "ID": ["abc-123", "def-456"],
            "Proceso": ["produce-peru-2024", "produce-peru-2024"],
            "Empresa": ["Cementos Lima", "Cementos Pacasmayo"],
            "Estado": ["EN_REVISION_FICEM", "APROBADO_FICEM"],
            "Creado": ["2024-11-15", "2024-11-10"],
            "Última actualización": ["2024-11-20", "2024-11-18"]
        })

    st.divider()

    st.info("""
    **Próximamente:**
    - Detalle de cada submission
    - Descarga de archivos Excel
    - Revisión y aprobación inline
    - Historial de cambios de estado
    - Comentarios y observaciones
    """)


def main():
    """Función principal"""
    init_session()

    if st.session_state.token is None:
        login_form()
    else:
        main_app()


if __name__ == "__main__":
    main()