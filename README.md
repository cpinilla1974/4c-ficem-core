# Calculadora País 4C - v1

Sistema de Huella de Carbono para la Industria Cementera LATAM - Etapa 1

## Instalación

### 1. Activar entorno virtual

```bash
cd /home/cpinilla/projects/latam-3c
source venv_v1/bin/activate
```

### 2. Instalar dependencias (si es necesario)

```bash
pip install -r v1/requirements.txt
```

### 3. Inicializar base de datos (primera vez)

```bash
cd v1
python init_db.py
```

## Ejecutar la aplicación

```bash
cd v1
streamlit run app.py
```

La aplicación estará disponible en: http://localhost:8501

## Estructura del Proyecto

```
v1/
├── app.py                          # Aplicación principal
├── requirements.txt                # Dependencias
├── init_db.py                      # Script inicialización BD
├── config/                         # Configuraciones
├── modules/                        # Módulos lógica de negocio
├── database/                       # Modelos y repositorios BD
│   ├── __init__.py
│   ├── models.py                   # Modelos SQLAlchemy
│   └── repository.py               # Acceso a datos
├── pages/                          # Páginas Streamlit (23)
│   ├── dashboard/                  # 3 páginas
│   │   ├── 01_resumen_consolidado.py
│   │   ├── 02_distribucion_bandas_gcca.py
│   │   └── 03_historico_timeline.py
│   ├── empresas/                   # 3 páginas
│   │   ├── 01_listado_empresas.py
│   │   ├── 02_registro_empresa.py
│   │   └── 03_detalle_empresa.py
│   ├── calculadoras_3c/            # 4 páginas (PRIORIDAD FASE 1)
│   │   ├── 01_importar_3c.py
│   │   ├── 02_validar_importacion.py
│   │   ├── 03_calcular.py
│   │   └── 04_resultados_3c.py
│   ├── excel_tradicional/          # 4 páginas
│   │   ├── 01_generar_templates.py
│   │   ├── 02_cargar_excel.py
│   │   ├── 03_corregir_errores.py
│   │   └── 04_procesar.py
│   ├── analisis/                   # 4 páginas
│   │   ├── 01_curvas_co2_resistencia.py
│   │   ├── 02_comparativa_pais.py
│   │   ├── 03_analisis_bandas.py
│   │   └── 04_tendencias_temporales.py
│   ├── reportes/                   # 3 páginas
│   │   ├── 01_reporte_individual.py
│   │   ├── 02_reporte_consolidado.py
│   │   └── 03_exportar_datos.py
│   └── hoja_ruta/                  # 3 páginas
│       ├── 01_estado_implementacion.py
│       ├── 02_checklist_entregables.py
│       └── 03_empresas_piloto.py
└── data/
    └── latam4c.db                  # Base de datos SQLite
```

## Navegación del Sistema

### 📊 Dashboard (3 páginas)
- Resumen Consolidado: Métricas generales del sistema
- Distribución Bandas GCCA: Clasificación por bandas
- Histórico Timeline: Evolución temporal

### 🏭 Empresas (3 páginas)
- Listado Empresas: Tabla con todas las empresas
- Registro Nueva Empresa: Formulario de alta
- Detalle Empresa: Vista individual con historial

### 🔧 Calculadoras 3C (4 páginas) - PRIORIDAD FASE 1
- Importar desde 3C: Upload desde calculadora corporativa
- Validar Importación: Verificación automática
- Calcular: Motor de cálculos A1-A3
- Resultados 3C: Visualización emisiones + banda GCCA

### 📋 Excel Tradicional (4 páginas)
- Generar Templates: Descarga Excel personalizado
- Cargar Excel Manual: Upload y validación
- Corregir Errores: Feedback específico
- Procesar: Cálculo tras validación

### 📈 Análisis y Visualizaciones (4 páginas)
- Curvas CO₂ vs Resistencia: Benchmarking concretos
- Comparativa por País: Percentiles P10-P90
- Análisis por Bandas: Distribución GCCA
- Tendencias Temporales: Evolución multi-año

### 📄 Reportes (3 páginas)
- Generar Reporte Individual: PDF por empresa
- Reporte Consolidado País: Agregación anónima
- Exportar Datos: CSV/Excel

### 🛣️ Hoja de Ruta (3 páginas)
- Estado Implementación: Fases 1-4 progreso
- Checklist Entregables: Tareas por fase
- Empresas Piloto: Tracking validación

## Base de Datos

### Tabla: empresas
- id (PK)
- nombre
- pais
- perfil_planta (integrada/molienda/concreto)
- contacto
- email
- created_at
- updated_at

**Datos de prueba:** 3 empresas (Colombia, Perú, Chile)

## Estado Actual

✅ Estructura completa de carpetas
✅ Entorno virtual configurado (venv_v1)
✅ Base de datos SQLite creada y conectada
✅ 23 páginas con títulos y descripciones
✅ Navegación funcional entre páginas
✅ Menú lateral colapsable Streamlit

⏳ Lógica de negocio (Fase 1-4 según planificación)

## Tecnologías

- **Python**: 3.12
- **Streamlit**: 1.51.0
- **SQLAlchemy**: 2.0.44
- **Pandas**: 2.3.3
- **Plotly**: 6.4.0
- **OpenPyXL**: 3.1.5
- **XlsxWriter**: 3.2.9

## Próximos Pasos

1. Implementar generador de templates Excel (Fase 1)
2. Desarrollar upgrade calculadoras 3C (Fase 1)
3. Construir motor de cálculos A1-A3 (Fase 2)
4. Implementar clasificación GCCA (Fase 2)
5. Desarrollar visualizaciones y reportes (Fase 3)

---

**Versión:** 1.0 - MVP
**Fecha:** 2025-11-13
**Etapa:** 1 - Operador Centralizado
