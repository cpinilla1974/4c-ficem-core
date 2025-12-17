# Páginas del Frontend FICEM (4c-ficem-web)

## Arquitectura

```
4c-ficem-web (Next.js)
    ↓ JWT en headers
4c-ficem-core (FastAPI)
    ↓ PostgreSQL
```

---

## Secciones del Frontend FICEM

### SECCIÓN PÚBLICA (sin autenticación)

#### 1. Home / Landing Page
- **URL**: `/`
- **Consume**: Ninguno (estático)
- **Muestra**:
  - Hero section
  - Descripción del proyecto 4C LATAM
  - Call-to-action para países
  - Enlace a dashboard público
  - Enlace a blog

#### 2. About / Sobre el Proyecto
- **URL**: `/about`
- **Consume**: Ninguno (estático)
- **Muestra**:
  - Qué es FICEM
  - Qué es el proyecto 4C
  - Países participantes
  - Metodología GCCA
  - Contacto

#### 3. Dashboard Regional Público
- **URL**: `/dashboard`
- **Consume**: `GET /public/stats`
- **Muestra**:
  - Estadísticas agregadas LATAM (anónimas):
    - Total de empresas participantes
    - Total de toneladas de cemento/concreto
    - Distribución por bandas GCCA
    - Promedio regional de emisiones A1-A3
  - Gráficos:
    - Mapa de países participantes
    - Evolución temporal regional
    - Distribución de bandas GCCA

#### 4. Países Participantes
- **URL**: `/paises`
- **Consume**: `GET /public/paises`
- **Muestra**:
  - Lista de países participantes
  - Estado de cada país (activo, en preparación)
  - Enlace a sitio web de cada país (4c-peru, 4c-colombia, etc.)
  - Coordinador de país

#### 5. Blog / Noticias
- **URL**: `/blog`
- **Consume**: `GET /public/blog`
- **Muestra**:
  - Listado de posts de blog
  - Filtros: fecha, categoría, país
  - Preview de cada post

#### 6. Detalle de Post
- **URL**: `/blog/{slug}`
- **Consume**: `GET /public/blog/{slug}`
- **Muestra**:
  - Contenido completo del post
  - Fecha de publicación
  - Autor
  - Imágenes

#### 7. Documentación Pública
- **URL**: `/docs`
- **Consume**: Ninguno (estático)
- **Muestra**:
  - Guías de uso
  - Metodología GCCA
  - Preguntas frecuentes
  - Documentos descargables (PDFs)

---

### SECCIÓN OPERADOR FICEM (requiere login con rol `operador_ficem`)

#### 8. Dashboard Operador
- **URL**: `/operator/dashboard`
- **Consume**: `GET /operator/stats`
- **Muestra**:
  - Resumen del sistema:
    - Total envíos pendientes de revisión
    - Total empresas activas
    - Total usuarios por rol
    - Alertas y notificaciones
  - Gráficos:
    - Envíos por país
    - Estados de envíos (aprobado, rechazado, pendiente)
    - Actividad reciente

#### 9. Revisión de Envíos
- **URL**: `/operator/revisiones`
- **Consume**:
  - `GET /uploads/pending?approved_by_country=true` - Envíos aprobados por coordinadores país
  - `POST /uploads/{id}/review` - Aprobar/rechazar final
- **Muestra**:
  - Tabla de envíos pendientes de revisión FICEM
  - Filtros: país, empresa, fecha
  - Por cada envío:
    - País y empresa
    - Fecha de envío
    - Estado de validaciones
    - Aprobación del coordinador país
  - Acciones:
    - Ver detalle completo
    - Aprobar y ejecutar cálculos
    - Rechazar con comentarios

#### 10. Gestión de Usuarios
- **URL**: `/operator/usuarios`
- **Consume**:
  - `GET /admin/users` - Lista todos los usuarios
  - `POST /admin/users` - Crear usuario
  - `PUT /admin/users/{id}` - Editar usuario
  - `DELETE /admin/users/{id}` - Eliminar usuario
- **Muestra**:
  - Tabla de usuarios
  - Filtros: rol, país, empresa, estado
  - Por cada usuario:
    - Email
    - Rol (empresa, coordinador_pais, operador_ficem)
    - País
    - Empresa (si aplica)
    - Estado (activo/inactivo)
  - Acciones:
    - Crear nuevo usuario
    - Editar
    - Desactivar/activar
    - Resetear contraseña

#### 11. Gestión de Empresas
- **URL**: `/operator/empresas`
- **Consume**:
  - `GET /admin/empresas` - Lista todas las empresas
  - `POST /admin/empresas` - Crear empresa
  - `PUT /admin/empresas/{id}` - Editar empresa
  - `DELETE /admin/empresas/{id}` - Eliminar empresa
- **Muestra**:
  - Tabla de empresas
  - Filtros: país, perfil_planta
  - Por cada empresa:
    - Nombre
    - País
    - Perfil de planta (integrada, molienda, concreto)
    - Total de plantas
    - Total de envíos
  - Acciones:
    - Crear nueva empresa
    - Editar
    - Ver plantas de la empresa
    - Ver envíos históricos

#### 12. Gestión de Plantas
- **URL**: `/operator/plantas`
- **Consume**:
  - `GET /admin/plantas` - Lista todas las plantas
  - `POST /admin/plantas` - Crear planta
  - `PUT /admin/plantas/{id}` - Editar planta
  - `DELETE /admin/plantas/{id}` - Eliminar planta
- **Muestra**:
  - Tabla de plantas
  - Filtros: país, empresa, tipo
  - Por cada planta:
    - Nombre
    - Empresa
    - País
    - Ubicación (ciudad, coordenadas)
    - Tipo de planta
  - Acciones:
    - Crear nueva planta
    - Editar
    - Ver en mapa

#### 13. Factores de Emisión
- **URL**: `/operator/factores-emision`
- **Consume**:
  - `GET /admin/factores-emision` - Lista factores
  - `PUT /admin/factores-emision` - Actualizar factores
- **Muestra**:
  - Tabla editable de factores de emisión
  - Por país o global
  - Categorías:
    - Combustibles
    - Electricidad
    - Transporte
    - Materias primas
  - Campos:
    - Nombre del factor
    - Valor
    - Unidad
    - País (si aplica)
    - Fuente
    - Última actualización
  - Acciones:
    - Editar valores
    - Agregar nuevo factor
    - Importar desde Excel
    - Exportar a Excel

#### 14. Bandas GCCA
- **URL**: `/operator/bandas-gcca`
- **Consume**:
  - `GET /admin/bandas-gcca` - Obtener bandas actuales
  - `PUT /admin/bandas-gcca` - Actualizar límites
- **Muestra**:
  - Tabla editable de límites de bandas GCCA
  - Por resistencia de concreto
  - Visualización gráfica de bandas (AA, A, B, C, D, E, F)
  - Campos:
    - Resistencia (MPa)
    - Límite AA
    - Límite A
    - Límite B
    - ... hasta F
  - Acciones:
    - Editar límites
    - Recalcular bandas de todos los envíos procesados

#### 15. Explorador de Datos
- **URL**: `/operator/data-explorer`
- **Consume**:
  - `GET /data/query` - Ejecutar consulta personalizada
  - `GET /data/stats` - Estadísticas generales
- **Muestra**:
  - Editor SQL (con autocompletado)
  - Lista de tablas disponibles
  - Resultados en tabla
  - Opciones de visualización:
    - Tabla
    - Gráfico de barras
    - Gráfico de líneas
    - Scatter plot
  - Acciones:
    - Ejecutar query
    - Guardar query favorita
    - Exportar resultados

#### 16. Descarga Masiva
- **URL**: `/operator/export`
- **Consume**: `GET /data/export`
- **Muestra**:
  - Formulario de selección:
    - Rango de fechas
    - País (todos o específico)
    - Empresa (todas o específica)
    - Tipo de datos (envíos, resultados, empresas, plantas)
    - Formato (CSV, Excel, JSON)
  - Acciones:
    - Generar exportación
    - Descargar archivo
    - Ver historial de exportaciones

#### 17. Herramientas IA
- **URL**: `/operator/ai`
- **Consume**:
  - `POST /ai/chat` - Chat con knowledge-api
  - `GET /ai/predictions` - Predicciones
- **Muestra**:
  - Chat interactivo:
    - Preguntas sobre datos
    - Análisis automático
    - Recomendaciones
  - Predicciones:
    - Tendencias futuras
    - Detección de anomalías
    - Análisis de patrones
  - Acciones:
    - Enviar pregunta
    - Generar reporte con IA
    - Ejecutar análisis predictivo

#### 18. Benchmarking Regional
- **URL**: `/operator/benchmarking`
- **Consume**: `GET /benchmarking/regional`
- **Muestra**:
  - Comparativa entre países:
    - Promedio de emisiones A1-A3 por país
    - Distribución de bandas GCCA por país
    - Percentiles P10, P50, P90
  - Gráficos:
    - Mapa de calor por país
    - Boxplots comparativos
    - Evolución temporal por país
  - Filtros:
    - Rango de fechas
    - Tipo de planta
    - Resistencia de concreto

#### 19. Gestión de Blog
- **URL**: `/operator/blog`
- **Consume**:
  - `GET /admin/blog` - Lista posts
  - `POST /admin/blog` - Crear post
  - `PUT /admin/blog/{id}` - Editar post
  - `DELETE /admin/blog/{id}` - Eliminar post
- **Muestra**:
  - Lista de posts (publicados y borradores)
  - Por cada post:
    - Título
    - Autor
    - Fecha de publicación
    - Estado (borrador, publicado)
  - Editor de posts:
    - Título
    - Slug (URL)
    - Contenido (Markdown o WYSIWYG)
    - Imágenes
    - Categoría
    - País relacionado (opcional)
  - Acciones:
    - Crear nuevo post
    - Editar
    - Publicar/despublicar
    - Eliminar

---

## Resumen de Páginas

| Sección | Total Páginas | Páginas |
|---------|---------------|---------|
| **Pública** | 7 | Home, About, Dashboard, Países, Blog, Post, Docs |
| **Operador FICEM** | 12 | Dashboard, Revisiones, Usuarios, Empresas, Plantas, Factores, Bandas, Explorador, Export, IA, Benchmarking, Blog |
| **TOTAL** | 19 | |

---

## Stack Tecnológico Recomendado

```
- Next.js 14+ (App Router)
- TypeScript
- TailwindCSS
- shadcn/ui (componentes)
- Recharts (gráficos)
- React Query (cache de API)
- Zod (validación)
- axios (HTTP client)
- react-markdown (para blog)
```

## Estructura del Proyecto

```
4c-ficem-web/
├── app/
│   ├── (public)/              # Rutas públicas
│   │   ├── page.tsx           # Home
│   │   ├── about/
│   │   ├── dashboard/
│   │   ├── paises/
│   │   ├── blog/
│   │   │   ├── page.tsx       # Lista
│   │   │   └── [slug]/        # Detalle
│   │   └── docs/
│   ├── (operator)/            # Rutas operador
│   │   ├── dashboard/
│   │   ├── revisiones/
│   │   ├── usuarios/
│   │   ├── empresas/
│   │   ├── plantas/
│   │   ├── factores-emision/
│   │   ├── bandas-gcca/
│   │   ├── data-explorer/
│   │   ├── export/
│   │   ├── ai/
│   │   ├── benchmarking/
│   │   └── blog/
│   └── login/                 # Autenticación
├── components/
│   ├── ui/                    # shadcn components
│   ├── charts/
│   ├── tables/
│   ├── forms/
│   └── layouts/
├── lib/
│   ├── api/                   # Cliente API
│   ├── auth/                  # JWT handling
│   └── utils/
└── types/                     # TypeScript types
```

---

## Autenticación

**Flujo:**
1. Usuario accede a `/login`
2. Ingresa email y contraseña
3. Frontend hace `POST /auth/login` a 4c-ficem-core
4. Backend retorna JWT
5. Frontend guarda JWT en localStorage/cookie
6. Todas las requests a `/operator/*` incluyen header:
   ```
   Authorization: Bearer {jwt_token}
   ```

**Middleware de Next.js:**
- Rutas `/operator/*` requieren JWT válido con rol `operador_ficem`
- Si no hay JWT o rol incorrecto → redirect a `/login`

---

## Próximos Pasos

1. ⏭️ Crear repositorio `4c-ficem-web`
2. ⏭️ Setup Next.js + TypeScript + TailwindCSS
3. ⏭️ Implementar páginas públicas (1-7)
4. ⏭️ Implementar autenticación
5. ⏭️ Implementar páginas operador (8-19)

---

**Última actualización**: 2025-12-07
