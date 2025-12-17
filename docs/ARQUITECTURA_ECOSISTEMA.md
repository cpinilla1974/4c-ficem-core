# Arquitectura del Ecosistema 4C LATAM

## Visión General

```
┌──────────────────────────────────────────────────────────────────┐
│                    ECOSISTEMA 4C LATAM                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  4c-ficem-web (Frontend FICEM)                             │ │
│  │  ├─> Sección Pública (landing, blog, dashboard LATAM)     │ │
│  │  └─> Sección Operador (admin, exploración, IA)            │ │
│  └──────────────────────────┬─────────────────────────────────┘ │
│                             ↓ JWT + APIs REST                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  4c-ficem-core (Backend API - Centralizado)               │ │
│  │  ├─> APIs REST para todos los frontends                   │ │
│  │  ├─> Motor de cálculos A1-A3                              │ │
│  │  ├─> Validación de datos                                  │ │
│  │  └─> Gestión usuarios, empresas, factores                 │ │
│  └──────────────────────────┬─────────────────────────────────┘ │
│                             ↓                                    │
│         ┌───────────────────┼──────────────────────┐            │
│         ↓                   ↓                      ↓            │
│  ┌─────────────┐     ┌─────────────┐      ┌─────────────┐      │
│  │ 4c-peru     │     │ 4c-colombia │      │ 4c-chile    │      │
│  │ (Next.js)   │     │ (Next.js)   │      │ (Next.js)   │      │
│  └─────────────┘     └─────────────┘      └─────────────┘      │
│         ↓                   ↓                      ↓            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL (ficem_bd)                                     │ │
│  │  knowledge-api (BD conocimiento + IA)                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Repositorios

### 1. latam-3c (Documentación)
**URL**: https://github.com/cpinilla1974/latam-3c
**Propósito**: Documentación técnica centralizada
- Arquitectura del ecosistema
- Decisiones técnicas
- Flujos de datos
- Estructura de Excel de entrada

### 2. 4c-ficem-core (Backend API - Este Repo)
**Propósito**: Backend REST centralizado
**Stack**: FastAPI + PostgreSQL
**Responsabilidades**:
- APIs REST para todos los frontends
- Autenticación JWT
- Motor de cálculos A1-A3
- Clasificación GCCA
- Validación de datos
- CRUD usuarios, empresas, plantas
- Gestión de factores de emisión
- Exploración de datos
- Integración con knowledge-api

### 3. 4c-ficem-web (Frontend FICEM - Nuevo)
**Propósito**: Frontend oficial de FICEM LATAM
**Stack**: Next.js + TypeScript + TailwindCSS
**Secciones**:

#### a) Pública (sin login)
- Landing page
- Dashboard regional (estadísticas anónimas)
- Blog / Noticias
- Documentación pública

#### b) Operador FICEM (requiere login)
- Administración usuarios/empresas/plantas
- Gestión factores de emisión
- Exploración de datos (ficem_bd)
- Herramientas IA (knowledge-api)
- Benchmarking regional
- Revisión de envíos
- Ejecución de cálculos

### 4. 4c-peru (Frontend País)
**Propósito**: Frontend para Perú
**Stack**: Next.js + TypeScript
**Usuarios**:
- Empresas (carga datos, ve resultados)
- Coordinador País (revisa, aprueba)

### 5. 4c-colombia, 4c-chile, etc. (Frontends País)
**Propósito**: Frontends para cada país
**Stack**: Next.js (mismo que 4c-peru)
**Estructura**: Idéntica a 4c-peru

### 6. knowledge-api (IA/Analítica - Desarrollo Paralelo)
**Propósito**: Sistema de IA y base de datos de conocimiento
**Stack**: Python + LangChain + ChromaDB
**Funcionalidades**:
- RAG (Retrieval Augmented Generation)
- Chat inteligente
- Predicciones
- Generación de reportes con IA

---

## Flujo de Datos

### Empresa Carga Datos
```
[4c-peru]
    ↓ Descarga template
[4c-ficem-core] → Genera Excel
    ↓ Upload Excel
[4c-ficem-core] → Valida
    ↓ Envía a revisión
[Coordinador País en 4c-peru]
    ↓ Aprueba
[4c-ficem-core] → Ejecuta cálculos A1-A3
    ↓ Almacena
[PostgreSQL ficem_bd]
    ↓ Consulta resultados
[4c-peru] → Muestra resultados a empresa
```

### Operador FICEM Administra
```
[4c-ficem-web - Operador]
    ↓ CRUD usuarios/empresas
[4c-ficem-core] → APIs /admin/*
    ↓ Actualiza
[PostgreSQL ficem_bd]
```

### Público Consulta Dashboard
```
[4c-ficem-web - Público]
    ↓ GET /public/stats
[4c-ficem-core] → Consulta agregada anónima
    ↓ Retorna
[PostgreSQL ficem_bd]
```

---

## Autenticación y Autorización

### Emisión de JWT
- **Emisor**: `4c-ficem-core` (endpoint `/auth/login`)
- **Consumidores**: Todos los frontends
- **Contenido JWT**:
  ```json
  {
    "user_id": 123,
    "email": "usuario@empresa.com",
    "rol": "empresa | coordinador_pais | operador_ficem",
    "pais": "peru",
    "empresa_id": 456
  }
  ```

### Roles y Permisos

| Rol | Acceso | Frontends |
|-----|--------|-----------|
| **empresa** | Solo sus datos | 4c-peru, 4c-colombia, etc. |
| **coordinador_pais** | Datos de su país | 4c-peru, 4c-colombia, etc. |
| **operador_ficem** | Todo el sistema | 4c-ficem-web |

---

## APIs del Backend (4c-ficem-core)

### Para Frontends País (4c-peru, etc.)
```
POST   /auth/login
GET    /templates/{tipo}
POST   /uploads
GET    /uploads/{id}
POST   /uploads/{id}/submit
GET    /results/{empresa_id}
GET    /benchmarking/{pais}
```

### Para Frontend FICEM (4c-ficem-web)
```
# Administración
POST   /admin/users
PUT    /admin/users/{id}
DELETE /admin/users/{id}
POST   /admin/empresas
PUT    /admin/empresas/{id}
DELETE /admin/empresas/{id}
PUT    /admin/factores-emision
PUT    /admin/bandas-gcca

# Exploración de datos
GET    /data/query
GET    /data/export
GET    /data/stats

# Público
GET    /public/stats
GET    /public/blog
POST   /admin/blog

# IA
POST   /ai/chat
GET    /ai/predictions
```

---

## Base de Datos (PostgreSQL)

### Esquema Centralizado
```sql
-- Usuarios y autenticación
usuarios (id, email, password_hash, rol, pais, empresa_id)

-- Empresas y plantas
empresas (id, nombre, pais, perfil_planta)
plantas (id, empresa_id, nombre, ubicacion)

-- Envíos y resultados
envios (id, empresa_id, archivo, estado, created_at)
resultados (id, envio_id, a1, a2, a3, banda_gcca)

-- Configuración
factores_emision (id, nombre, valor, unidad, pais)
bandas_gcca (id, resistencia, limite_aa, limite_a, ...)

-- Público
blog_posts (id, titulo, contenido, slug, published_at)
```

### Esquemas por País (opcional)
```sql
schema_peru.remitos
schema_colombia.remitos
schema_chile.remitos
```

---

## Frontend 4c-ficem-web (Páginas)

### Sección Pública (17 páginas totales)
1. **Home** - Landing page
2. **About** - Sobre FICEM y el proyecto
3. **Dashboard Regional** - Estadísticas LATAM anónimas
4. **Países** - Lista de países participantes
5. **Blog** - Listado de noticias
6. **Blog Post** - Detalle de noticia
7. **Documentación** - Guías públicas

### Sección Operador FICEM (10 páginas adicionales)
8. **Dashboard Operador** - Resumen del sistema
9. **Revisión de Envíos** - Aprobar/rechazar
10. **Gestión Usuarios** - CRUD usuarios
11. **Gestión Empresas** - CRUD empresas
12. **Gestión Plantas** - CRUD plantas
13. **Factores de Emisión** - Actualizar factores
14. **Bandas GCCA** - Actualizar bandas
15. **Explorador de Datos** - Consultas SQL
16. **Descarga Masiva** - Exportar datos
17. **Herramientas IA** - Chat, predicciones
18. **Benchmarking Regional** - Comparativas
19. **Gestión Blog** - CRUD posts

---

## Stack Tecnológico

### Backend (4c-ficem-core)
- FastAPI 0.104+
- PostgreSQL 12+
- SQLAlchemy 2.0+
- Alembic (migraciones)
- JWT (python-jose)
- Pandas, NumPy (cálculos)
- openpyxl (Excel)

### Frontend (4c-ficem-web, 4c-peru, etc.)
- Next.js 14+ (App Router)
- TypeScript
- TailwindCSS + shadcn/ui
- React Query (API cache)
- Recharts (gráficos)
- axios (HTTP client)

### IA (knowledge-api)
- Python
- LangChain
- ChromaDB
- Ollama / Claude API

---

## Deploy

### Producción
```
4c-ficem-core     → Render / Railway / DigitalOcean
4c-ficem-web      → Vercel
4c-peru           → Vercel
4c-colombia       → Vercel
PostgreSQL        → Render / Supabase / AWS RDS
knowledge-api     → Render / Railway
```

### Desarrollo
```
4c-ficem-core     → localhost:8000
4c-ficem-web      → localhost:3000
4c-peru           → localhost:3001
PostgreSQL        → localhost:5432
```

---

## Orden de Desarrollo

1. ✅ Limpiar 4c-ficem-core (HECHO)
2. ⏭️ Implementar backend FASE 1-7 (core funcional)
3. ⏭️ Crear 4c-ficem-web
4. ⏭️ Implementar páginas públicas (landing, blog)
5. ⏭️ Crear 4c-peru
6. ⏭️ Implementar páginas empresa/coordinador
7. ⏭️ Implementar backend FASE 8-10 (admin + público)
8. ⏭️ Implementar páginas operador FICEM
9. ⏭️ Integrar knowledge-api (FASE 11)
10. ⏭️ Testing end-to-end

---

**Última actualización**: 2025-12-07
