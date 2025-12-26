# Quick Start - 4C FICEM CORE

## Instalación Rápida

### 1. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` y configurar:
- `DATABASE_URL`: URL de PostgreSQL
- `JWT_SECRET_KEY`: Clave secreta para JWT (cambiar en producción)

### 4. Crear base de datos PostgreSQL

```bash
# En PostgreSQL
createdb ficem_core
```

O usando psql:
```sql
CREATE DATABASE ficem_core;
```

### 5. Inicializar base de datos

```bash
# Ejecutar migraciones
alembic upgrade head
```

### 6. Crear usuario administrador

```bash
python scripts/crear_usuario_admin.py
```

Esto creará el usuario ROOT con credenciales definidas en variables de entorno:

| Variable | Descripción |
|----------|-------------|
| `ADMIN_EMAIL` | Email del admin (default: admin@ficem.org) |
| `ADMIN_PASSWORD` | Password del admin (REQUERIDO en producción) |

Opcionalmente, puedes crear usuarios de ejemplo para desarrollo:
```bash
echo "s" | python scripts/crear_usuario_admin.py
```

> **IMPORTANTE**: Los passwords de usuarios de ejemplo se definen en variables de entorno.
> Ver `.env.example` para la lista completa.

### 7. Ejecutar servicios

#### Opción A: Solo API (FastAPI)
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Opción B: API + Admin App (recomendado)
Terminal 1 - API:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Streamlit:
```bash
streamlit run admin_app.py --server.port 8501
```

### 8. Acceder a las aplicaciones

**API REST**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Admin App (Streamlit)**:
- URL: http://localhost:8501
- Login: Usar credenciales configuradas en `.env`

## Probar Login

### Desde Swagger UI

1. Ir a http://localhost:8000/docs
2. Expandir `POST /auth/login`
3. Click en "Try it out"
4. Usar credenciales configuradas en tu `.env`:
   ```json
   {
     "email": "<ADMIN_EMAIL>",
     "password": "<ADMIN_PASSWORD>"
   }
   ```
5. Click en "Execute"
6. Copiar el `access_token` de la respuesta

### Desde cURL

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "$ADMIN_EMAIL",
    "password": "$ADMIN_PASSWORD"
  }'
```

### Usar el token

```bash
TOKEN="<tu_token_aqui>"

curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

## Probar desde Frontend

### Ejemplo con fetch (JavaScript)

```javascript
// Login - usar credenciales de tu .env
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: process.env.ADMIN_EMAIL,
    password: process.env.ADMIN_PASSWORD
  })
});

const { access_token } = await loginResponse.json();

// Usar token
const userResponse = await fetch('http://localhost:8000/auth/me', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

const user = await userResponse.json();
console.log(user);
```

### Ejemplo con axios (React/Next.js)

```javascript
import axios from 'axios';

const API_URL = 'http://localhost:8000';

// Login - usar credenciales de tu .env
const loginResponse = await axios.post(`${API_URL}/auth/login`, {
  email: process.env.ADMIN_EMAIL,
  password: process.env.ADMIN_PASSWORD
});

const token = loginResponse.data.access_token;

// Guardar token (localStorage, cookie, etc.)
localStorage.setItem('token', token);

// Usar token en requests
const userResponse = await axios.get(`${API_URL}/auth/me`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

console.log(userResponse.data);
```

## Siguiente Paso

Una vez funcionando la autenticación, se pueden implementar las siguientes fases según [docs/PLAN_IMPLEMENTACION.md](docs/PLAN_IMPLEMENTACION.md):

- FASE 3: Templates Excel
- FASE 4: Carga y validación Excel
- FASE 5: Motor de cálculos A1-A3
- ... y más

---

## Gestión de Usuarios desde Admin App

1. Accede a http://localhost:8501
2. Login con las credenciales configuradas en tu `.env`
3. Ve a la sección "👥 Usuarios"
4. **Ver usuarios**: Click en "🔄 Cargar Usuarios"
5. **Crear usuario**: Pestaña "Crear Usuario", completa el formulario

**Roles disponibles**:
- `ROOT` - Superadmin (acceso total)
- `ADMIN_PROCESO` - Gestiona procesos MRV
- `EJECUTIVO_FICEM` - Solo lectura ejecutiva
- `COORDINADOR_PAIS` - Supervisa país
- `SUPERVISOR_EMPRESA` - Aprueba envíos empresa
- `INFORMANTE_EMPRESA` - Carga datos empresa
- `VISOR_EMPRESA` - Solo lectura empresa

---

**Última actualización**: 2025-12-17
