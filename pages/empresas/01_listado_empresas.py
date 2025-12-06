"""
Empresas - Listado
"""
import streamlit as st
from database.repository import EmpresaRepository

st.set_page_config(page_title="Empresas", page_icon="🏭", layout="wide")

st.title("🏭 Listado de Empresas")
st.markdown("---")

st.header("Empresas registradas en el sistema")

# Obtener empresas desde BD
repo = EmpresaRepository(st.session_state.db_engine)
empresas = repo.get_all()

if empresas:
    st.success(f"Total de empresas: {len(empresas)}")

    # Mostrar tabla
    import pandas as pd

    df = pd.DataFrame([{
        'ID': e.id,
        'Nombre': e.nombre,
        'País': e.pais,
        'Perfil Planta': e.perfil_planta,
        'Contacto': e.contacto or '-',
        'Email': e.email or '-'
    } for e in empresas])

    st.dataframe(df, use_container_width=True)

else:
    st.warning("No hay empresas registradas")

st.markdown("""
---
**Funcionalidades futuras:**
- Búsqueda y filtros
- Ordenamiento por columnas
- Exportación a Excel/CSV
- Acciones rápidas (editar, eliminar)
""")
