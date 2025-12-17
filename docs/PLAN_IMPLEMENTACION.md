# Plan de Implementación - 4C FICEM CORE

## Decisiones Tomadas

- ✅ **Arquitectura 2 Repositorios**:
  - `4c-ficem-core`: Backend API REST (FastAPI)
  - `4c-ficem-web`: Frontend FICEM (Next.js) - público + operador
- ✅ Eliminar módulos IA (van en knowledge-api)
- ✅ Backend puro: FastAPI + PostgreSQL + Motor de Cálculos

---

## Ecosistema Completo

```
┌─────────────────────────────────────────────────────────┐
│  4c-ficem-web (Frontend FICEM - Nuevo Repo)             │
│  ├─> Sección Pública (landing, blog, dashboard)        │
│  └─> Sección Operador (admin, exploración, IA)         │
└──────────────────────────┬──────────────────────────────┘
                           ↓ JWT + APIs
┌─────────────────────────────────────────────────────────┐
│  4c-ficem-core (Backend API - Este Repo)                │
│  ├─> APIs REST para frontends país                     │
│  ├─> APIs REST para frontend FICEM                     │
│  ├─> Motor de cálculos A1-A3                           │
│  └─> Gestión de datos y usuarios                       │
└──────────────────────────┬──────────────────────────────┘
                           ↓
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ 4c-peru       │  │ 4c-colombia   │  │ 4c-chile      │
│ (Frontend)    │  │ (Frontend)    │  │ (Frontend)    │
└───────────────┘  └───────────────┘  └───────────────┘
        ↓                  ↓                  ↓
┌─────────────────────────────────────────────────────────┐
│  PostgreSQL (ficem_bd)                                  │
│  knowledge-api (BD conocimiento + IA)                   │
└─────────────────────────────────────────────────────────┘
```

---

## Este Repositorio: 4c-ficem-core (Backend)

### Arquitectura del Proyecto

```
4c-ficem-core/
├── api/                          # FastAPI REST
│   ├── main.py                   # App principal
│   ├── dependencies.py           # Inyección dependencias
│   ├── routes/
│   │   ├── auth.py              # POST /auth/login
│   │   ├── templates.py         # GET /templates/{tipo}
│   │   ├── uploads.py           # POST /uploads, /uploads/{id}/submit|review
│   │   ├── results.py           # GET /results/{empresa_id}
│   │   ├── benchmarking.py      # GET /benchmarking/{pais}
│   │   ├── admin.py             # 🆕 Gestión usuarios/empresas/factores
│   │   ├── data_explorer.py     # 🆕 Exploración datos ficem_bd
│   │   └── public.py            # 🆕 Endpoints públicos (stats, blog)
│   ├── schemas/                 # Pydantic models
│   │   ├── auth.py
│   │   ├── empresa.py
│   │   ├── upload.py
│   │   ├── resultado.py
│   │   ├── admin.py             # 🆕 Schemas admin
│   │   └── public.py            # 🆕 Schemas públicos
│   ├── services/                # Lógica de negocio
│   │   ├── auth_service.py
│   │   ├── upload_service.py
│   │   ├── calculo_service.py
│   │   ├── admin_service.py     # 🆕 CRUD admin
│   │   └── data_service.py      # 🆕 Exploración datos
│   └── middleware/
│       └── jwt_auth.py          # Middleware JWT
│
├── calculos/                     # Motor de cálculos
│   ├── __init__.py
│   ├── clinker.py               # Cálculo A1
│   ├── cemento.py               # Cálculo A2
│   ├── concreto.py              # Cálculo A3
│   ├── clasificador_gcca.py     # Usa modules/bandas_utils.py
│   └── validador.py             # Validaciones coherencia
│
├── excel/                        # Procesamiento Excel
│   ├── __init__.py
│   ├── generator.py             # Generación templates
│   ├── parser.py                # Lectura Excel
│   ├── validator.py             # Validaciones
│   └── schemas.py               # Estructura esperada
│
├── database/                     # Capa datos
│   ├── __init__.py
│   ├── connection.py            # ✅ MANTENER
│   ├── models.py                # ⚠️ EXPANDIR
│   └── repository.py            # ⚠️ EXPANDIR
│
├── modules/                      # Utilidades
│   ├── __init__.py
│   └── bandas_utils.py          # ✅ MANTENER
│
├── services/                     # Servicios auxiliares
│   ├── __init__.py
│   └── utiles.py                # ✅ MANTENER
│
├── sql/                          # Scripts SQL
│   ├── create_remitos_unificados.sql
│   ├── create_vistas_materializadas.sql
│   ├── create_gcca_references.sql
│   └── insert_gcca_data.sql
│
├── data/                         # Datos estáticos
│   └── bandas_gcca.json         # ✅ MANTENER
│
├── tests/                        # Tests
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── alembic/                      # Migraciones BD
│   └── versions/
│
├── .env.example
├── alembic.ini
├── requirements.txt
└── README.md
```

---

## Orden de Implementación Backend

### FASE 1: Fundación (Base de Datos)
**Objetivo**: Estructura de datos sólida

1. **Expandir Modelos SQLAlchemy** (database/models.py)
   - Usuario (grupos: empresa, coordinador_pais, operador_ficem)
   - Planta (relacionada con Empresa)
   - Envio (estados: borrador, validando, rechazado, aprobado, procesado)
   - Resultado (cálculos A1-A3, banda GCCA)
   - FactorEmision (tabla configurable para operador FICEM)
   - BlogPost (para sección pública)

2. **Expandir Repositorios** (database/repository.py)
   - CRUD para todos los modelos
   - Queries optimizadas

3. **Migraciones Alembic**
   - `alembic init`
   - Migración inicial

4. **Scripts SQL de Datos de Referencia**
   - Ejecutar sql/create_gcca_references.sql
   - Ejecutar sql/insert_gcca_data.sql

**Entregable**: Base de datos completa

---

### FASE 2: Autenticación (FastAPI Core)
**Objetivo**: Sistema de autenticación funcionando

5. **FastAPI Base** (api/main.py)
   - App FastAPI
   - CORS configurado (permite 4c-ficem-web + frontends país)
   - Health check endpoint

6. **Schemas Pydantic** (api/schemas/auth.py)
   - LoginRequest
   - TokenResponse
   - UserResponse

7. **Auth Service** (api/services/auth_service.py)
   - Verificación credenciales
   - Generación JWT con rol de usuario
   - Validación tokens

8. **Auth Routes** (api/routes/auth.py)
   - POST /auth/login
   - POST /auth/refresh

9. **JWT Middleware** (api/middleware/jwt_auth.py)
   - Dependency para proteger rutas
   - Verificación de roles

**Entregable**: Login funcionando, JWT emitido

---

### FASE 3: Gestión de Templates Excel
**Objetivo**: Generación de plantillas

10. **Excel Generator** (excel/generator.py)
    - Templates para integrada / molienda / concreto
    - Hojas según perfil de planta

11. **Excel Schemas** (excel/schemas.py)
    - Definición de columnas esperadas

12. **Templates Routes** (api/routes/templates.py)
    - GET /templates/{tipo}

**Entregable**: Descarga de templates

---

### FASE 4: Carga y Validación de Excel
**Objetivo**: Empresas pueden cargar datos

13. **Excel Parser** (excel/parser.py)
    - Lectura de Excel

14. **Excel Validator** (excel/validator.py)
    - Validación de estructura
    - Validación de coherencia lógica

15. **Upload Service** (api/services/upload_service.py)
    - Orquesta parsing + validación

16. **Upload Schemas** (api/schemas/upload.py)
    - UploadResponse
    - ValidationError

17. **Upload Routes** (api/routes/uploads.py)
    - POST /uploads
    - GET /uploads/{id}
    - POST /uploads/{id}/submit

**Entregable**: Carga de Excel con validación

---

### FASE 5: Motor de Cálculos A1-A3
**Objetivo**: Cálculo de huella de carbono

18. **Cálculo Clinker** (calculos/clinker.py)
19. **Cálculo Cemento** (calculos/cemento.py)
20. **Cálculo Concreto** (calculos/concreto.py)
21. **Validador** (calculos/validador.py)
22. **Clasificador GCCA** (calculos/clasificador_gcca.py)
23. **Calculo Service** (api/services/calculo_service.py)

**Entregable**: Cálculos A1-A3 + GCCA

---

### FASE 6: Revisión y Aprobación
**Objetivo**: Coordinador país y FICEM revisan envíos

24. **Review Endpoints** (api/routes/uploads.py)
    - POST /uploads/{id}/review
    - GET /uploads/pending

25. **Permisos por Grupo**
    - Middleware verifica rol

**Entregable**: Flujo de revisión completo

---

### FASE 7: Resultados y Benchmarking
**Objetivo**: Consulta de resultados

26. **Results Routes** (api/routes/results.py)
    - GET /results/{empresa_id}
    - GET /results/{empresa_id}/historico

27. **Benchmarking Routes** (api/routes/benchmarking.py)
    - GET /benchmarking/{pais}
    - GET /benchmarking/regional

28. **Vistas Materializadas**
    - Ejecutar sql/create_vistas_materializadas.sql

**Entregable**: Consultas de resultados

---

### FASE 8: APIs Administración (Operador FICEM)
**Objetivo**: Gestión completa del sistema

29. **Admin Service** (api/services/admin_service.py)
    - CRUD usuarios
    - CRUD empresas
    - CRUD plantas
    - Actualizar factores de emisión
    - Actualizar bandas GCCA

30. **Admin Routes** (api/routes/admin.py)
    - POST/PUT/DELETE /admin/users
    - POST/PUT/DELETE /admin/empresas
    - POST/PUT/DELETE /admin/plantas
    - PUT /admin/factores-emision
    - PUT /admin/bandas-gcca

31. **Permisos Admin**
    - Solo rol `operador_ficem`

**Entregable**: APIs de administración

---

### FASE 9: APIs Exploración de Datos
**Objetivo**: Operador FICEM explora datos

32. **Data Explorer Service** (api/services/data_service.py)
    - Queries a ficem_bd
    - Agregaciones
    - Descarga masiva CSV/Excel

33. **Data Explorer Routes** (api/routes/data_explorer.py)
    - GET /data/query (consulta personalizada)
    - GET /data/export (descarga masiva)
    - GET /data/stats (estadísticas generales)

**Entregable**: Exploración de datos

---

### FASE 10: APIs Públicas (Sección Pública)
**Objetivo**: Endpoints para landing y blog

34. **Public Service** (api/services/public_service.py)
    - Estadísticas regionales anónimas
    - Gestión de blog posts

35. **Public Routes** (api/routes/public.py)
    - GET /public/stats (dashboard público)
    - GET /public/blog (lista posts)
    - GET /public/blog/{slug} (detalle post)

36. **Admin Blog Routes** (api/routes/admin.py)
    - POST/PUT/DELETE /admin/blog

**Entregable**: APIs públicas

---

### FASE 11: Integración con knowledge-api
**Objetivo**: Conectar con herramientas IA

37. **Knowledge API Client** (api/services/knowledge_service.py)
    - Cliente HTTP para knowledge-api
    - Endpoints de chat
    - Endpoints de análisis predictivo

38. **AI Routes** (api/routes/ai.py)
    - POST /ai/chat (proxy a knowledge-api)
    - GET /ai/predictions

**Entregable**: Integración IA

---

### FASE 12: Testing y Documentación
**Objetivo**: Sistema robusto

39. **Tests Unitarios** (tests/unit/)
40. **Tests de Integración** (tests/integration/)
41. **Documentación API**
    - OpenAPI automático
    - README actualizado

**Entregable**: Sistema testeado

---

## Dependencias entre Fases

```
FASE 1 (BD)
    ↓
FASE 2 (Auth)
    ↓
FASE 3-7 (Core: Templates, Upload, Cálculos, Revisión, Resultados)
    ↓
FASE 8 (Admin APIs)
    ↓
FASE 9 (Data Explorer)
    ↓
FASE 10 (APIs Públicas)
    ↓
FASE 11 (Integración IA)
    ↓
FASE 12 (Testing)
```

---

## Próximos Pasos

1. ✅ Ejecutar limpieza de código
2. ✅ Actualizar requirements.txt
3. ✅ Crear estructura de directorios
4. ⏭️ **Iniciar FASE 1: Expandir modelos BD**
5. ⏭️ Crear repositorio `4c-ficem-web` (Frontend)

---

**Última actualización**: 2025-12-07
