-- ============================================================================
-- VISTAS MATERIALIZADAS: Dashboard Remitos LATAM
-- ============================================================================
-- Optimizan el rendimiento del dashboard pre-calculando consultas complejas
-- Se actualizan manualmente con: REFRESH MATERIALIZED VIEW nombre_vista;
-- ============================================================================

-- ============================================================================
-- VISTA 1: Resumen por Origen
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_resumen_por_origen AS
SELECT
    origen,
    empresa,
    pais,
    COUNT(*) as total_remitos,
    SUM(volumen) as volumen_total,
    ROUND(AVG(CASE WHEN resistencia_mpa > 0 THEN resistencia_mpa END)::numeric, 1) as resistencia_promedio,
    ROUND(AVG(CASE WHEN co2_kg_m3 > 0 THEN co2_kg_m3 END)::numeric, 1) as co2_promedio,
    MIN(fecha) as fecha_inicio,
    MAX(fecha) as fecha_fin
FROM remitos
GROUP BY origen, empresa, pais
ORDER BY total_remitos DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_resumen_origen ON mv_resumen_por_origen(origen);

-- ============================================================================
-- VISTA 2: Evolución Temporal Mensual
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_evolucion_temporal AS
SELECT
    DATE_TRUNC('month', fecha)::date as mes,
    origen,
    COUNT(*) as num_remitos,
    SUM(volumen) as volumen_m3
FROM remitos
WHERE fecha IS NOT NULL
GROUP BY DATE_TRUNC('month', fecha), origen
ORDER BY mes, origen;

CREATE INDEX IF NOT EXISTS idx_mv_evolucion_mes ON mv_evolucion_temporal(mes);
CREATE INDEX IF NOT EXISTS idx_mv_evolucion_origen ON mv_evolucion_temporal(origen);

-- ============================================================================
-- VISTA 3: Top Plantas por Volumen
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_plantas AS
SELECT
    origen,
    planta,
    COUNT(*) as num_remitos,
    ROUND(SUM(volumen)::numeric, 0) as volumen_total,
    ROUND(AVG(co2_kg_m3)::numeric, 1) as co2_promedio
FROM remitos
WHERE planta IS NOT NULL
GROUP BY origen, planta
ORDER BY volumen_total DESC
LIMIT 20;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_top_plantas ON mv_top_plantas(origen, planta);

-- ============================================================================
-- VISTA 4: Distribución de Resistencias
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_distribucion_resistencia AS
SELECT
    origen,
    resistencia_mpa,
    COUNT(*) as cantidad
FROM remitos
WHERE resistencia_mpa > 0
GROUP BY origen, resistencia_mpa
ORDER BY origen, resistencia_mpa;

CREATE INDEX IF NOT EXISTS idx_mv_dist_resistencia_origen ON mv_distribucion_resistencia(origen);

-- ============================================================================
-- COMENTARIOS
-- ============================================================================

COMMENT ON MATERIALIZED VIEW mv_resumen_por_origen IS 'Resumen agregado por origen para dashboard principal';
COMMENT ON MATERIALIZED VIEW mv_evolucion_temporal IS 'Evolución mensual de remitos y volumen por origen';
COMMENT ON MATERIALIZED VIEW mv_top_plantas IS 'Top 20 plantas por volumen total';
COMMENT ON MATERIALIZED VIEW mv_distribucion_resistencia IS 'Distribución de resistencias por origen para histogramas';

-- ============================================================================
-- FUNCIÓN: Refrescar todas las vistas
-- ============================================================================

CREATE OR REPLACE FUNCTION refresh_dashboard_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_resumen_por_origen;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_evolucion_temporal;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_plantas;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_distribucion_resistencia;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_dashboard_views() IS 'Refresca todas las vistas materializadas del dashboard en paralelo';

-- Para refrescar todas las vistas: SELECT refresh_dashboard_views();
