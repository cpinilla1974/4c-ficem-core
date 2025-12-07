# Metodología de Trabajo - 4C FICEM CORE

## Rol en el Ecosistema

**4C FICEM CORE** es el **backend centralizado** del sistema de huella de carbono para la industria cementera de Latinoamérica.

### Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    ECOSISTEMA 4C LATAM                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  latam-3c (Documentación)                                   │
│  └── Arquitectura, decisiones, flujos, funcionalidades      │
│      https://github.com/cpinilla1974/latam-3c               │
│                                                             │
│  4c-ficem-core (ESTE REPO) ◄── Backend Centralizado         │
│  └── APIs REST, cálculos, validación, PostgreSQL            │
│  └── Streamlit para operador FICEM                          │
│  └── JWT auth para todos los frontends                      │
│                                                             │
│  4c-peru (Frontend País)                                    │
│  └── Next.js, consume APIs de ficem-core                    │
│  └── Empresas cargan Excel, coordinadores revisan           │
│                                                             │
│  knowledge-api (IA/Analítica)                               │
│  └── RAG, predicciones, insights (desarrollo paralelo)      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Documentación Centralizada

**IMPORTANTE**: La documentación técnica vive en `latam-3c`:

| Documento | Contenido |
|-----------|-----------|
| `docs/1-tecnica/02-funcionalidades-por-usuario.md` | Funcionalidades por grupo, arquitectura, auth |
| `docs/1-tecnica/03-flujo-datos.md` | Flujo completo: empresa → país → FICEM |
| `docs/1-tecnica/01-estructura-datos-entrada.md` | Estructura de Excel de entrada |
| `docs/3-sesiones/` | Registro de decisiones por fecha |

**URL**: https://github.com/cpinilla1974/latam-3c/tree/main/docs

---

## Responsabilidades de FICEM CORE

### APIs REST (FastAPI)
- `/auth/login` - Autenticación JWT
- `/templates/{tipo}` - Generación de plantillas Excel
- `/uploads` - Carga y validación de Excel
- `/uploads/{id}/submit` - Confirmación de envío
- `/uploads/{id}/review` - Revisión por coordinador/FICEM
- `/results/{empresa_id}` - Resultados de cálculos
- `/benchmarking/{pais}` - Datos de benchmarking

### Motor de Cálculos
- Cálculos A1-A3 (Clinker, Cemento, Concreto)
- Clasificación GCCA (bandas A-G, AA-F)
- Validación de datos

### Base de Datos (PostgreSQL)
- Esquemas separados por país
- Usuarios y sesiones centralizados
- Datos de empresas, plantas, envíos, resultados

### Streamlit (Operador FICEM)
- Revisar envíos validados por países
- Ejecutar cálculos
- Gestionar empresas/plantas/usuarios
- Monitorear procesamiento
- Benchmarking regional

---

## Stack Tecnológico

- **API**: FastAPI
- **BD**: PostgreSQL (esquemas por país)
- **Auth**: JWT (emitido aquí, consumido por frontends)
- **Frontend Operador**: Streamlit
- **Python**: pandas, openpyxl, SQLAlchemy

---

## Iniciar la Aplicación

```bash
# Entorno virtual
python3 -m venv venv_ficem
source venv_ficem/bin/activate
pip install -r requirements.txt

# Streamlit (operador)
streamlit run app.py --server.port 8501

# FastAPI (APIs)
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## Políticas

### Comunicación
- Español neutro (NO regionalismos)
- Respuestas directas

### Commits
- NO incluir "Co-Authored-By: Claude"
- NO usar "Generated with Claude Code"
- Commits limpios del usuario

### Sesiones
- Documentar decisiones en `latam-3c/docs/3-sesiones/`
- Este repo es solo código

---

**Última actualización**: 2025-12-07
