"""
Sistema centralizado de permisos por rol
"""
from database.models import UserRole

# Matriz de permisos: acción -> roles permitidos
# "*" significa todos los usuarios autenticados
PERMISOS = {
    # === Procesos MRV ===
    "procesos.listar": ["*"],
    "procesos.ver": ["*"],
    "procesos.crear": ["ROOT", "ADMIN_PROCESO"],
    "procesos.editar": ["ROOT", "ADMIN_PROCESO"],
    "procesos.cambiar_estado": ["ROOT", "ADMIN_PROCESO"],
    "procesos.eliminar": ["ROOT"],

    # === Submissions ===
    "submissions.listar": ["*"],
    "submissions.ver_propios": ["*"],
    "submissions.ver_empresa": ["SUPERVISOR_EMPRESA", "INFORMANTE_EMPRESA", "VISOR_EMPRESA"],
    "submissions.ver_pais": ["COORDINADOR_PAIS"],
    "submissions.ver_todos": ["ROOT", "ADMIN_PROCESO", "EJECUTIVO_FICEM"],
    "submissions.crear": ["INFORMANTE_EMPRESA", "SUPERVISOR_EMPRESA"],
    "submissions.editar": ["INFORMANTE_EMPRESA"],
    "submissions.enviar": ["INFORMANTE_EMPRESA", "SUPERVISOR_EMPRESA"],
    "submissions.aprobar_empresa": ["SUPERVISOR_EMPRESA"],
    "submissions.rechazar_empresa": ["SUPERVISOR_EMPRESA"],
    "submissions.aprobar_ficem": ["ROOT", "ADMIN_PROCESO"],
    "submissions.rechazar_ficem": ["ROOT", "ADMIN_PROCESO"],

    # === Usuarios ===
    "usuarios.listar": ["ROOT", "ADMIN_PROCESO", "COORDINADOR_PAIS"],
    "usuarios.listar_pais": ["COORDINADOR_PAIS"],
    "usuarios.ver": ["ROOT", "ADMIN_PROCESO"],
    "usuarios.crear": ["ROOT", "ADMIN_PROCESO"],
    "usuarios.editar": ["ROOT", "ADMIN_PROCESO"],
    "usuarios.desactivar": ["ROOT", "ADMIN_PROCESO"],

    # === Empresas ===
    "empresas.listar": ["*"],
    "empresas.ver": ["*"],
    "empresas.crear": ["ROOT", "ADMIN_PROCESO", "COORDINADOR_PAIS"],
    "empresas.editar": ["ROOT", "ADMIN_PROCESO"],

    # === Dashboard ===
    "dashboard.ver": ["*"],
    "dashboard.estadisticas_globales": ["ROOT", "ADMIN_PROCESO", "EJECUTIVO_FICEM"],
    "dashboard.estadisticas_pais": ["COORDINADOR_PAIS"],
}


def tiene_permiso(usuario, accion: str) -> bool:
    """
    Verifica si un usuario tiene permiso para realizar una acción.

    Args:
        usuario: Objeto Usuario con atributo 'rol'
        accion: String de la acción (ej: "procesos.crear")

    Returns:
        bool: True si tiene permiso
    """
    # ROOT siempre tiene todos los permisos
    if usuario.rol.value == "ROOT":
        return True

    roles_permitidos = PERMISOS.get(accion, [])

    if not roles_permitidos:
        return False

    if "*" in roles_permitidos:
        return True

    return usuario.rol.value in roles_permitidos


def requiere_permiso(accion: str):
    """
    Decorador para verificar permisos en endpoints.
    Uso: @requiere_permiso("procesos.crear")
    """
    from functools import wraps
    from fastapi import HTTPException, status

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=None, **kwargs):
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No autenticado"
                )

            if not tiene_permiso(current_user, accion):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"No tiene permiso para: {accion}"
                )

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


# Mapeo de estados de submission a rol responsable
TAREA_POR_ESTADO = {
    "BORRADOR": "INFORMANTE_EMPRESA",
    "ENVIADO": "SUPERVISOR_EMPRESA",
    "APROBADO_EMPRESA": "ADMIN_PROCESO",
    "EN_REVISION_FICEM": "ADMIN_PROCESO",
    "RECHAZADO_EMPRESA": "INFORMANTE_EMPRESA",
    "RECHAZADO_FICEM": "INFORMANTE_EMPRESA",
}


def obtener_tareas_pendientes(usuario, db) -> list:
    """
    Obtiene las tareas pendientes para un usuario según su rol.

    Returns:
        Lista de diccionarios con tipo de tarea y cantidad
    """
    from database.models import Submission, EstadoSubmission

    tareas = []
    rol = usuario.rol.value

    if rol == "INFORMANTE_EMPRESA":
        # Submissions en borrador o rechazados de su empresa
        borrador = db.query(Submission).filter(
            Submission.empresa_id == usuario.empresa_id,
            Submission.estado_actual == EstadoSubmission.BORRADOR
        ).count()

        rechazados = db.query(Submission).filter(
            Submission.empresa_id == usuario.empresa_id,
            Submission.estado_actual.in_([
                EstadoSubmission.RECHAZADO_EMPRESA,
                EstadoSubmission.RECHAZADO_FICEM
            ])
        ).count()

        if borrador:
            tareas.append({"tipo": "completar_envio", "cantidad": borrador, "accion": "Completar y enviar"})
        if rechazados:
            tareas.append({"tipo": "corregir_rechazado", "cantidad": rechazados, "accion": "Corregir y reenviar"})

    elif rol == "SUPERVISOR_EMPRESA":
        # Submissions esperando aprobación de su empresa
        pendientes = db.query(Submission).filter(
            Submission.empresa_id == usuario.empresa_id,
            Submission.estado_actual == EstadoSubmission.ENVIADO
        ).count()

        if pendientes:
            tareas.append({"tipo": "aprobar_envio", "cantidad": pendientes, "accion": "Revisar y aprobar"})

    elif rol in ["ROOT", "ADMIN_PROCESO"]:
        # Submissions esperando aprobación FICEM
        pendientes = db.query(Submission).filter(
            Submission.estado_actual == EstadoSubmission.APROBADO_EMPRESA
        ).count()

        en_revision = db.query(Submission).filter(
            Submission.estado_actual == EstadoSubmission.EN_REVISION_FICEM
        ).count()

        if pendientes:
            tareas.append({"tipo": "revisar_submission", "cantidad": pendientes, "accion": "Iniciar revisión"})
        if en_revision:
            tareas.append({"tipo": "finalizar_revision", "cantidad": en_revision, "accion": "Finalizar revisión"})

    elif rol == "COORDINADOR_PAIS":
        # Submissions de su país en cualquier estado activo
        from database.models import Empresa

        activos = db.query(Submission).join(Empresa).filter(
            Empresa.pais == usuario.pais,
            Submission.estado_actual.notin_([
                EstadoSubmission.APROBADO_FICEM,
                EstadoSubmission.PUBLICADO,
                EstadoSubmission.ARCHIVADO
            ])
        ).count()

        if activos:
            tareas.append({"tipo": "monitorear_pais", "cantidad": activos, "accion": "Monitorear progreso"})

    return tareas