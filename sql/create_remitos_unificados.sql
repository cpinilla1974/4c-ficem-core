-- ============================================================================
-- ESQUEMA UNIFICADO: Remitos de Concreto con Emisiones Desagregadas
-- ============================================================================
-- Consolida datos de remitos_co2, remitos_concretos y huella_concretos
-- Estructura normalizada con tabla principal + tabla de componentes
-- ============================================================================

-- ============================================================================
-- TABLA 1: REMITOS (Principal - 1 fila por remito)
-- ============================================================================

CREATE TABLE remitos (
    id SERIAL PRIMARY KEY,

    -- Identificación
    id_remito TEXT NOT NULL,
    origen TEXT NOT NULL,  -- 'pacas', 'mzma', 'melon', 'lomax'
    empresa TEXT,
    pais TEXT,

    -- Temporales
    fecha DATE NOT NULL,
    año INTEGER,
    mes INTEGER,
    trimestre INTEGER,

    -- Ubicación y producción
    planta TEXT,
    producto TEXT,
    formulacion TEXT,

    -- Características del concreto
    resistencia_mpa REAL NOT NULL,
    volumen REAL NOT NULL,
    slump REAL,

    -- Cemento utilizado
    tipo_cemento TEXT,
    contenido_cemento REAL,      -- kg cemento por m³
    factor_clinker REAL,          -- Contenido de clinker en el cemento (0-1)
    coprocesamiento REAL,         -- % coprocesamiento en planta origen del cemento

    -- Contexto del proyecto
    proyecto TEXT,
    cliente TEXT,

    -- Totales de emisiones CO2 (kg)
    co2_total REAL,
    co2_kg_m3 REAL,               -- Intensidad de carbono
    a1_total REAL,                -- Producción materias primas
    a2_total REAL,                -- Transporte materias primas
    a3_total REAL,                -- Producción concreto
    a4_total REAL,                -- Transporte concreto
    a5_total REAL,                -- Otros

    -- Metadata
    archivo_origen TEXT,
    fecha_migracion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (volumen > 0),
    CHECK (resistencia_mpa > 0),
    CHECK (factor_clinker IS NULL OR (factor_clinker >= 0 AND factor_clinker <= 1)),
    CHECK (coprocesamiento IS NULL OR (coprocesamiento >= 0 AND coprocesamiento <= 100)),
    UNIQUE(origen, id_remito)
);

-- ============================================================================
-- TABLA 2: REMITOS_EMISIONES_COMPONENTES (Detalle - N filas por remito)
-- ============================================================================

CREATE TABLE remitos_emisiones_componentes (
    id SERIAL PRIMARY KEY,

    -- Relación con remito
    remito_id INTEGER NOT NULL REFERENCES remitos(id) ON DELETE CASCADE,

    -- Clasificación de la emisión
    alcance TEXT NOT NULL,        -- 'A1', 'A2', 'A3', 'A4', 'A5'
    categoria TEXT,               -- 'Cemento', 'Agregados', 'Aditivos', 'Agua', 'Planta'
    componente TEXT NOT NULL,     -- Nombre específico del componente

    -- Valor de emisión
    valor_co2 REAL NOT NULL,      -- kg CO2
    unidad TEXT DEFAULT 'kg',

    -- Constraints
    CHECK (valor_co2 >= 0),
    UNIQUE(remito_id, componente)
);

-- ============================================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- ============================================================================

-- Índices tabla remitos
CREATE INDEX idx_remitos_origen ON remitos(origen);
CREATE INDEX idx_remitos_fecha ON remitos(fecha);
CREATE INDEX idx_remitos_año ON remitos(año);
CREATE INDEX idx_remitos_pais ON remitos(pais);
CREATE INDEX idx_remitos_empresa ON remitos(empresa);
CREATE INDEX idx_remitos_planta ON remitos(planta);
CREATE INDEX idx_remitos_resistencia ON remitos(resistencia_mpa);
CREATE INDEX idx_remitos_tipo_cemento ON remitos(tipo_cemento);
CREATE INDEX idx_remitos_origen_fecha ON remitos(origen, fecha);

-- Índices tabla componentes
CREATE INDEX idx_componentes_remito ON remitos_emisiones_componentes(remito_id);
CREATE INDEX idx_componentes_alcance ON remitos_emisiones_componentes(alcance);
CREATE INDEX idx_componentes_categoria ON remitos_emisiones_componentes(categoria);
CREATE INDEX idx_componentes_componente ON remitos_emisiones_componentes(componente);
CREATE INDEX idx_componentes_alcance_cat ON remitos_emisiones_componentes(alcance, categoria);

-- ============================================================================
-- COMENTARIOS EN TABLAS
-- ============================================================================

COMMENT ON TABLE remitos IS 'Tabla principal de remitos de concreto unificados de toda LATAM';
COMMENT ON TABLE remitos_emisiones_componentes IS 'Emisiones CO₂ desagregadas por componente - Estructura normalizada';

COMMENT ON COLUMN remitos.origen IS 'Origen de datos: pacas (Perú), mzma (México), melon (Chile), lomax (Argentina)';
COMMENT ON COLUMN remitos.factor_clinker IS 'Contenido de clinker en el cemento usado (0-1). Se obtiene de tabla cementos';
COMMENT ON COLUMN remitos.coprocesamiento IS 'Porcentaje de coprocesamiento en planta de cemento origen (0-100)';
COMMENT ON COLUMN remitos.co2_kg_m3 IS 'Intensidad de carbono del concreto (kg CO2/m³)';

COMMENT ON COLUMN remitos_emisiones_componentes.alcance IS 'Alcance según metodología: A1=producción, A2=transporte materias primas, A3=planta, A4=transporte producto, A5=otros';
COMMENT ON COLUMN remitos_emisiones_componentes.categoria IS 'Categoría de emisión: Cemento, Agregados, Aditivos, Agua, Planta';
COMMENT ON COLUMN remitos_emisiones_componentes.componente IS 'Nombre específico del componente emisor (ej: co2_cem_descarbonatacion_clinker)';
