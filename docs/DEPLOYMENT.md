# Guía de Deployment - 4C FICEM CORE API

## Arquitectura de Ambientes

### Desarrollo (Local)
- Base de datos con usuarios de prueba
- DEBUG=True
- Datos fake para testing
- CORS permisivo

### Staging
- Base de datos con datos similares a producción (anonimizados)
- DEBUG=False
- Simula producción
- CORS restrictivo

### Producción
- Base de datos VACÍA (solo esquema)
- DEBUG=False
- UN solo usuario ROOT con credenciales reales
- CORS restrictivo (solo frontends autorizados)
- HTTPS obligatorio

---

## Deployment en Producción

### Pre-requisitos

1. **Servidor con:**
   - Ubuntu 20.04+ / Debian 11+
   - Python 3.10+
   - PostgreSQL 14+
   - Nginx (para reverse proxy)
   - Certificado SSL (Let's Encrypt)

2. **DNS configurado:**
   - `api.4c-latam.org` → IP del servidor

3. **Variables de entorno preparadas** (ver sección Variables)

---

## Paso 1: Preparar el Servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3.10 python3.10-venv python3-pip postgresql postgresql-contrib nginx certbot python3-certbot-nginx

# Crear usuario de aplicación
sudo useradd -m -s /bin/bash ficem
sudo su - ficem
```

---

## Paso 2: Clonar y Configurar la Aplicación

```bash
# Clonar repositorio
git clone https://github.com/cpinilla1974/4c-ficem-core.git
cd 4c-ficem-core

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install gunicorn  # Para producción
```

---

## Paso 3: Configurar Base de Datos PostgreSQL

```bash
# Conectar a PostgreSQL
sudo -u postgres psql

# Crear base de datos y usuario
CREATE DATABASE ficem_core_prod;
CREATE USER ficem_user WITH ENCRYPTED PASSWORD 'contraseña_segura_aqui';
GRANT ALL PRIVILEGES ON DATABASE ficem_core_prod TO ficem_user;
\q
```

---

## Paso 4: Variables de Entorno de Producción

Crear archivo `.env` (NO commitear a git):

```bash
# Base de datos PostgreSQL
DATABASE_URL=postgresql://ficem_user:contraseña_segura_aqui@localhost:5432/ficem_core_prod

# JWT - CAMBIAR ESTAS CLAVES
JWT_SECRET_KEY=clave_super_secreta_generada_con_openssl_rand_hex_32
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

# FastAPI
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# CORS - SOLO frontends autorizados
ALLOWED_ORIGINS=https://peru.4c-latam.org,https://colombia.4c-latam.org,https://admin.4c-latam.org

# Configuración de archivos
MAX_UPLOAD_SIZE_MB=50
UPLOAD_DIR=/var/ficem/uploads

# Logs
LOG_LEVEL=INFO
LOG_FILE=/var/log/ficem/api.log
```

**Generar JWT_SECRET_KEY seguro:**
```bash
openssl rand -hex 32
```

---

## Paso 5: Inicializar Base de Datos

```bash
# Ejecutar migraciones
alembic upgrade head

# Crear SOLO usuario ROOT (NO usuarios de prueba)
python scripts/crear_usuario_admin.py
```

**IMPORTANTE**:
- NO responder "s" para crear usuarios de ejemplo
- Usar email y contraseña REALES del administrador FICEM
- Ejemplo: `director@ficem.org` con contraseña segura

---

## Paso 6: Configurar Systemd Service

Crear `/etc/systemd/system/ficem-api.service`:

```ini
[Unit]
Description=4C FICEM CORE API
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=ficem
Group=ficem
WorkingDirectory=/home/ficem/4c-ficem-core
Environment="PATH=/home/ficem/4c-ficem-core/venv/bin"
EnvironmentFile=/home/ficem/4c-ficem-core/.env
ExecStart=/home/ficem/4c-ficem-core/venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --access-logfile /var/log/ficem/access.log \
    --error-logfile /var/log/ficem/error.log \
    api.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Habilitar e iniciar servicio:**
```bash
sudo mkdir -p /var/log/ficem /var/ficem/uploads
sudo chown -R ficem:ficem /var/log/ficem /var/ficem

sudo systemctl daemon-reload
sudo systemctl enable ficem-api
sudo systemctl start ficem-api
sudo systemctl status ficem-api
```

---

## Paso 7: Configurar Nginx Reverse Proxy

Crear `/etc/nginx/sites-available/ficem-api`:

```nginx
server {
    listen 80;
    server_name api.4c-latam.org;

    # Redirigir a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.4c-latam.org;

    # SSL
    ssl_certificate /etc/letsencrypt/live/api.4c-latam.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.4c-latam.org/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Logs
    access_log /var/log/nginx/ficem-api-access.log;
    error_log /var/log/nginx/ficem-api-error.log;

    # Límites
    client_max_body_size 50M;

    # Proxy a FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

**Habilitar sitio:**
```bash
sudo ln -s /etc/nginx/sites-available/ficem-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Paso 8: Configurar SSL con Let's Encrypt

```bash
sudo certbot --nginx -d api.4c-latam.org
```

---

## Paso 9: Configurar Admin App Streamlit (Opcional)

Si se desea exponer la Admin App en producción:

Crear `/etc/systemd/system/ficem-admin.service`:

```ini
[Unit]
Description=4C FICEM Admin App
After=network.target ficem-api.service
Requires=ficem-api.service

[Service]
Type=simple
User=ficem
Group=ficem
WorkingDirectory=/home/ficem/4c-ficem-core
Environment="PATH=/home/ficem/4c-ficem-core/venv/bin"
EnvironmentFile=/home/ficem/4c-ficem-core/.env
ExecStart=/home/ficem/4c-ficem-core/venv/bin/streamlit run admin_app.py \
    --server.port 8501 \
    --server.address 127.0.0.1 \
    --server.headless true

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Nginx config para Admin App** (`/etc/nginx/sites-available/ficem-admin`):

```nginx
server {
    listen 443 ssl http2;
    server_name admin.4c-latam.org;

    ssl_certificate /etc/letsencrypt/live/admin.4c-latam.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.4c-latam.org/privkey.pem;

    # Restricción por IP (opcional - solo oficina FICEM)
    # allow 203.0.113.0/24;
    # deny all;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Post-Deployment: Configuración Inicial

### 1. Crear Usuario ROOT
El primer usuario ROOT debe crearse manualmente en el servidor:

```bash
cd /home/ficem/4c-ficem-core
source venv/bin/activate
python scripts/crear_usuario_admin.py
```

**Ingresar datos reales:**
- Email: `director@ficem.org` (o email del director FICEM)
- Password: Contraseña segura (min 12 caracteres)

### 2. Crear Coordinadores de País
El usuario ROOT accede a Admin App (`https://admin.4c-latam.org`) y crea:

- Coordinador Perú: `coordinador@asocem.org.pe` (rol: COORDINADOR_PAIS)
- Coordinador Colombia: `coordinador@ccac.org.co` (rol: COORDINADOR_PAIS)
- Coordinador Chile: `coordinador@ich.cl` (rol: COORDINADOR_PAIS)
- etc.

### 3. Configurar Procesos MRV
El usuario ROOT o ADMIN_PROCESO crea los procesos activos para cada país.

---

## Monitoreo y Mantenimiento

### Logs
```bash
# Logs de la API
sudo journalctl -u ficem-api -f

# Logs de Nginx
sudo tail -f /var/log/nginx/ficem-api-error.log

# Logs de aplicación
sudo tail -f /var/log/ficem/api.log
```

### Health Check
```bash
curl https://api.4c-latam.org/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "database": "connected",
  "service": "4c-ficem-core"
}
```

### Backup de Base de Datos
```bash
# Backup diario automático
sudo crontab -e

# Agregar:
0 2 * * * pg_dump -U ficem_user ficem_core_prod | gzip > /backup/ficem_$(date +\%Y\%m\%d).sql.gz
```

### Actualizar Aplicación
```bash
cd /home/ficem/4c-ficem-core
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart ficem-api
```

---

## Checklist de Seguridad

- [ ] JWT_SECRET_KEY generado aleatoriamente (no usar el del ejemplo)
- [ ] DEBUG=False en producción
- [ ] CORS configurado solo con frontends autorizados
- [ ] SSL/HTTPS configurado correctamente
- [ ] Firewall configurado (solo puertos 80, 443, 22)
- [ ] PostgreSQL solo acepta conexiones locales
- [ ] Passwords seguros (min 12 caracteres)
- [ ] NO hay usuarios de prueba en BD de producción
- [ ] Backups automáticos configurados
- [ ] Logs monitoreados
- [ ] Admin App con restricción de IP (opcional)

---

## Troubleshooting

### API no inicia
```bash
# Ver logs
sudo journalctl -u ficem-api -n 50

# Verificar permisos
ls -la /home/ficem/4c-ficem-core

# Verificar .env
cat /home/ficem/4c-ficem-core/.env
```

### Error de conexión a BD
```bash
# Verificar PostgreSQL
sudo systemctl status postgresql

# Probar conexión manual
psql -U ficem_user -d ficem_core_prod -h localhost
```

### CORS Error en frontend
Verificar que `ALLOWED_ORIGINS` en `.env` incluye el dominio del frontend:
```
ALLOWED_ORIGINS=https://peru.4c-latam.org,https://colombia.4c-latam.org
```

---

## Contacto

Para soporte en deployment:
- **Equipo**: DevOps FICEM
- **Email**: soporte@ficem.org

---

**Última actualización**: 2025-12-17