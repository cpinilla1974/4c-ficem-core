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
| `BORRADOR` | En configuración |
| `ACTIVO` | Abierto para submissions |
| `CERRADO` | No acepta nuevos submissions |
| `ARCHIVADO` | Histórico |

---

## API de Submissions

### Endpoints

| Método | Endpoint | Rol requerido | Descripción |
|--------|----------|---------------|-------------|
| POST | `/api/v1/procesos/{proceso_id}/submissions` | INFORMANTE_EMPRESA, SUPERVISOR_EMPRESA | Crear submission |
| GET | `/api/v1/procesos/{proceso_id}/submissions` | Según visibilidad | Listar submissions de un proceso |
| GET | `/api/v1/submissions/{id}` | Según visibilidad | Obtener detalle de submission |
| POST | `/api/v1/submissions/{id}/upload` | INFORMANTE_EMPRESA | Subir archivo Excel |
| POST | `/api/v1/submissions/{id}/validate` | Cualquier autenticado | Validar archivo |
| POST | `/api/v1/submissions/{id}/submit` | INFORMANTE_EMPRESA, SUPERVISOR_EMPRESA | Enviar para revisión |
| POST | `/api/v1/submissions/{id}/aprobar-empresa` | SUPERVISOR_EMPRESA | Aprobar/rechazar a nivel empresa |
| POST | `/api/v1/submissions/{id}/aprobar-ficem` | ROOT, ADMIN_PROCESO | Aprobar/rechazar a nivel FICEM |
| POST | `/api/v1/submissions/{id}/comentarios` | Cualquier autenticado | Agregar comentario |
| GET | `/api/v1/submissions/{id}/results` | Según visibilidad | Obtener resultados (solo si APROBADO_FICEM) |

### Visibilidad de Submissions

| Rol | Qué ve |
|-----|--------|
| ROOT, ADMIN_PROCESO, EJECUTIVO_FICEM | Todos los submissions |
| COORDINADOR_PAIS | Submissions de empresas de su país |
| SUPERVISOR_EMPRESA, INFORMANTE_EMPRESA, VISOR_EMPRESA | Solo submissions de su empresa |

### Flujo de Estados

```
BORRADOR ──────────────────────────────────────┐
    │                                          │
    │ POST /submit                             │
    ▼                                          │
ENVIADO ───────────────────────────────────────┤
    │                                          │
    ├── POST /aprobar-empresa {accion:"rechazar"}
    │       │                                  │
    │       ▼                                  │
    │   RECHAZADO_EMPRESA ─────────────────────┘
    │       (vuelve a BORRADOR para corregir)
    │
    └── POST /aprobar-empresa {accion:"aprobar"}
            │
            ▼
    APROBADO_EMPRESA
            │
            ├── POST /aprobar-ficem {accion:"en_revision"}
            │       │
            │       ▼
            │   EN_REVISION_FICEM
            │       │
            │       ├── {accion:"aprobar"} ──► APROBADO_FICEM
            │       └── {accion:"rechazar"} ─► RECHAZADO_FICEM
            │
            ├── POST /aprobar-ficem {accion:"aprobar"}
            │       │
            │       ▼
            │   APROBADO_FICEM ──► PUBLICADO
            │
            └── POST /aprobar-ficem {accion:"rechazar"}
                    │
                    ▼
                RECHAZADO_FICEM
                    (vuelve a BORRADOR para corregir)
```

### Ejemplos de Uso

#### Crear submission (INFORMANTE_EMPRESA)
```bash
curl -X POST http://localhost:8000/api/v1/procesos/MRV-AR-2024/submissions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"empresa_id": 1, "planta_id": 1}'
```

#### Subir archivo Excel
```bash
curl -X POST http://localhost:8000/api/v1/submissions/{id}/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "archivo=@datos.xlsx"
```

#### Validar archivo
```bash
curl -X POST http://localhost:8000/api/v1/submissions/{id}/validate \
  -H "Authorization: Bearer $TOKEN"
```

#### Enviar para revisión
```bash
curl -X POST http://localhost:8000/api/v1/submissions/{id}/submit \
  -H "Authorization: Bearer $TOKEN"
```

#### Aprobar a nivel empresa (SUPERVISOR_EMPRESA)
```bash
curl -X POST http://localhost:8000/api/v1/submissions/{id}/aprobar-empresa \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"accion": "aprobar", "comentario": "Datos verificados"}'
```

#### Aprobar a nivel FICEM (ROOT, ADMIN_PROCESO)
```bash
curl -X POST http://localhost:8000/api/v1/submissions/{id}/aprobar-ficem \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"accion": "aprobar", "comentario": "Aprobado para cálculos"}'
```

### Request/Response

#### SubmissionCreate (POST /submissions)
```json
{
  "empresa_id": 1,
  "planta_id": 1
}
```

#### SubmissionReviewRequest (POST /aprobar-empresa, /aprobar-ficem)
```json
{
  "accion": "aprobar",      // "aprobar", "rechazar", "en_revision" (solo FICEM)
  "comentario": "Opcional"
}
```

#### SubmissionResponse
```json
{
  "id": "uuid",
  "proceso_id": "MRV-AR-2024",
  "empresa_id": 1,
  "empresa_nombre": "Loma Negra",
  "planta_id": 1,
  "planta_nombre": "Planta Olavarría",
  "estado_actual": "ENVIADO",
  "archivo_excel": {
    "url": "s3://...",
    "filename": "datos.xlsx",
    "uploaded_at": "2024-12-17T10:00:00Z"
  },
  "validaciones": [...],
  "comentarios": [...],
  "workflow_history": [...],
  "submitted_at": "2024-12-17T10:30:00Z",
  "reviewed_at": null,
  "approved_at": null
}
```

---

## Código fuente

- Modelo Usuario: [database/models.py:16-30](database/models.py#L16-L30)
- Estados Submission: [database/models.py:49-59](database/models.py#L49-L59)
- Permisos API: [api/routes/procesos.py](api/routes/procesos.py)
- Schemas: [api/schemas/procesos.py](api/schemas/procesos.py)
- Migración: [scripts/migrate_usuarios_permisos_v2.py](scripts/migrate_usuarios_permisos_v2.py)