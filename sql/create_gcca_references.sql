-- ============================================================================
-- Tablas de Referencia GCCA para Benchmarking Multidimensional
-- ============================================================================
-- Diseño flexible que permite clasificar referencias por múltiples dimensiones
-- Basado en: GCCA GNR Concrete Pilot Project Report on KPIs (Julio 2020)
-- ============================================================================

-- TABLA 1: Dimensiones de Clasificación
-- Define las diferentes formas de clasificar las referencias
CREATE TABLE IF NOT EXISTS ref_dimensiones (
    id SERIAL PRIMARY KEY,
    dimension VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    nivel_jerarquia INTEGER DEFAULT 1,
    dimension_padre_id INTEGER REFERENCES ref_dimensiones(id),
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_dimension_no_circular CHECK (id != dimension_padre_id)
);

-- TABLA 2: Valores de Dimensiones
-- Los valores específicos para cada dimensión (ej: "Mundial", "Europa", etc.)
CREATE TABLE IF NOT EXISTS ref_valores_dimension (
    id SERIAL PRIMARY KEY,
    dimension_id INTEGER NOT NULL REFERENCES ref_dimensiones(id) ON DELETE CASCADE,
    valor VARCHAR(200) NOT NULL,
    codigo VARCHAR(50),
    orden_visualizacion INTEGER DEFAULT 0,
    metadata JSONB,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dimension_id, valor)
);

-- TABLA 3: Categorías de KPIs
-- Agrupa los KPIs por tipo (Energía, Transporte, Huella CO2, etc.)
CREATE TABLE IF NOT EXISTS ref_categorias_kpi (
    id SERIAL PRIMARY KEY,
    categoria VARCHAR(200) NOT NULL UNIQUE,
    descripcion TEXT,
    unidad_base VARCHAR(50),
    orden_visualizacion INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 4: KPIs (Indicadores)
-- Define cada KPI específico dentro de una categoría
CREATE TABLE IF NOT EXISTS ref_kpis (
    id SERIAL PRIMARY KEY,
    categoria_id INTEGER NOT NULL REFERENCES ref_categorias_kpi(id) ON DELETE CASCADE,
    kpi_nombre VARCHAR(200) NOT NULL,
    kpi_codigo VARCHAR(100) UNIQUE,
    descripcion TEXT,
    unidad VARCHAR(50) NOT NULL,
    tipo_metrica VARCHAR(50), -- 'continuo', 'discreto', 'porcentaje', 'ratio'
    formula TEXT,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(categoria_id, kpi_nombre)
);

-- TABLA 5: Referencias GCCA (Tabla Principal)
-- Almacena los valores de referencia con sus dimensiones
CREATE TABLE IF NOT EXISTS ref_gcca_benchmarks (
    id SERIAL PRIMARY KEY,
    kpi_id INTEGER NOT NULL REFERENCES ref_kpis(id) ON DELETE CASCADE,
    fuente VARCHAR(500) NOT NULL,
    año_referencia INTEGER,

    -- Estadísticas
    valor_minimo NUMERIC(12,4),
    valor_promedio NUMERIC(12,4),
    valor_maximo NUMERIC(12,4),
    desviacion_estandar NUMERIC(12,4),
    mediana NUMERIC(12,4),

    -- Percentiles
    percentil_10 NUMERIC(12,4),
    percentil_25 NUMERIC(12,4),
    percentil_75 NUMERIC(12,4),
    percentil_90 NUMERIC(12,4),

    -- Metadata adicional
    cobertura_porcentaje NUMERIC(5,2),
    num_muestras INTEGER,
    observaciones TEXT,
    metadata JSONB,

    -- Control
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 6: Asociación Referencias-Dimensiones (Tabla Puente)
-- Permite asociar cada referencia con múltiples dimensiones
CREATE TABLE IF NOT EXISTS ref_benchmark_dimensiones (
    id SERIAL PRIMARY KEY,
    benchmark_id INTEGER NOT NULL REFERENCES ref_gcca_benchmarks(id) ON DELETE CASCADE,
    valor_dimension_id INTEGER NOT NULL REFERENCES ref_valores_dimension(id) ON DELETE CASCADE,
    peso NUMERIC(5,4) DEFAULT 1.0, -- Permite ponderación si es necesario
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(benchmark_id, valor_dimension_id)
);

-- TABLA 7: Rangos Interpretativos
-- Define rangos de interpretación para cada KPI (ej: bueno, regular, crítico)
CREATE TABLE IF NOT EXISTS ref_rangos_interpretativos (
    id SERIAL PRIMARY KEY,
    kpi_id INTEGER NOT NULL REFERENCES ref_kpis(id) ON DELETE CASCADE,
    nombre_rango VARCHAR(100) NOT NULL, -- 'excelente', 'bueno', 'regular', 'crítico'
    valor_min NUMERIC(12,4),
    valor_max NUMERIC(12,4),
    color_hex VARCHAR(7), -- Para visualización
    descripcion TEXT,
    aplicable_a_dimension_id INTEGER REFERENCES ref_dimensiones(id),
    orden INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- ============================================================================

CREATE INDEX idx_benchmark_kpi ON ref_gcca_benchmarks(kpi_id);
CREATE INDEX idx_benchmark_activo ON ref_gcca_benchmarks(activo) WHERE activo = TRUE;
CREATE INDEX idx_benchmark_año ON ref_gcca_benchmarks(año_referencia);

CREATE INDEX idx_benchmark_dim_benchmark ON ref_benchmark_dimensiones(benchmark_id);
CREATE INDEX idx_benchmark_dim_valor ON ref_benchmark_dimensiones(valor_dimension_id);

CREATE INDEX idx_valores_dimension_dim ON ref_valores_dimension(dimension_id);
CREATE INDEX idx_valores_dimension_activo ON ref_valores_dimension(activo) WHERE activo = TRUE;

CREATE INDEX idx_kpis_categoria ON ref_kpis(categoria_id);
CREATE INDEX idx_kpis_codigo ON ref_kpis(kpi_codigo);
CREATE INDEX idx_kpis_activo ON ref_kpis(activo) WHERE activo = TRUE;

CREATE INDEX idx_rangos_kpi ON ref_rangos_interpretativos(kpi_id);

-- ============================================================================
-- VISTAS ÚTILES PARA CONSULTAS
-- ============================================================================

-- Vista que combina referencias con todas sus dimensiones
CREATE OR REPLACE VIEW v_benchmarks_completos AS
SELECT
    rb.id AS benchmark_id,
    rk.kpi_codigo,
    rk.kpi_nombre,
    rc.categoria,
    rb.fuente,
    rb.año_referencia,
    rb.valor_minimo,
    rb.valor_promedio,
    rb.valor_maximo,
    rb.desviacion_estandar,
    rk.unidad,
    rb.cobertura_porcentaje,
    rb.num_muestras,
    rb.observaciones,
    -- Agregamos dimensiones como JSON
    json_agg(
        json_build_object(
            'dimension', rd.dimension,
            'valor', rvd.valor,
            'codigo', rvd.codigo
        )
    ) AS dimensiones
FROM ref_gcca_benchmarks rb
JOIN ref_kpis rk ON rb.kpi_id = rk.id
JOIN ref_categorias_kpi rc ON rk.categoria_id = rc.id
LEFT JOIN ref_benchmark_dimensiones rbd ON rb.id = rbd.benchmark_id
LEFT JOIN ref_valores_dimension rvd ON rbd.valor_dimension_id = rvd.id
LEFT JOIN ref_dimensiones rd ON rvd.dimension_id = rd.id
WHERE rb.activo = TRUE
GROUP BY rb.id, rk.kpi_codigo, rk.kpi_nombre, rc.categoria, rb.fuente,
         rb.año_referencia, rb.valor_minimo, rb.valor_promedio, rb.valor_maximo,
         rb.desviacion_estandar, rk.unidad, rb.cobertura_porcentaje,
         rb.num_muestras, rb.observaciones;

-- Vista simplificada para comparaciones rápidas
CREATE OR REPLACE VIEW v_benchmarks_por_region AS
SELECT
    rc.categoria,
    rk.kpi_nombre,
    rvd.valor AS region,
    rb.valor_promedio,
    rb.valor_minimo,
    rb.valor_maximo,
    rk.unidad
FROM ref_gcca_benchmarks rb
JOIN ref_kpis rk ON rb.kpi_id = rk.id
JOIN ref_categorias_kpi rc ON rk.categoria_id = rc.id
JOIN ref_benchmark_dimensiones rbd ON rb.id = rbd.benchmark_id
JOIN ref_valores_dimension rvd ON rbd.valor_dimension_id = rvd.id
JOIN ref_dimensiones rd ON rvd.dimension_id = rd.id
WHERE rb.activo = TRUE AND rd.dimension = 'Region Geografica'
ORDER BY rc.categoria, rk.kpi_nombre, rvd.orden_visualizacion;

-- ============================================================================
-- COMENTARIOS EN TABLAS
-- ============================================================================

COMMENT ON TABLE ref_dimensiones IS 'Define las dimensiones de clasificación (ej: Región Geográfica, Tipo de Clima, Nivel de Desarrollo)';
COMMENT ON TABLE ref_valores_dimension IS 'Valores específicos para cada dimensión (ej: Mundial, Europa, América del Norte)';
COMMENT ON TABLE ref_categorias_kpi IS 'Categorías de KPIs (Energía, Transporte, Huella CO2, etc.)';
COMMENT ON TABLE ref_kpis IS 'Indicadores específicos dentro de cada categoría';
COMMENT ON TABLE ref_gcca_benchmarks IS 'Valores de referencia GCCA con estadísticas completas';
COMMENT ON TABLE ref_benchmark_dimensiones IS 'Asociación muchos-a-muchos entre referencias y dimensiones';
COMMENT ON TABLE ref_rangos_interpretativos IS 'Rangos de interpretación para cada KPI (bueno, regular, crítico)';

COMMENT ON COLUMN ref_gcca_benchmarks.metadata IS 'JSON con información adicional flexible';
COMMENT ON COLUMN ref_valores_dimension.metadata IS 'JSON para propiedades adicionales del valor';
