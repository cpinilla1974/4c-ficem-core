# Metodología de Trabajo - 4C FICEM CORE

## Contexto del Proyecto

**4C FICEM CORE** es el backend centralizado del sistema de cálculo de huella de carbono para la industria cementera y de concreto en Latinoamérica.

**Origen**: Extraído de `latam-3c/v1` como parte de la arquitectura de dos aplicaciones separadas (decisión 2025-12-06).

**Documentación centralizada**: Toda la documentación técnica vive en el repo `latam-3c`:
- Plan de arquitectura: `docs/1-tecnica/00-plan-etapa-1-dos-apps.md`
- Especificación técnica: `docs/1-tecnica/01-arquitectura-ficem-4c.md`
- Decisión de separación: `docs/3-sesiones/sesion_2025-12-06.md`
- Documentación técnica completa: `latam-3c/docs/1-tecnica/`

**Acceso a documentación**:
```
https://github.com/cpinilla1974/latam-3c/tree/main/docs
```

---

## Responsabilidades de FICEM CORE

- Motor de cálculos A1-A3 (Clinker, Cemento, Concreto)
- Validador de datos Excel
- Clasificador GCCA (bandas A-G, AA-F)
- Base de datos centralizada (SQLite → PostgreSQL)
- Interfaz Streamlit para operador FICEM
- APIs REST para consumo por otros frontends
- Integración con microservicios de knowledge-api

---

## Principios de Documentación

1. **Solo lo esencial**: Documentar únicamente lo discutido y acordado
2. **Bloques de construcción**: Cada documento debe ser necesario y suficiente para construir
3. **Sin opciones**: Las opciones son para discusión en pantalla, no para documentar
4. **Conciso**: Evitar documentos extensos, ir al punto

### Qué NO documentar
- Listas de opciones
- Planes tentativos sin discutir
- Recomendaciones no solicitadas
- Información redundante o especulativa

### Qué SÍ documentar
- Decisiones técnicas tomadas (en sesiones/)
- Estructuras de datos
- Especificaciones funcionales
- Cambios de arquitectura
- Integraciones con otros servicios

---

## Política de Comunicación

- NUNCA usar jerga argentina o regionalismos (ej: "tenés", "vos", etc.)
- SIEMPRE usar español neutro profesional
- Usar tuteo neutro ("tienes", "tú") según contexto

---

## Política de Commits

- NUNCA incluir a Claude como autor del commit
- NO usar las líneas "🤖 Generated with Claude Code" ni "Co-Authored-By: Claude"
- Los commits deben aparecer como del usuario únicamente

---

## Gestión de Sesiones de Trabajo

### Al iniciar una sesión:
1. Revisar documentación en `latam-3c/docs/` para contexto
2. Si hay decisiones nuevas, documentarlas en `latam-3c/docs/3-sesiones/sesion_YYYY-MM-DD.md`
3. Mantener este repo enfocado en código y cambios técnicos

### Al finalizar una sesión:
1. Si hubo cambios significativos, crear/actualizar sesión en latam-3c
2. Hacer commit con descripción clara
3. Guardar cambios antes de terminar

---

## Iniciar la Aplicación

Cuando se diga "inicia la aplicación":

1. **Verificar entorno virtual**:
   - Si no existe: `python3 -m venv venv_ficem`
   - Activar: `source venv_ficem/bin/activate`

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar Streamlit**:
   ```bash
   streamlit run app.py --server.port 8501
   ```

4. **Acceso**: http://localhost:8501

---

## Stack Tecnológico

- **Frontend**: Streamlit (presentación operador FICEM)
- **Backend Logic**: Python (módulos de cálculo, validación, clasificación)
- **Database**: SQLite (desarrollo) → PostgreSQL (producción)
- **APIs**: FastAPI (futuro para exponer como microservicios)
- **Dependencias**: pandas, openpyxl, xlsxwriter, SQLAlchemy, plotly

---

## Estructura de Carpetas

```
ficem-core/
├── app.py                      # Interfaz Streamlit operador
├── requirements.txt
├── modules/                    # Lógica de negocio
│   ├── calculator.py          # Motor A1-A3
│   ├── validator.py           # Validaciones
│   ├── classifier.py          # Clasificación GCCA
│   └── ...
├── database/                   # Modelos y acceso datos
│   ├── models.py
│   ├── repository.py
│   └── latam4c.db
├── api/                        # APIs REST (futuro)
├── config/                     # Configuración (factores, bandas)
├── pages/                      # Páginas Streamlit
├── ai_modules/                 # Módulos IA (RAG, ML, análisis)
├── services/                   # Servicios de negocio
└── data/                       # Datos estáticos y BD
```

---

## Próximos Pasos Iniciales

1. Eliminar referencias a `vector_store` local (migraron a knowledge-api)
2. Implementar cliente REST para consumir microservicios de knowledge-api
3. Refactor de páginas que usaban vector_store
4. Crear APIs REST para exposición de funcionalidades
5. Sincronizar estructura con plan en latam-3c

---

**Última actualización**: 2025-12-06
**Versión**: 1.0
