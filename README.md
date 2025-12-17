# 4C FICEM CORE

Backend centralizado del sistema de huella de carbono para la industria cementera de Latinoamérica.

## Arquitectura

Este repositorio es el **backend REST** que sirve a:
- Frontends de país (4c-peru, 4c-colombia, etc.)
- Sistema de IA/analítica (knowledge-api)

```
Frontend País (4c-peru)
        ↓
4C FICEM CORE (Este repo) ← Backend REST
        ↓
PostgreSQL
```

## Tecnologías

- **Framework**: FastAPI
- **Base de datos**: PostgreSQL (esquemas por país)
- **Autenticación**: JWT
- **ORM**: SQLAlchemy 2.0+
- **Migraciones**: Alembic

## Instalación

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Inicializar base de datos
alembic upgrade head

# Crear usuario administrador
python scripts/crear_usuario_admin.py

# Ejecutar API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# (Opcional) Ejecutar app de administración Streamlit
streamlit run admin_app.py --server.port 8501
```

## Estructura del Proyecto

```
4c-ficem-core/
├── api/                  # FastAPI REST
│   ├── main.py
│   ├── routes/          # Endpoints
│   ├── schemas/         # Pydantic models
│   ├── services/        # Lógica de negocio
│   └── middleware/      # Auth JWT
├── calculos/            # Motor cálculos A1-A3
├── excel/               # Procesamiento Excel
├── database/            # Models, repositories
├── modules/             # Utilidades (GCCA)
├── sql/                 # Scripts SQL
└── tests/               # Tests unitarios e integración
```

## Endpoints Implementados

### Autenticación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Autenticación JWT |
| GET | `/api/v1/auth/me` | Info usuario actual |

### Usuarios
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/usuarios` | Listar usuarios (filtros: país, rol) |
| GET | `/api/v1/usuarios/{id}` | Obtener usuario por ID |
| POST | `/api/v1/usuarios` | Crear nuevo usuario |
| PUT | `/api/v1/usuarios/{id}` | Actualizar usuario |
| DELETE | `/api/v1/usuarios/{id}` | Desactivar usuario |

### Procesos MRV
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/procesos` | Listar procesos MRV |
| POST | `/api/v1/procesos` | Crear proceso MRV |

### Submissions
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/submissions` | Listar submissions |
| POST | `/api/v1/submissions` | Crear submission |

## App de Administración (Streamlit)

Interfaz web para operadores FICEM:
- **URL**: http://localhost:8501
- **Credenciales por defecto**: `admin@ficem.org` / `admin123`

**Funcionalidades**:
- Dashboard con métricas
- Gestión de usuarios (listar, crear, filtrar)
- Gestión de procesos MRV
- Monitoreo de submissions

## Documentación

- **Arquitectura del ecosistema**: [docs/ARQUITECTURA_ECOSISTEMA.md](docs/ARQUITECTURA_ECOSISTEMA.md)
- **Plan de implementación**: [docs/PLAN_IMPLEMENTACION.md](docs/PLAN_IMPLEMENTACION.md)
- **Páginas frontend**: [docs/FRONTEND_PAGES.md](docs/FRONTEND_PAGES.md)
- **Metodología**: [CLAUDE.md](CLAUDE.md)
- **Documentación técnica completa**: https://github.com/cpinilla1974/latam-3c

## API Docs

Una vez ejecutando, accede a:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=api --cov=calculos --cov=excel
```

## Desarrollo

Ver [PLAN_IMPLEMENTACION.md](PLAN_IMPLEMENTACION.md) para el orden de implementación por fases.

## Licencia

Proyecto privado - FICEM LATAM
