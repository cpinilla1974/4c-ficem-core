-- ============================================================================
-- Inserción de Datos de Referencia GCCA
-- ============================================================================
-- Fuente: GCCA GNR Concrete Pilot Project Report on KPIs (Julio 2020)
-- ============================================================================

-- PASO 1: Insertar Dimensiones de Clasificación
-- ============================================================================

INSERT INTO ref_dimensiones (dimension, descripcion, nivel_jerarquia, dimension_padre_id) VALUES
('Region Geografica', 'Clasificación por región geográfica mundial', 1, NULL),
('Tipo de Clima', 'Clasificación climática', 1, NULL),
('Nivel de Desarrollo', 'Nivel de desarrollo económico', 1, NULL),
('Tipo de Metrica', 'Clasificación del tipo de métrica estadística', 1, NULL)
ON CONFLICT (dimension) DO NOTHING;

-- PASO 2: Insertar Valores de Dimensiones
-- ============================================================================

-- Regiones Geográficas
INSERT INTO ref_valores_dimension (dimension_id, valor, codigo, orden_visualizacion) VALUES
((SELECT id FROM ref_dimensiones WHERE dimension = 'Region Geografica'), 'Mundial', 'WORLD', 1),
((SELECT id FROM ref_dimensiones WHERE dimension = 'Region Geografica'), 'Europa', 'EU', 2),
((SELECT id FROM ref_dimensiones WHERE dimension = 'Region Geografica'), 'América del Norte', 'NA', 3),
((SELECT id FROM ref_dimensiones WHERE dimension = 'Region Geografica'), 'Sudamérica', 'SA', 4),
((SELECT id FROM ref_dimensiones WHERE dimension = 'Region Geografica'), 'Asia', 'AS', 5),
((SELECT id FROM ref_dimensiones WHERE dimension = 'Region Geografica'), 'Oceanía', 'OC', 6),
((SELECT id FROM ref_dimensiones WHERE dimension = 'Region Geografica'), 'África', 'AF', 7)
ON CONFLICT (dimension_id, valor) DO NOTHING;

-- Tipos de Clima
INSERT INTO ref_valores_dimension (dimension_id, valor, codigo, orden_visualizacion) VALUES
((SELECT id FROM ref_dimensiones WHERE dimension = 'Tipo de Clima'), 'Templado', 'TEMP', 1),
((SELECT id FROM ref_dimensiones WHERE dimension = 'Tipo de Clima'), 'Frío', 'COLD', 2),
((SELECT id FROM ref_dimensiones WHERE dimension = 'Tipo de Clima'), 'Subtropical', 'SUBT', 3),
((SELECT id FROM ref_dimensiones WHERE dimension = 'Tipo de Clima'), 'Tropical', 'TROP', 4)
ON CONFLICT (dimension_id, valor) DO NOTHING;

-- PASO 3: Insertar Categorías de KPIs
-- ============================================================================

INSERT INTO ref_categorias_kpi (categoria, descripcion, unidad_base, orden_visualizacion) VALUES
('Energía', 'Proceso energético de producción de concreto', 'kWh/m³', 1),
('Transporte', 'Distribución y logística de concreto', 'km', 2),
('Combustible', 'Consumo de combustible en transporte', 'km/l', 3),
('Huella CO2', 'Emisiones de gases de efecto invernadero', 'kg CO2/m³', 4)
ON CONFLICT (categoria) DO NOTHING;

-- PASO 4: Insertar KPIs Específicos
-- ============================================================================

INSERT INTO ref_kpis (categoria_id, kpi_nombre, kpi_codigo, descripcion, unidad, tipo_metrica) VALUES
-- Energía
((SELECT id FROM ref_categorias_kpi WHERE categoria = 'Energía'),
 'Energía Total de Producción', 'ENERGIA_TOTAL',
 'Energía total consumida en producción de concreto', 'kWh/m³', 'continuo'),

((SELECT id FROM ref_categorias_kpi WHERE categoria = 'Energía'),
 'Energía Eléctrica', 'ENERGIA_ELECTRICA',
 'Consumo de electricidad en producción', 'kWh/m³', 'continuo'),

((SELECT id FROM ref_categorias_kpi WHERE categoria = 'Energía'),
 'Energía Térmica', 'ENERGIA_TERMICA',
 'Consumo de energía térmica en producción', 'MJ/m³', 'continuo'),

-- Transporte
((SELECT id FROM ref_categorias_kpi WHERE categoria = 'Transporte'),
 'Distancia de Distribución', 'DISTANCIA_DISTRIBUCION',
 'Distancia promedio de entrega de concreto', 'km', 'continuo'),

((SELECT id FROM ref_categorias_kpi WHERE categoria = 'Transporte'),
 'Volumen por Entrega', 'VOLUMEN_ENTREGA',
 'Volumen promedio de concreto por entrega', 'm³', 'continuo'),

-- Combustible
((SELECT id FROM ref_categorias_kpi WHERE categoria = 'Combustible'),
 'Eficiencia de Combustible', 'EFICIENCIA_COMBUSTIBLE',
 'Eficiencia de combustible de camiones', 'km/l', 'continuo'),

((SELECT id FROM ref_categorias_kpi WHERE categoria = 'Combustible'),
 'Consumo Específico', 'CONSUMO_ESPECIFICO',
 'Consumo específico de combustible por volumen y distancia', 'l/km/m³', 'continuo')

ON CONFLICT (kpi_codigo) DO NOTHING;

-- PASO 5: Insertar Referencias GCCA - ENERGÍA TOTAL
-- ============================================================================

-- Mundial
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'ENERGIA_TOTAL'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    1.2, 10.0, 64.0, 11.0,
    100,
    '~80% de valores entre 1-6 kWh/m³. Promedio influenciado por regiones de alta producción en América del Norte'
) RETURNING id AS mundial_energia_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:mundial_energia_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'WORLD'));

-- Europa
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'ENERGIA_TOTAL'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    1.8, 4.4, 16.0, 3.0,
    100,
    '~80% de valores entre 1-5 kWh/m³. Costos operativos en climas fríos pueden explicar brecha máxima'
) RETURNING id AS europa_energia_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:europa_energia_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'EU'));

-- América del Norte
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'ENERGIA_TOTAL'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    1.2, 21.4, 64.0, 19.0,
    97,
    '~2x promedio mundial, ~5x promedio europeo. Costos operativos en clima frío (especialmente Canadá). ~90% de valores entre 1-35 kWh/m³'
) RETURNING id AS na_energia_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:na_energia_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'NA'));

-- PASO 6: ENERGÍA ELÉCTRICA
-- ============================================================================

-- Mundial - Electricidad
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'ENERGIA_ELECTRICA'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    1.2, 4.2, 8.2, 1.5,
    79,
    '~80% electricidad: 2-6 kWh/m³'
) RETURNING id AS mundial_elec_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:mundial_elec_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'WORLD'));

-- Europa - Electricidad
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'ENERGIA_ELECTRICA'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    2.3, 3.6, 5.5, 0.9,
    58,
    '~80% electricidad: 2-4 kWh/m³. Menor variabilidad que mundo'
) RETURNING id AS europa_elec_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:europa_elec_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'EU'));

-- América del Norte - Electricidad
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'ENERGIA_ELECTRICA'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    1.2, 5.2, 8.6, 2.01,
    100,
    '~80% electricidad: 2-6 kWh/m³'
) RETURNING id AS na_elec_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:na_elec_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'NA'));

-- PASO 7: ENERGÍA TÉRMICA
-- ============================================================================

-- Mundial - Térmica
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'ENERGIA_TERMICA'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    0, 29, 210, 43,
    76,
    '~85% térmica: 0-18 MJ/m³. Promedio térmico influenciado por sitios de América del Norte'
) RETURNING id AS mundial_term_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:mundial_term_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'WORLD'));

-- Europa - Térmica
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'ENERGIA_TERMICA'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    0, 5.7, 53, 13,
    58,
    '~70% térmica: 0-4 MJ/m³. Menor variabilidad que mundo'
) RETURNING id AS europa_term_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:europa_term_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'EU'));

-- América del Norte - Térmica
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'ENERGIA_TERMICA'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    0, 60.3, 210, 68,
    97,
    '~60% térmica: 4-27 MJ/m³. Energía térmica significativamente más alta (climas fríos)'
) RETURNING id AS na_term_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:na_term_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'NA'));

-- PASO 8: TRANSPORTE - DISTANCIA
-- ============================================================================

-- Mundial
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'DISTANCIA_DISTRIBUCION'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    5, 16, 61, 9,
    100,
    '~80% valores: 10-30 km. Varía según red de distribución de participantes'
) RETURNING id AS mundial_dist_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:mundial_dist_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'WORLD'));

-- Europa
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'DISTANCIA_DISTRIBUCION'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    6.8, 12, 26, 5,
    100,
    '~75% valores: 10-30 km. No varía según ancho geográfico de países'
) RETURNING id AS europa_dist_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:europa_dist_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'EU'));

-- América del Norte
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'DISTANCIA_DISTRIBUCION'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    8.6, 23, 29, 7,
    100,
    '~2x promedio europeo (23 km vs 12 km). ~70% valores: 8-20 km. Mayor distancia por geografía de continente'
) RETURNING id AS na_dist_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:na_dist_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'NA'));

-- PASO 9: TRANSPORTE - VOLUMEN
-- ============================================================================

-- Mundial
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'VOLUMEN_ENTREGA'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    4.5, 6.6, 10, 1,
    100,
    '~80% valores: 4.5-8 m³/entrega. Mayoría camiones óptimamente cargados (~8 m³ capacidad)'
) RETURNING id AS mundial_vol_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:mundial_vol_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'WORLD'));

-- Europa
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'VOLUMEN_ENTREGA'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    4.6, 7, 10, 1,
    100,
    '~80% valores: 4.5-8 m³/entrega'
) RETURNING id AS europa_vol_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:europa_vol_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'EU'));

-- América del Norte
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, num_muestras, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'VOLUMEN_ENTREGA'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    5.5, 6.4, 8, 1,
    60, NULL,
    '~80% valores: 5.5-7 m³/entrega. Casi óptimamente cargados'
) RETURNING id AS na_vol_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:na_vol_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'NA'));

-- PASO 10: COMBUSTIBLE - EFICIENCIA
-- ============================================================================

-- Mundial
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'EFICIENCIA_COMBUSTIBLE'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    0.1, 1.15, 2.6, 1.0,
    100,
    'Combustible: Diesel (todos participantes). ~75% eficiencia: 0-2 km/l. ~24% datos estimados (2.6 km/l estándar)'
) RETURNING id AS mundial_efic_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:mundial_efic_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'WORLD'));

-- PASO 11: COMBUSTIBLE - CONSUMO ESPECÍFICO
-- ============================================================================

-- Mundial
INSERT INTO ref_gcca_benchmarks (
    kpi_id, fuente, año_referencia,
    valor_minimo, valor_promedio, valor_maximo, desviacion_estandar,
    cobertura_porcentaje, observaciones
) VALUES (
    (SELECT id FROM ref_kpis WHERE kpi_codigo = 'CONSUMO_ESPECIFICO'),
    'GCCA GNR Concrete Pilot Project Report on KPIs',
    2020,
    0.5, 4.8, 13.8, 3.0,
    100,
    '~80% consumo específico: 1-5 l/km/m³'
) RETURNING id AS mundial_cons_id \gset

INSERT INTO ref_benchmark_dimensiones (benchmark_id, valor_dimension_id) VALUES
(:mundial_cons_id, (SELECT id FROM ref_valores_dimension WHERE codigo = 'WORLD'));

-- ============================================================================
-- INSERTAR RANGOS INTERPRETATIVOS
-- ============================================================================

-- Para Energía Total (LATAM)
INSERT INTO ref_rangos_interpretativos (
    kpi_id, nombre_rango, valor_min, valor_max, color_hex, descripcion, orden
) VALUES
((SELECT id FROM ref_kpis WHERE kpi_codigo = 'ENERGIA_TOTAL'), 'Optimista', NULL, 8, '#00C853', 'Consumo energético óptimo', 1),
((SELECT id FROM ref_kpis WHERE kpi_codigo = 'ENERGIA_TOTAL'), 'Objetivo Realista', 8, 12, '#4CAF50', 'Rango objetivo considerando climas variados LATAM', 2),
((SELECT id FROM ref_kpis WHERE kpi_codigo = 'ENERGIA_TOTAL'), 'Aceptable', 12, 16, '#FFC107', 'Consumo aceptable pero mejorable', 3),
((SELECT id FROM ref_kpis WHERE kpi_codigo = 'ENERGIA_TOTAL'), 'Crítico', 16, NULL, '#F44336', 'Consumo energético crítico, requiere acción', 4);

-- Para Distancia de Distribución (LATAM)
INSERT INTO ref_rangos_interpretativos (
    kpi_id, nombre_rango, valor_min, valor_max, color_hex, descripcion, orden
) VALUES
((SELECT id FROM ref_kpis WHERE kpi_codigo = 'DISTANCIA_DISTRIBUCION'), 'Óptimo', NULL, 15, '#00C853', 'Distancia óptima de distribución', 1),
((SELECT id FROM ref_kpis WHERE kpi_codigo = 'DISTANCIA_DISTRIBUCION'), 'Referencia LATAM', 15, 20, '#4CAF50', 'Rango referencia para LATAM', 2),
((SELECT id FROM ref_kpis WHERE kpi_codigo = 'DISTANCIA_DISTRIBUCION'), 'Largo', 20, 30, '#FFC107', 'Distancia larga, optimizable', 3),
((SELECT id FROM ref_kpis WHERE kpi_codigo = 'DISTANCIA_DISTRIBUCION'), 'Excesivo', 30, NULL, '#F44336', 'Distancia excesiva, requiere análisis', 4);

-- ============================================================================
-- VERIFICACIÓN
-- ============================================================================

-- Contar registros insertados
SELECT 'Dimensiones:', COUNT(*) FROM ref_dimensiones;
SELECT 'Valores de Dimensión:', COUNT(*) FROM ref_valores_dimension;
SELECT 'Categorías KPI:', COUNT(*) FROM ref_categorias_kpi;
SELECT 'KPIs:', COUNT(*) FROM ref_kpis;
SELECT 'Benchmarks:', COUNT(*) FROM ref_gcca_benchmarks;
SELECT 'Asociaciones Benchmark-Dimensión:', COUNT(*) FROM ref_benchmark_dimensiones;
SELECT 'Rangos Interpretativos:', COUNT(*) FROM ref_rangos_interpretativos;

-- Mostrar vista de benchmarks completos
SELECT * FROM v_benchmarks_por_region LIMIT 10;
