"""
Repositorio de acceso a datos
"""
from .models import Empresa, get_session, get_engine


class EmpresaRepository:
    """Repositorio para operaciones CRUD de empresas"""

    def __init__(self, engine):
        self.engine = engine

    def get_all(self):
        """Obtener todas las empresas"""
        session = get_session(self.engine)
        try:
            return session.query(Empresa).all()
        finally:
            session.close()

    def get_by_id(self, empresa_id):
        """Obtener empresa por ID"""
        session = get_session(self.engine)
        try:
            return session.query(Empresa).filter(Empresa.id == empresa_id).first()
        finally:
            session.close()

    def create(self, nombre, pais, perfil_planta, contacto=None, email=None):
        """Crear nueva empresa"""
        session = get_session(self.engine)
        try:
            empresa = Empresa(
                nombre=nombre,
                pais=pais,
                perfil_planta=perfil_planta,
                contacto=contacto,
                email=email
            )
            session.add(empresa)
            session.commit()
            session.refresh(empresa)
            return empresa
        finally:
            session.close()

    def count(self):
        """Contar total de empresas"""
        session = get_session(self.engine)
        try:
            return session.query(Empresa).count()
        finally:
            session.close()
