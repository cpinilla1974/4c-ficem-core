"""
Módulo de conexión a base de datos
Adaptado para usar PostgreSQL con SQLAlchemy
"""
import streamlit as st
from database.models import get_engine


def get_connection(ruta_db=None):
    """
    Obtiene el engine de PostgreSQL compatible con pandas

    Args:
        ruta_db: Parámetro legacy, ignorado (se mantiene por compatibilidad)

    Returns:
        Engine de SQLAlchemy que pandas puede usar directamente
    """
    # Retornar engine directamente - pandas lo acepta sin warnings
    return get_engine()


def get_connection_from_session():
    """
    Obtiene conexión desde session_state de Streamlit
    """
    # Usar la misma lógica que get_connection
    return get_connection()


def get_connection_indicadores():
    """
    Conexión a base de datos de indicadores
    En PostgreSQL todo está en la misma BD
    """
    return get_connection()
