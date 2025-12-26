# Implementación Motor de Procesos MRV Multi-País

**Fecha**: 2025-12-10
**Estado**: ✅ Completado (Fase 1: Infraestructura)

---

## Resumen

Se implementó el **Motor de Procesos MRV configurable** que permite a cada país tener múltiples protocolos (PRODUCE, MRV HR, 4C nacional) sin cambios de código.

---

## Archivos Creados/Modificados

### 1. Base de Datos

#### Migración
- **`scripts/migrate_procesos_mrv.py`**: Script de migración para crear tablas
  - Tabla `procesos_mrv`: Registry de procesos configurables
  - Tabla `submissions`: Envíos dentro de procesos
  - Índices optimizados (7 índices en total)
  - Soporte para rollback

**Ejecutar migración**:
```bash
python scripts/migrate_procesos_mrv.py
```

#### Modelos SQLAlchemy
- **`database/models.py`**: Agregados modelos `ProcesoMRV` y `Submission`
  - Nuevos Enums: `EstadoProceso`, `EstadoSubmission`, `TipoProceso`
  - Relaciones: proceso ← submissions
  - Campos JSONB para configuración flexible

---

### 2. API REST (FastAPI)

#### Esquemas Pydantic
- **`api/schemas/procesos.py`**: 20+ esquemas para validación
  - `ProcesoCreate`, `ProcesoResponse`, `ProcesoList`
  - `SubmissionCreate`, `SubmissionResponse`, `SubmissionList`
  - `SubmissionValidateResponse`, `SubmissionReviewRequest`
  - Schemas para comentarios, validaciones, workflow

#### Endpoints - Procesos
- **`api/routes/procesos.py`**: 7 endpoints
  - `GET /api/v1/procesos` - Listar procesos (filtros: país, estado, tipo)
  - `GET /api/v1/procesos/{id}` - Detalle de proceso
  - `POST /api/v1/procesos` - Crear proceso (admin FICEM)
  - `PUT /api/v1/procesos/{id}` - Actualizar proceso
  - `PATCH /api/v1/procesos/{id}/estado` - Cambiar estado
  - `DELETE /api/v1/procesos/{id}` - Eliminar proceso
  - `GET /api/v1/procesos/{id}/template` - Descargar template (TODO)

#### Endpoints - Submissions
- **`api/routes/submissions.py`**: 9 endpoints
  - `POST /api/v1/procesos/{id}/submissions` - Crear submission
  - `GET /api/v1/procesos/{id}/submissions` - Listar submissions
  - `GET /api/v1/submissions/{id}` - Detalle submission
  - `POST /api/v1/submissions/{id}/upload` - Subir Excel (TODO: storage real)
  - `POST /api/v1/submissions/{id}/validate` - Validar datos (TODO: validaciones reales)
  - `POST /api/v1/submissions/{id}/submit` - Enviar para revisión
  - `POST /api/v1/submissions/{id}/review` - Aprobar/rechazar (coordinador)
  - `POST /api/v1/submissions/{id}/comentarios` - Agregar comentario
  - `GET /api/v1/submissions/{id}/results` - Ver resultados (TODO: motor cálculos)

#### Registro de Rutas
- **`api/main.py`**: Rutas registradas bajo `/api/v1`

---

### 3. Documentación

#### Documentación Técnica
- **`docs/sesiones/2025-12-10.md`**: Decisión arquitectónica completa
  - Contexto y problema
  - Modelo de datos detallado
  - APIs diseñadas
  - Plan de migración por fases

- **`docs/IMPLEMENTACION_MOTOR_PROCESOS.md`**: Este documento (resumen)

#### Documentación para Frontends
- **`latam-3c/docs/1-tecnica/05-api-motor-procesos-mrv.md`**: Guía completa de consumo
  - 9 secciones con ejemplos completos
  - Códigos de ejemplo React/TypeScript
  - Diagramas de estados y transiciones
  - Tabla de permisos por rol
  - Mapeo de endpoints antiguos → nuevos

#### Actualización de CLAUDE.md
- **`CLAUDE.md`**: Política de documentación de sesiones corregida
  - Sesiones locales: `docs/sesiones/YYYY-MM-DD.md`
  - Sesiones ecosistema: `latam-3c/docs/3-sesiones/`

---

## Arquitectura Implementada

### Modelo de Datos

```
ProcesoMRV (Registry)
├── id: "produce-peru-2024"
├── pais_iso: "PE"
├── tipo: PRODUCE | MRV_HR | 4C_NACIONAL
├── estado: borrador | activo | cerrado | archivado
├── config: JSONB
│   ├── template_version
│   ├── validaciones[]
│   ├── workflow_steps[]
│   ├── calculos_habilitados[]
│   └── deadlines
└── submissions[]
    └── Submission
        ├── estado_actual
        ├── workflow_history[]
        ├── archivo_excel
        ├── datos_extraidos
        ├── validaciones[]
        ├── comentarios[]
        └── resultados_calculos
```

### Máquina de Estados - Submission

```
borrador → enviado → en_revision → aprobado → publicado
              ↓
           rechazado → borrador
```

### Permisos por Rol

| Acción | Empresa | Coordinador País | Operador FICEM |
|--------|---------|------------------|----------------|
| Crear proceso | ❌ | ❌ | ✅ |
| Ver procesos | ✅ (su país) | ✅ (su país) | ✅ (todos) |
| Crear submission | ✅ | ❌ | ✅ |
| Subir Excel | ✅ (su empresa) | ❌ | ✅ |
| Validar | ✅ | ✅ | ✅ |
| Enviar submission | ✅ | ❌ | ✅ |
| Aprobar/rechazar | ❌ | ✅ | ✅ |

---

## Cómo Usar

### 1. Ejecutar Migración

```bash
# Aplicar migración
python scripts/migrate_procesos_mrv.py

# Revertir (si necesario)
python scripts/migrate_procesos_mrv.py --rollback
```

### 2. Crear Proceso (Operador FICEM)

```bash
curl -X POST http://localhost:8000/api/v1/procesos \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "produce-peru-2024",
    "pais_iso": "PE",
    "tipo": "PRODUCE",
    "nombre": "Protocolo PRODUCE Perú 2024",
    "ciclo": "2024",
    "config": {
      "template_version": "produce_peru_v2.1.xlsx",
      "hojas_requeridas": ["Cemento", "Concreto"],
      "validaciones": [...],
      "workflow_steps": [...],
      "deadline_envio": "2025-03-31",
      "calculos_habilitados": ["gcca", "bandas"]
    }
  }'
```

### 3. Activar Proceso

```bash
curl -X PATCH http://localhost:8000/api/v1/procesos/produce-peru-2024/estado \
  -H "Authorization: Bearer {token}" \
  -d '{"estado": "activo"}'
```

### 4. Flujo Empresa

```bash
# 1. Listar procesos activos
GET /api/v1/procesos?pais=PE&estado=activo

# 2. Crear submission
POST /api/v1/procesos/produce-peru-2024/submissions
{"empresa_id": 123}

# 3. Subir Excel
POST /api/v1/submissions/{id}/upload
[archivo]

# 4. Validar
POST /api/v1/submissions/{id}/validate

# 5. Enviar
POST /api/v1/submissions/{id}/submit
```

### 5. Flujo Coordinador

```bash
# 1. Ver submissions pendientes
GET /api/v1/procesos/produce-peru-2024/submissions?estado=enviado

# 2. Revisar submission
GET /api/v1/submissions/{id}

# 3. Aprobar o rechazar
POST /api/v1/submissions/{id}/review
{
  "accion": "aprobar",
  "comentario": "Datos validados correctamente"
}
```

---

## TODOs (Próximas Fases)

### Fase 2: Funcionalidad Completa
- [ ] Implementar almacenamiento de archivos (S3 o filesystem)
- [ ] Implementar validaciones dinámicas según `config.validaciones`
- [ ] Implementar generación de templates Excel dinámicos
- [ ] Parser de Excel → `datos_extraidos` JSON

### Fase 3: Motor de Cálculos
- [ ] Integrar motor de cálculos GCCA
- [ ] Cálculo de bandas por país
- [ ] Trigger automático: aprobar → calcular
- [ ] Benchmarking multi-empresa

### Fase 4: Workflow Avanzado
- [ ] Sistema de notificaciones (email/webhook)
- [ ] Triggers configurables por paso
- [ ] Reportes consolidados por proceso
- [ ] Exportadores por tipo (PRODUCE, MRV HR, etc.)

### Fase 5: Migración de Endpoints Antiguos
- [ ] Deprecar `/uploads` → `/submissions`
- [ ] Migrar datos existentes
- [ ] Mantener compatibilidad temporal

---

## Testing

### Tests Manuales

```bash
# 1. Iniciar API
uvicorn api.main:app --reload --port 8000

# 2. Ver documentación interactiva
open http://localhost:8000/docs

# 3. Autenticarse (ver storage/keys/DEV_CREDENTIALS.md)
POST /api/v1/auth/login
{
  "email": "<EMAIL>",
  "password": "<PASSWORD>"
}

# 4. Probar endpoints con token
Authorization: Bearer {access_token}
```

### Tests Automatizados (TODO)
- [ ] Tests unitarios para modelos
- [ ] Tests de integración para endpoints
- [ ] Tests de permisos por rol
- [ ] Tests de workflow completo

---

## Métricas de Implementación

| Categoría | Cantidad |
|-----------|----------|
| **Archivos creados** | 6 |
| **Archivos modificados** | 2 |
| **Modelos SQLAlchemy** | 2 nuevos |
| **Enums** | 3 nuevos |
| **Tablas BD** | 2 |
| **Índices BD** | 7 |
| **Endpoints API** | 16 |
| **Esquemas Pydantic** | 20+ |
| **Documentación** | 3 docs |
| **Líneas de código** | ~1500 |

---

## Referencias

- **Sesión de diseño**: `docs/sesiones/2025-12-10.md`
- **API para frontends**: `latam-3c/docs/1-tecnica/05-api-motor-procesos-mrv.md`
- **Endpoints legacy**: `latam-3c/docs/1-tecnica/04-api-endpoints-prioritarios.md`
- **Repo ecosistema**: https://github.com/cpinilla1974/latam-3c

---

**Estado**: ✅ Listo para testing y refinamiento
**Próximo paso**: Ejecutar migración y crear primer proceso de prueba