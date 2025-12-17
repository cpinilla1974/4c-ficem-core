# Usuarios y Permisos - 4C FICEM CORE

> Esquema definitivo. Aprobado 2025-12-10. Actualizado con valores MAYÚSCULAS.

## Roles

| # | Rol | Valor BD | Quién es | Qué puede ver | Qué puede hacer |
|---|-----|----------|----------|---------------|-----------------|
| 1 | Root | `ROOT` | Superadmin FICEM | Todo | Todo |
| 2 | Admin Proceso | `ADMIN_PROCESO` | Staff FICEM | Todo | Gestionar procesos, aprobar submissions |
| 3 | Ejecutivo FICEM | `EJECUTIVO_FICEM` | Directivo FICEM | Todo | Solo ver |
| 4 | Amigo FICEM | `AMIGO_FICEM` | Académico, consultor | Público + Amigos FICEM | Solo ver + API |
| 5 | Coordinador País | `COORDINADOR_PAIS` | Asociación nacional | Todo de su país | Solo ver + enviar recordatorios |
| 6 | Supervisor Empresa | `SUPERVISOR_EMPRESA` | Jefe en empresa | Su empresa + Amigos FICEM | Aprobar antes de enviar |
| 7 | Informante Empresa | `INFORMANTE_EMPRESA` | Empleado empresa | Su empresa + Amigos FICEM | Cargar datos |
| 8 | Visor Empresa | `VISOR_EMPRESA` | Empleado empresa | Su empresa + Amigos FICEM | Solo ver |

---

## Niveles de Visibilidad de Datos

| Nivel | Quién puede ver |
|-------|-----------------|
| Público | Todos |
| Amigos FICEM | Amigos + Empresas + Coordinadores + FICEM |
| País | Coordinador de ese país + FICEM |
| Empresa | Solo esa empresa + FICEM |
| FICEM | Solo Root, Admin Proceso, Ejecutivo FICEM |

---

## Flujo de Aprobación

```
Informante carga datos
       ↓
    [ENVIADO]
       ↓
Supervisor Empresa aprueba
       ↓
 [APROBADO_EMPRESA]
       ↓
Admin Proceso FICEM aprueba
       ↓
  [APROBADO_FICEM]

Coordinador País observa todo el flujo (no aprueba)
```

### Estados de Submission

| Estado | Descripción |
|--------|-------------|
| `BORRADOR` | Informante trabajando |
| `ENVIADO` | Informante envió a supervisor |
| `APROBADO_EMPRESA` | Supervisor empresa aprobó |
| `EN_REVISION_FICEM` | Admin FICEM revisando |
| `APROBADO_FICEM` | Admin FICEM aprobó (final) |
| `RECHAZADO_EMPRESA` | Supervisor rechazó |
| `RECHAZADO_FICEM` | Admin FICEM rechazó |
| `PUBLICADO` | Visible públicamente |
| `ARCHIVADO` | Histórico |

---

## Proceso MRV

Cada proceso tiene un Admin Proceso asignado como responsable (`coordinador_ficem_id`).

---

## Migración

### Ejecutar migración

```bash
cd /home/cpinilla/projects/4c-ficem-core
source venv/bin/activate
python scripts/migrate_usuarios_permisos_v2.py
```

### Ver estado actual

```bash
python scripts/migrate_usuarios_permisos_v2.py --status
```

### Rollback (si es necesario)

```bash
python scripts/migrate_usuarios_permisos_v2.py --rollback
```

### Mapeo de roles (migración automática)

| Rol anterior | Rol nuevo |
|--------------|-----------|
| `empresa` | `INFORMANTE_EMPRESA` |
| `operador_ficem` | `ADMIN_PROCESO` |
| `admin` | `ROOT` |
| `coordinador_pais` | `COORDINADOR_PAIS` |

### Mapeo de estados (migración automática)

| Estado anterior | Estado nuevo |
|-----------------|--------------|
| `aprobado` | `APROBADO_FICEM` |
| `rechazado` | `RECHAZADO_FICEM` |
| `en_revision` | `EN_REVISION_FICEM` |

---

## API de Procesos

### Endpoints

| Método | Endpoint | Rol requerido | Descripción |
|--------|----------|---------------|-------------|
| GET | `/api/v1/procesos` | Cualquier usuario autenticado | Listar procesos |
| GET | `/api/v1/procesos/{id}` | Cualquier usuario autenticado | Obtener proceso |
| POST | `/api/v1/procesos` | ROOT, ADMIN_PROCESO | Crear proceso |
| PUT | `/api/v1/procesos/{id}` | ROOT, ADMIN_PROCESO | Actualizar proceso |
| PATCH | `/api/v1/procesos/{id}/estado` | ROOT, ADMIN_PROCESO | Cambiar estado |
| DELETE | `/api/v1/procesos/{id}` | ROOT | Eliminar proceso |

### Estados de Proceso

| Estado | Descripción |
|--------|-------------|
| `borrador` | En configuración |
| `activo` | Abierto para submissions |
| `cerrado` | No acepta nuevos submissions |
| `archivado` | Histórico |

---

## Código fuente

- Modelo Usuario: [database/models.py:16-30](database/models.py#L16-L30)
- Estados Submission: [database/models.py:49-59](database/models.py#L49-L59)
- Permisos API: [api/routes/procesos.py](api/routes/procesos.py)
- Schemas: [api/schemas/procesos.py](api/schemas/procesos.py)
- Migración: [scripts/migrate_usuarios_permisos_v2.py](scripts/migrate_usuarios_permisos_v2.py)