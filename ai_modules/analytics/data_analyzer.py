"""
Motor de Análisis Inteligente de Datos de Huella de Carbono
Piloto IA - FICEM BD

Proporciona análisis automático, detección de patrones, comparaciones
y generación de insights accionables.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from ai_modules.rag.sql_tool import SQLTool


class DataAnalyzer:
    """
    Analizador inteligente de datos de huella de carbono.
    Genera insights automáticos, comparaciones y recomendaciones.
    """

    def __init__(self):
        self.sql_tool = SQLTool()
        self._cache_stats = None

    def get_estadisticas_generales(self) -> Dict:
        """Obtiene estadísticas generales de toda la base de datos"""
        query = """
        SELECT
            COUNT(*) as total_registros,
            COUNT(DISTINCT origen) as total_companias,
            COUNT(DISTINCT año) as total_años,
            MIN(huella_co2) as huella_min,
            MAX(huella_co2) as huella_max,
            AVG(huella_co2) as huella_promedio,
            STDDEV(huella_co2) as huella_std,
            SUM(num_remitos) as total_remitos,
            SUM(volumen) as volumen_total
        FROM huella_concretos
        WHERE huella_co2 IS NOT NULL
        """
        result = self.sql_tool.execute_query(query)
        return result['rows'][0] if result['success'] and result['rows'] else {}

    def get_ranking_companias(self) -> List[Dict]:
        """Ranking de compañías por huella promedio"""
        query = """
        SELECT
            origen as compania,
            AVG(huella_co2) as huella_promedio,
            SUM(num_remitos) as total_remitos,
            SUM(volumen) as volumen_total,
            AVG("REST") as resistencia_promedio
        FROM huella_concretos
        WHERE huella_co2 IS NOT NULL
        GROUP BY origen
        ORDER BY huella_promedio ASC
        """
        result = self.sql_tool.execute_query(query)
        return result['rows'] if result['success'] else []

    def get_distribucion_bandas(self) -> Dict:
        """Distribución de remitos por bandas GCCA"""
        query = """
        SELECT
            SUM(AA_Near_Zero_Product) as banda_AA,
            SUM(A) as banda_A,
            SUM(B) as banda_B,
            SUM(C) as banda_C,
            SUM(D) as banda_D,
            SUM(E) as banda_E,
            SUM(F) as banda_F,
            SUM(num_remitos) as total_remitos
        FROM huella_concretos
        WHERE num_remitos IS NOT NULL
        """
        result = self.sql_tool.execute_query(query)
        if result['success'] and result['rows']:
            data = result['rows'][0]
            total = data.get('total_remitos', 1) or 1
            return {
                'AA': {'count': data.get('banda_AA', 0) or 0, 'porcentaje': ((data.get('banda_AA', 0) or 0) / total) * 100},
                'A': {'count': data.get('banda_A', 0) or 0, 'porcentaje': ((data.get('banda_A', 0) or 0) / total) * 100},
                'B': {'count': data.get('banda_B', 0) or 0, 'porcentaje': ((data.get('banda_B', 0) or 0) / total) * 100},
                'C': {'count': data.get('banda_C', 0) or 0, 'porcentaje': ((data.get('banda_C', 0) or 0) / total) * 100},
                'D': {'count': data.get('banda_D', 0) or 0, 'porcentaje': ((data.get('banda_D', 0) or 0) / total) * 100},
                'E': {'count': data.get('banda_E', 0) or 0, 'porcentaje': ((data.get('banda_E', 0) or 0) / total) * 100},
                'F': {'count': data.get('banda_F', 0) or 0, 'porcentaje': ((data.get('banda_F', 0) or 0) / total) * 100},
                'total': total
            }
        return {}

    def detectar_outliers(self, threshold: float = 2.5) -> List[Dict]:
        """Detecta productos con huella anormalmente alta o baja"""
        stats = self.get_estadisticas_generales()
        promedio = stats.get('huella_promedio', 0)
        std = stats.get('huella_std', 0)

        query = f"""
        SELECT
            origen as compania,
            "REST" as resistencia,
            huella_co2,
            num_remitos,
            volumen
        FROM huella_concretos
        WHERE huella_co2 IS NOT NULL
          AND (huella_co2 > {promedio + threshold * std}
               OR huella_co2 < {promedio - threshold * std})
        ORDER BY ABS(huella_co2 - {promedio}) DESC
        LIMIT 10
        """
        result = self.sql_tool.execute_query(query)
        return result['rows'] if result['success'] else []

    def analizar_compania_detallado(self, compania: str, año: Optional[int] = None) -> Dict:
        """
        Análisis completo y detallado de una compañía.
        Retorna múltiples insights automáticos.
        """
        # 1. Datos básicos
        result_basico = self.sql_tool.get_huella_promedio_compania(compania, año)
        if not result_basico['success'] or not result_basico['rows']:
            return {'error': f'No se encontraron datos para {compania}'}

        datos_basicos = result_basico['rows'][0]

        # 2. Comparación con promedio industria
        stats_generales = self.get_estadisticas_generales()
        promedio_industria = stats_generales.get('huella_promedio', 0)
        huella_compania = datos_basicos.get('huella_promedio', 0)

        diferencia_porcentual = ((huella_compania - promedio_industria) / promedio_industria) * 100 if promedio_industria else 0

        # 3. Ranking entre competencia
        ranking = self.get_ranking_companias()
        posicion = next((i+1 for i, c in enumerate(ranking) if c['compania'].lower() == compania.lower()), None)

        # 4. Distribución por bandas de la compañía
        where_clause = f"WHERE LOWER(origen) = LOWER('{compania}')"
        if año:
            where_clause += f" AND año = {año}"

        query_bandas = f"""
        SELECT
            SUM(AA_Near_Zero_Product) as banda_AA,
            SUM(A) as banda_A,
            SUM(B) as banda_B,
            SUM(C) as banda_C,
            SUM(D) as banda_D,
            SUM(E) as banda_E,
            SUM(F) as banda_F,
            SUM(num_remitos) as total_remitos
        FROM huella_concretos
        {where_clause}
        """
        result_bandas = self.sql_tool.execute_query(query_bandas)
        bandas = result_bandas['rows'][0] if result_bandas['success'] and result_bandas['rows'] else {}

        # 5. Detectar productos problemáticos (banda E y F)
        query_problemas = f"""
        SELECT
            "REST" as resistencia,
            huella_co2,
            E + F as remitos_problematicos
        FROM huella_concretos
        {where_clause}
        AND (E > 0 OR F > 0)
        ORDER BY (E + F) DESC
        LIMIT 5
        """
        result_problemas = self.sql_tool.execute_query(query_problemas)
        productos_problematicos = result_problemas['rows'] if result_problemas['success'] else []

        # 6. Generar insights
        insights = self._generar_insights_compania(
            datos_basicos,
            diferencia_porcentual,
            posicion,
            len(ranking),
            bandas,
            productos_problematicos
        )

        # 7. Calcular potencial de mejora
        potencial = self._calcular_potencial_mejora(bandas, datos_basicos)

        return {
            'datos_basicos': datos_basicos,
            'comparacion': {
                'promedio_industria': promedio_industria,
                'diferencia_porcentual': diferencia_porcentual,
                'posicion_ranking': posicion,
                'total_companias': len(ranking)
            },
            'bandas': bandas,
            'productos_problematicos': productos_problematicos,
            'insights': insights,
            'potencial_mejora': potencial,
            'alertas': self._generar_alertas(bandas, diferencia_porcentual)
        }

    def analizar_completo(self) -> Dict:
        """
        Análisis completo de TODA la base de datos.
        Genera reporte ejecutivo con múltiples insights.
        """
        # 1. Estadísticas generales
        stats = self.get_estadisticas_generales()

        # 2. Ranking de compañías
        ranking = self.get_ranking_companias()

        # 3. Distribución por bandas
        bandas = self.get_distribucion_bandas()

        # 4. Outliers
        outliers = self.detectar_outliers()

        # 5. Tendencias temporales
        tendencias = self._analizar_tendencias_temporales()

        # 6. Correlaciones
        correlaciones = self._calcular_correlaciones()

        # 7. Insights generales
        insights_generales = self._generar_insights_generales(stats, ranking, bandas, tendencias)

        # 8. Recomendaciones priorizadas
        recomendaciones = self._generar_recomendaciones_priorizadas(ranking, bandas, outliers)

        return {
            'resumen_ejecutivo': {
                'total_companias': stats.get('total_companias', 0),
                'total_remitos': stats.get('total_remitos', 0),
                'huella_promedio': stats.get('huella_promedio', 0),
                'rango_huella': (stats.get('huella_min', 0), stats.get('huella_max', 0))
            },
            'ranking_companias': ranking,
            'distribucion_bandas': bandas,
            'outliers': outliers[:5],  # Top 5 casos extremos
            'tendencias': tendencias,
            'correlaciones': correlaciones,
            'insights': insights_generales,
            'recomendaciones': recomendaciones
        }

    def _generar_insights_compania(self, datos, diferencia_pct, posicion, total_companias, bandas, problemas) -> List[str]:
        """Genera insights específicos de una compañía"""
        insights = []

        huella = datos.get('huella_promedio', 0)

        # Insight de posicionamiento
        if diferencia_pct < -10:
            insights.append(f"🌟 **Desempeño excelente**: La huella está {abs(diferencia_pct):.1f}% BAJO el promedio de la industria")
        elif diferencia_pct < 0:
            insights.append(f"✅ **Buen desempeño**: La huella está {abs(diferencia_pct):.1f}% por debajo del promedio")
        elif diferencia_pct < 10:
            insights.append(f"📊 **Desempeño promedio**: La huella está {diferencia_pct:.1f}% cerca del promedio")
        else:
            insights.append(f"⚠️ **Requiere atención**: La huella está {diferencia_pct:.1f}% SOBRE el promedio de la industria")

        # Insight de ranking
        if posicion == 1:
            insights.append(f"🏆 **Líder de la industria**: Ocupa el puesto #{posicion} de {total_companias} compañías")
        elif posicion <= 2:
            insights.append(f"🥈 **Top performer**: Ocupa el puesto #{posicion} de {total_companias} compañías")
        elif posicion:
            insights.append(f"📍 **Posición #{posicion}** de {total_companias} compañías")

        # Insight de distribución por bandas
        total_remitos = bandas.get('total_remitos', 1) or 1
        bandas_buenas = (bandas.get('banda_AA', 0) or 0) + (bandas.get('banda_A', 0) or 0) + (bandas.get('banda_B', 0) or 0)
        pct_buenas = (bandas_buenas / total_remitos) * 100

        if pct_buenas > 60:
            insights.append(f"💚 **Distribución saludable**: {pct_buenas:.1f}% de remitos en bandas AA-B (excelente)")
        elif pct_buenas > 40:
            insights.append(f"🟡 **Distribución mejorable**: {pct_buenas:.1f}% de remitos en bandas AA-B")
        else:
            insights.append(f"🔴 **Distribución crítica**: Solo {pct_buenas:.1f}% de remitos en bandas AA-B")

        # Insight de productos problemáticos
        if problemas:
            total_problematicos = sum(p.get('remitos_problematicos', 0) for p in problemas)
            pct_problematicos = (total_problematicos / total_remitos) * 100
            if pct_problematicos > 15:
                insights.append(f"⚠️ **ALERTA**: {pct_problematicos:.1f}% de remitos en bandas E-F (crítico)")
            elif pct_problematicos > 5:
                insights.append(f"🟡 **Atención**: {pct_problematicos:.1f}% de remitos en bandas E-F")

        return insights

    def _calcular_potencial_mejora(self, bandas, datos) -> Dict:
        """Calcula el potencial de mejora si se optimizan productos en bandas malas"""
        total_remitos = bandas.get('total_remitos', 1) or 1
        remitos_malos = (bandas.get('banda_E', 0) or 0) + (bandas.get('banda_F', 0) or 0)

        if remitos_malos == 0:
            return {'tiene_potencial': False, 'mensaje': 'No hay productos en bandas críticas'}

        # Estimación: si mejoran productos E-F a banda B, ahorran ~50 kg CO2/m³
        reduccion_estimada_por_m3 = 50
        volumen_afectado = (remitos_malos / total_remitos) * datos.get('volumen_total', 0)
        ahorro_co2_tons = (reduccion_estimada_por_m3 * volumen_afectado) / 1000

        return {
            'tiene_potencial': True,
            'remitos_mejorables': int(remitos_malos),
            'porcentaje_remitos': (remitos_malos / total_remitos) * 100,
            'reduccion_estimada_kg_m3': reduccion_estimada_por_m3,
            'ahorro_co2_tons_año': ahorro_co2_tons,
            'mensaje': f'Optimizando {int(remitos_malos):,} remitos en bandas E-F se podrían ahorrar ~{ahorro_co2_tons:.0f} toneladas de CO₂/año'
        }

    def _generar_alertas(self, bandas, diferencia_pct) -> List[Dict]:
        """Genera alertas según severidad"""
        alertas = []

        total = bandas.get('total_remitos', 1) or 1

        # Alerta crítica: mucho volumen en banda F
        banda_f = (bandas.get('banda_F', 0) or 0)
        if banda_f > total * 0.10:
            alertas.append({
                'nivel': 'critico',
                'mensaje': f'{(banda_f/total)*100:.1f}% de remitos en Banda F (crítico)',
                'accion': 'Revisión urgente de procesos productivos'
            })

        # Alerta media: huella muy por encima del promedio
        if diferencia_pct > 15:
            alertas.append({
                'nivel': 'medio',
                'mensaje': f'Huella {diferencia_pct:.1f}% sobre promedio industria',
                'accion': 'Implementar plan de reducción de emisiones'
            })

        # Alerta baja: pocas productos en banda AA
        banda_aa = (bandas.get('banda_AA', 0) or 0)
        if banda_aa < total * 0.05 and total > 100:
            alertas.append({
                'nivel': 'bajo',
                'mensaje': f'Solo {(banda_aa/total)*100:.1f}% de remitos en Banda AA (near-zero)',
                'accion': 'Oportunidad de desarrollar productos bajos en carbono'
            })

        return alertas

    def _analizar_tendencias_temporales(self) -> Dict:
        """Analiza evolución temporal de la huella"""
        query = """
        SELECT
            año,
            AVG(huella_co2) as huella_promedio,
            COUNT(*) as registros
        FROM huella_concretos
        WHERE año IS NOT NULL AND huella_co2 IS NOT NULL
        GROUP BY año
        ORDER BY año
        """
        result = self.sql_tool.execute_query(query)

        if not result['success'] or len(result['rows']) < 2:
            return {'tiene_datos': False}

        datos = result['rows']
        años = [d['año'] for d in datos]
        huellas = [d['huella_promedio'] for d in datos]

        # Calcular tendencia simple
        cambio_total = huellas[-1] - huellas[0]
        cambio_pct = (cambio_total / huellas[0]) * 100 if huellas[0] else 0

        tendencia = 'mejora' if cambio_total < 0 else 'empeoramiento' if cambio_total > 0 else 'estable'

        return {
            'tiene_datos': True,
            'años': años,
            'huellas': huellas,
            'cambio_total': cambio_total,
            'cambio_porcentual': cambio_pct,
            'tendencia': tendencia,
            'mensaje': f'Cambio de {abs(cambio_pct):.1f}% en {años[-1] - años[0]} años ({tendencia})'
        }

    def _calcular_correlaciones(self) -> Dict:
        """Calcula correlaciones entre variables"""
        query = """
        SELECT
            "REST" as resistencia,
            huella_co2,
            volumen
        FROM huella_concretos
        WHERE "REST" IS NOT NULL AND huella_co2 IS NOT NULL
        """
        result = self.sql_tool.execute_query(query)

        if not result['success'] or len(result['rows']) < 10:
            return {'tiene_datos': False}

        df = pd.DataFrame(result['rows'])

        # Correlación resistencia vs huella
        corr_resist = df['resistencia'].corr(df['huella_co2'])

        return {
            'tiene_datos': True,
            'resistencia_vs_huella': corr_resist,
            'interpretacion': self._interpretar_correlacion(corr_resist, 'resistencia', 'huella')
        }

    def _interpretar_correlacion(self, corr: float, var1: str, var2: str) -> str:
        """Interpreta el valor de correlación"""
        abs_corr = abs(corr)
        direccion = 'positiva' if corr > 0 else 'negativa'

        if abs_corr > 0.7:
            fuerza = 'fuerte'
        elif abs_corr > 0.4:
            fuerza = 'moderada'
        else:
            fuerza = 'débil'

        return f'Correlación {direccion} {fuerza} ({corr:.2f}) entre {var1} y {var2}'

    def _generar_insights_generales(self, stats, ranking, bandas, tendencias) -> List[str]:
        """Genera insights del análisis completo"""
        insights = []

        # Insight de diversidad
        n_companias = stats.get('total_companias', 0)
        insights.append(f"📊 **Base de datos**: {n_companias} compañías con {stats.get('total_remitos', 0):,} remitos analizados")

        # Insight de rango
        rango = stats.get('huella_max', 0) - stats.get('huella_min', 0)
        insights.append(f"📈 **Rango de huella**: {stats.get('huella_min', 0):.1f} - {stats.get('huella_max', 0):.1f} kg CO₂/m³ (variación de {rango:.1f})")

        # Insight de distribución
        if bandas:
            total = bandas.get('total', 1)
            aa_a = (bandas['AA']['count'] + bandas['A']['count'])
            pct = (aa_a / total) * 100

            if pct > 30:
                insights.append(f"🌟 **Productos destacados**: {pct:.1f}% en bandas AA-A (excelente)")
            else:
                insights.append(f"⚠️ **Oportunidad de mejora**: Solo {pct:.1f}% en bandas AA-A")

        # Insight de tendencia
        if tendencias.get('tiene_datos'):
            tendencia_msg = tendencias.get('mensaje', '')
            if 'mejora' in tendencias.get('tendencia', ''):
                insights.append(f"📉 **Tendencia positiva**: {tendencia_msg}")
            else:
                insights.append(f"📊 **Tendencia**: {tendencia_msg}")

        # Insight de liderazgo
        if ranking:
            lider = ranking[0]
            peor = ranking[-1]
            brecha = peor['huella_promedio'] - lider['huella_promedio']
            insights.append(f"🏆 **Líder**: {lider['compania'].upper()} ({lider['huella_promedio']:.1f} kg CO₂/m³) vs último: {peor['compania'].upper()} ({peor['huella_promedio']:.1f}). Brecha: {brecha:.1f} kg CO₂/m³")

        return insights

    def _generar_recomendaciones_priorizadas(self, ranking, bandas, outliers) -> List[Dict]:
        """Genera recomendaciones priorizadas por impacto"""
        recomendaciones = []

        # Recomendación 1: Optimizar productos en bandas malas
        if bandas:
            total = bandas.get('total', 1)
            malos = (bandas['E']['count'] + bandas['F']['count'])
            if malos > total * 0.1:
                recomendaciones.append({
                    'prioridad': 'alta',
                    'titulo': 'Optimizar productos en bandas E-F',
                    'impacto': 'Alto - Afecta {:.1f}% del volumen'.format((malos/total)*100),
                    'accion': 'Revisar formulaciones y procesos de productos en bandas críticas'
                })

        # Recomendación 2: Benchmarking con líder
        if ranking and len(ranking) > 1:
            lider = ranking[0]
            recomendaciones.append({
                'prioridad': 'media',
                'titulo': f'Benchmarking con {lider["compania"].upper()}',
                'impacto': 'Medio - Aprender mejores prácticas',
                'accion': f'Estudiar procesos de {lider["compania"].upper()} (huella: {lider["huella_promedio"]:.1f} kg CO₂/m³)'
            })

        # Recomendación 3: Atender outliers
        if outliers:
            recomendaciones.append({
                'prioridad': 'media',
                'titulo': 'Revisar productos con huella extrema',
                'impacto': 'Medio - Casos específicos',
                'accion': f'Investigar {len(outliers)} productos con valores anormales'
            })

        # Recomendación 4: Aumentar productos AA
        if bandas:
            aa_pct = (bandas['AA']['count'] / bandas.get('total', 1)) * 100
            if aa_pct < 5:
                recomendaciones.append({
                    'prioridad': 'baja',
                    'titulo': 'Desarrollar productos near-zero',
                    'impacto': 'Bajo - Estratégico largo plazo',
                    'accion': 'Invertir en I+D para productos de banda AA (near-zero)'
                })

        return recomendaciones

    # ===== NUEVOS MÉTODOS DE MEJORA =====

    def validar_rangos_datos(self) -> Dict:
        """Valida si los datos están dentro de rangos esperados"""
        # Rangos esperados para huella de carbono
        RANGO_HUELLA_MIN = 150  # kg CO2/m³
        RANGO_HUELLA_MAX = 450  # kg CO2/m³

        query = """
        SELECT
            COUNT(*) as total_registros,
            COUNT(CASE WHEN huella_co2 >= %s AND huella_co2 <= %s THEN 1 END) as huella_valida,
            COUNT(CASE WHEN huella_co2 < %s THEN 1 END) as huella_baja,
            COUNT(CASE WHEN huella_co2 > %s THEN 1 END) as huella_alta,
            COUNT(CASE WHEN huella_co2 IS NOT NULL THEN 1 END) as con_huella
        FROM huella_concretos
        """ % (RANGO_HUELLA_MIN, RANGO_HUELLA_MAX, RANGO_HUELLA_MIN, RANGO_HUELLA_MAX)

        result = self.sql_tool.execute_query(query)
        if result['success'] and result['rows']:
            data = result['rows'][0]
            total = data.get('total_registros', 1) or 1

            return {
                'total_registros': total,
                'huella_valida': {
                    'count': data.get('huella_valida', 0) or 0,
                    'porcentaje': ((data.get('huella_valida', 0) or 0) / total) * 100,
                    'rango': f"{RANGO_HUELLA_MIN}-{RANGO_HUELLA_MAX} kg CO2/m³"
                },
                'huella_fuera_rango': {
                    'baja': data.get('huella_baja', 0) or 0,
                    'alta': data.get('huella_alta', 0) or 0,
                    'total_problemas': (data.get('huella_baja', 0) or 0) + (data.get('huella_alta', 0) or 0)
                }
            }
        return {}

    def get_ranking_por_tipo_cemento(self) -> List[Dict]:
        """Ranking de compañías segmentado por tipo de cemento"""
        query = """
        SELECT
            rtc.codigo_cemento as tipo_cemento,
            h.origen as compania,
            AVG(h.huella_co2) as huella_promedio,
            COUNT(h.*) as num_productos,
            AVG(rtc.factor_clinker_promedio) as factor_clinker,
            AVG(rtc.huella_co2_promedio) as huella_tipo_cemento
        FROM huella_concretos h
        LEFT JOIN ref_tipos_cemento rtc ON h.planta = rtc.planta
        WHERE h.huella_co2 IS NOT NULL
        GROUP BY rtc.codigo_cemento, h.origen
        ORDER BY rtc.codigo_cemento, huella_promedio ASC
        """
        result = self.sql_tool.execute_query(query)
        return result['rows'] if result['success'] else []

    def analizar_calidad_datos(self) -> Dict:
        """Análisis completo de calidad de datos con indicadores"""
        query = """
        SELECT
            COUNT(*) as total_registros,
            COUNT(DISTINCT origen) as total_companias,
            COUNT(DISTINCT año) as años_datos,
            MIN(año) as año_inicio,
            MAX(año) as año_fin,
            COUNT(CASE WHEN huella_co2 IS NOT NULL THEN 1 END) as con_huella,
            COUNT(CASE WHEN huella_co2 >= 150 AND huella_co2 <= 450 THEN 1 END) as registros_validos,
            COUNT(CASE WHEN huella_co2 < 150 OR huella_co2 > 450 THEN 1 END) as registros_anomalos,
            COUNT(CASE WHEN huella_co2 < 150 THEN 1 END) as huella_baja,
            COUNT(CASE WHEN huella_co2 > 450 THEN 1 END) as huella_alta,
            COUNT(CASE WHEN "A4_Total" IS NOT NULL THEN 1 END) as con_a4,
            COUNT(CASE WHEN volumen IS NOT NULL THEN 1 END) as con_volumen,
            COUNT(CASE WHEN "REST" IS NOT NULL THEN 1 END) as con_resistencia,
            MIN(huella_co2) as huella_minima,
            MAX(huella_co2) as huella_maxima,
            ROUND(AVG(huella_co2), 2) as huella_promedio,
            MIN(volumen) as volumen_minimo,
            MAX(volumen) as volumen_maximo,
            ROUND(AVG(volumen), 2) as volumen_promedio
        FROM huella_concretos
        """
        result = self.sql_tool.execute_query(query)
        if result['success'] and result['rows']:
            data = result['rows'][0]
            total = data.get('total_registros', 1) or 1

            registros_validos = (data.get('registros_validos', 0) or 0)
            calidad_datos = (registros_validos / total) * 100
            cobertura_a4 = ((data.get('con_a4', 0) or 0) / total) * 100
            cobertura_resistencia = ((data.get('con_resistencia', 0) or 0) / total) * 100

            return {
                'total_registros': total,
                'compañías': data.get('total_companias', 0) or 0,
                'plantas': 1,  # Solo 1 por ahora (no hay columna planta)
                'período': f"{data.get('año_inicio', '?')}-{data.get('año_fin', '?')}",
                'años_datos': data.get('años_datos', 0) or 0,
                'cobertura_a4': round(cobertura_a4, 1),
                'cobertura_resistencia': round(cobertura_resistencia, 1),
                'porcentaje_datos_validos': round(calidad_datos, 1),
                'porcentaje_datos_anómalos': round(100 - calidad_datos, 1),
                'calidad_general': 'Buena' if calidad_datos > 90 else 'Aceptable' if calidad_datos > 70 else 'Requiere mejora',
                'huella_minima': round(data.get('huella_minima', 0) or 0, 2),
                'huella_maxima': round(data.get('huella_maxima', 0) or 0, 2),
                'huella_promedio': data.get('huella_promedio', 0),
                'huella_baja': data.get('huella_baja', 0),
                'huella_alta': data.get('huella_alta', 0),
                'volumen_minimo': round(data.get('volumen_minimo', 0) or 0, 2),
                'volumen_maximo': round(data.get('volumen_maximo', 0) or 0, 2),
                'volumen_promedio': data.get('volumen_promedio', 0)
            }
        return {}
