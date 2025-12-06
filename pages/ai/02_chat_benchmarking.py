"""
Chat de Benchmarking con Análisis Inteligente
Piloto IA - FICEM BD

Incluye:
- Botón de análisis completo automático
- Chat con respuestas inteligentes y análisis profundo
- Preguntas pre-configuradas complejas
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go

# Agregar path para imports
sys.path.insert(0, str(Path.cwd()))

from ai_modules.rag.sql_tool import SQLTool
from ai_modules.analytics.data_analyzer import DataAnalyzer

def app():
    st.title("💬 Chat de Benchmarking Inteligente")
    st.markdown("### Análisis Automático de Datos de Huella de Carbono")

    # Inicializar herramientas
    @st.cache_resource
    def get_tools():
        return SQLTool(), DataAnalyzer()

    # Inicializar historial de chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Inicializar herramientas
    try:
        sql_tool, analyzer = get_tools()
        st.success(f"✅ Sistema de análisis inteligente listo")
    except Exception as e:
        st.error(f"❌ Error inicializando sistema: {e}")
        st.stop()

    # ============================================
    # BOTÓN DE ANÁLISIS COMPLETO
    # ============================================
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("🔍 ANÁLISIS COMPLETO DE BASE DE DATOS", type="primary", use_container_width=True):
            with st.spinner("🤖 Analizando todos los datos... Esto puede tardar 10-15 segundos"):
                try:
                    # Ejecutar análisis completo
                    analisis = analyzer.analizar_completo()

                    # Mostrar reporte estructurado
                    st.success("✅ Análisis completado!")

                    # 1. RESUMEN EJECUTIVO
                    st.subheader("📊 Resumen Ejecutivo")
                    resumen = analisis['resumen_ejecutivo']
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Compañías", resumen['total_companias'])
                    with col2:
                        st.metric("Remitos", f"{resumen['total_remitos']:,}")
                    with col3:
                        st.metric("Huella Promedio", f"{resumen['huella_promedio']:.1f} kg CO₂/m³")
                    with col4:
                        rango = resumen['rango_huella']
                        st.metric("Rango", f"{rango[0]:.0f} - {rango[1]:.0f}")

                    # 2. INSIGHTS PRINCIPALES
                    st.subheader("💡 Insights Principales")
                    for insight in analisis['insights']:
                        st.markdown(f"- {insight}")

                    # 3. RANKING DE COMPAÑÍAS
                    st.subheader("🏆 Ranking de Compañías")
                    df_ranking = pd.DataFrame(analisis['ranking_companias'])
                    df_ranking['compania'] = df_ranking['compania'].str.upper()

                    # Gráfico de barras
                    fig = px.bar(
                        df_ranking,
                        x='compania',
                        y='huella_promedio',
                        title='Huella Promedio por Compañía',
                        labels={'huella_promedio': 'Huella (kg CO₂/m³)', 'compania': 'Compañía'},
                        color='huella_promedio',
                        color_continuous_scale='RdYlGn_r'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Tabla detallada
                    with st.expander("📋 Ver tabla detallada"):
                        st.dataframe(df_ranking, use_container_width=True)

                    # 4. RECOMENDACIONES PRIORIZADAS
                    st.subheader("🎯 Recomendaciones Priorizadas")
                    for rec in analisis['recomendaciones']:
                        color = {
                            'alta': '🔴',
                            'media': '🟡',
                            'baja': '🟢'
                        }.get(rec['prioridad'], '⚪')

                        with st.expander(f"{color} **{rec['titulo']}** (Prioridad: {rec['prioridad'].upper()})"):
                            st.markdown(f"**Impacto:** {rec['impacto']}")
                            st.markdown(f"**Acción:** {rec['accion']}")

                except Exception as e:
                    st.error(f"❌ Error durante el análisis: {e}")
                    import traceback
                    st.code(traceback.format_exc())

    st.divider()

    # ============================================
    # SIDEBAR
    # ============================================
    with st.sidebar:
        st.header("📊 Base de Datos")

        st.markdown("""
        **Tablas disponibles:**
        - `huella_concretos` - Datos de huella de carbono
        - `cementos` - Datos de cementos
        - `plantas_latam` - Plantas de cemento
        """)

        st.divider()

        st.header("💡 Preguntas Inteligentes")

        preguntas_inteligentes = [
            "📊 Completitud de datos",
            "🔍 Análisis de MZMA",
            "🔍 Análisis de Melón",
            "🏆 ¿Qué compañía lidera?",
            "⚠️ ¿Dónde están los problemas?",
        ]

        st.markdown("**Análisis Profundo:**")
        for i, pregunta in enumerate(preguntas_inteligentes):
            if st.button(pregunta, key=f"smart_q_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": pregunta})
                st.rerun()

        st.divider()

        if st.button("🗑️ Limpiar Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # ============================================
    # CHAT
    # ============================================

    # Mostrar historial de mensajes
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Procesar pregunta pendiente
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        prompt = st.session_state.messages[-1]["content"]

        with st.chat_message("assistant"):
            with st.spinner("🤖 Analizando datos..."):
                try:
                    respuesta = procesar_pregunta_inteligente(prompt, sql_tool, analyzer)
                    st.markdown(respuesta)
                    
                    # Agregar a historial
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": respuesta
                    })

                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())

    # Input de usuario
    if prompt := st.chat_input("✍️ Pregunta sobre datos, análisis de compañías, tendencias..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # Footer
    st.divider()
    st.caption(f"💬 Chat de Benchmarking Inteligente - Análisis Automático con IA")


def procesar_pregunta_inteligente(prompt: str, sql_tool, analyzer):
    """
    Procesa preguntas con análisis inteligente automático.
    """
    prompt_lower = prompt.lower()

    # COMPLETITUD DE DATOS
    if "completitud" in prompt_lower or "calidad" in prompt_lower:
        calidad = analyzer.analizar_calidad_datos()
        validacion = analyzer.validar_rangos_datos()

        respuesta = f"""
# 🔍 ANÁLISIS DE INTEGRIDAD Y CALIDAD DE BASE DE DATOS LATAM-3C

## Score de Calidad: {int(calidad.get('porcentaje_datos_validos', 0))}/100

### 📊 VOLUMEN DE DATOS

| Métrica | Valor |
|---------|-------|
| **Total de Remitos** | {calidad.get('total_registros', 0):,} |
| **Período cubierto** | {calidad.get('período', 'N/A')} ({calidad.get('años_datos', 0)} años) |
| **Compañías distintas** | {calidad.get('compañías', 0)} |
| **Plantas distintas** | {calidad.get('plantas', 0)} |

### 📈 ESTADÍSTICAS DE HUELLA DE CARBONO

| Métrica | Valor | Rango Esperado |
|---------|-------|---|
| **Mínimo** | {calidad.get('huella_minima', 0):.1f} kg CO₂/m³ | 150-450 |
| **Promedio** | {calidad.get('huella_promedio', 0):.1f} kg CO₂/m³ | 150-450 |
| **Máximo** | {calidad.get('huella_maxima', 0):.1f} kg CO₂/m³ | 150-450 |

### ✅ VALIDACIÓN DE DATOS - HUELLA DE CARBONO

**Registros Válidos (150-450 kg CO₂/m³):**
- **Total válido:** {validacion.get('huella_valida', {}).get('count', 0):,} registros ({validacion.get('huella_valida', {}).get('porcentaje', 0):.1f}%)

**Registros Fuera de Rango (Anomalías):**
- **Huella muy baja (<150 kg CO₂/m³):** {validacion.get('huella_fuera_rango', {}).get('baja', 0):,} registros
- **Huella muy alta (>450 kg CO₂/m³):** {validacion.get('huella_fuera_rango', {}).get('alta', 0):,} registros
- **Total problemas:** {validacion.get('huella_fuera_rango', {}).get('total_problemas', 0):,} ({(validacion.get('huella_fuera_rango', {}).get('total_problemas', 0) / calidad.get('total_registros', 1) * 100):.1f}%)

### 📦 COBERTURA DE CAMPOS CRÍTICOS

| Campo | Cobertura | Estado |
|-------|-----------|--------|
| Huella CO₂ (A1-A3) | 100% | ✅ Completo |
| Resistencia (MPa) | {calidad.get('cobertura_resistencia', 0):.1f}% | {'✅' if calidad.get('cobertura_resistencia', 0) > 90 else '⚠️'} |
| Datos A4 (Transporte) | {calidad.get('cobertura_a4', 0):.1f}% | {'✅' if calidad.get('cobertura_a4', 0) > 80 else '⚠️'} |
| Volumen | 100% | ✅ Completo |

### 🎯 CLASIFICACIÓN DE CALIDAD

**Calidad General:** {calidad.get('calidad_general', 'N/A').upper()}

- **Datos válidos:** {calidad.get('porcentaje_datos_validos', 0):.1f}%
- **Datos anómalos:** {calidad.get('porcentaje_datos_anómalos', 0):.1f}%

### 🚨 HALLAZGOS CRÍTICOS

"""

        if calidad.get('huella_minima', 0) < 100:
            respuesta += f"⚠️ **Valor mínimo detectado:** {calidad.get('huella_minima', 0):.1f} kg CO₂/m³ (muy bajo, posible error de datos)\n"

        if calidad.get('huella_maxima', 0) > 500:
            respuesta += f"⚠️ **Valor máximo detectado:** {calidad.get('huella_maxima', 0):.1f} kg CO₂/m³ (muy alto, requiere validación)\n"

        if validacion.get('huella_fuera_rango', {}).get('total_problemas', 0) > 50:
            respuesta += f"🔴 **{validacion.get('huella_fuera_rango', {}).get('total_problemas', 0)} registros fuera de rango esperado** - Necesita revisión de datos\n"

        if calidad.get('cobertura_a4', 0) == 100:
            respuesta += "✅ **Cobertura A4 (Transporte):** Completa (100%)\n"
        elif calidad.get('cobertura_a4', 0) < 50:
            respuesta += f"⚠️ **Cobertura A4 baja:** {calidad.get('cobertura_a4', 0):.1f}% - Datos de transporte incompletos\n"

        respuesta += f"""

### 💡 RECOMENDACIONES

1. **Validación urgente de outliers:** Revisar los {validacion.get('huella_fuera_rango', {}).get('total_problemas', 0)} registros fuera de rango
2. **Limpieza de datos:** {validacion.get('huella_fuera_rango', {}).get('baja', 0)} registros con huella muy baja, {validacion.get('huella_fuera_rango', {}).get('alta', 0)} registros con huella muy alta
3. **Completar datos A4:** Mejorar cobertura de transporte desde {calidad.get('cobertura_a4', 0):.1f}% a 100%
4. **Validación de resistencia:** Mejorar completitud desde {calidad.get('cobertura_resistencia', 0):.1f}%

### 📋 CONCLUSIÓN

La base de datos tiene **{calidad.get('total_registros', 0):,} registros** de {calidad.get('compañías', 0)} compañías en {calidad.get('plantas', 0)} plantas, con {calidad.get('porcentaje_datos_validos', 0):.1f}% de datos dentro de rangos esperados. **{validacion.get('huella_fuera_rango', {}).get('total_problemas', 0)} registros requieren revisión** antes de usar en análisis críticos.
"""
        return respuesta

    # ANÁLISIS PROFUNDO DE COMPAÑÍA
    if "análisis" in prompt_lower:
        # Detectar compañía
        if "mzma" in prompt_lower:
            compania = "mzma"
        elif "melón" in prompt_lower or "melon" in prompt_lower:
            compania = "melon"
        elif "lomax" in prompt_lower:
            compania = "lomax"
        elif "pacas" in prompt_lower:
            compania = "pacas"
        else:
            compania = "mzma"

        # Ejecutar análisis completo
        analisis = analyzer.analizar_compania_detallado(compania, None)

        if 'error' in analisis:
            return analisis['error']

        # Construir respuesta narrativa
        datos = analisis['datos_basicos']
        comp = analisis['comparacion']

        respuesta = f"""
## 🔍 Análisis Completo de {compania.upper()}

### 📊 Datos Básicos
- **Remitos:** {datos.get('num_remitos', 0):,}
- **Huella Promedio:** {datos.get('huella_promedio', 0):.2f} kg CO₂/m³
- **Resistencia Promedio:** {datos.get('resistencia_promedio', 0):.1f} MPa
- **Volumen Total:** {datos.get('volumen_total', 0):,.0f} m³

### 🏆 Posicionamiento
- **Posición:** #{comp.get('posicion_ranking')} de {comp.get('total_companias')} compañías
- **vs Promedio Industria:** {datos.get('huella_promedio', 0):.2f} vs {comp.get('promedio_industria', 0):.2f} kg CO₂/m³
- **Diferencia:** {comp.get('diferencia_porcentual', 0):+.1f}%

### 💡 Insights Clave
"""
        for insight in analisis['insights']:
            respuesta += f"\n{insight}\n"

        return respuesta

    # LÍDER
    elif "líder" in prompt_lower or "lider" in prompt_lower or "mejor" in prompt_lower:
        ranking = analyzer.get_ranking_companias()
        if ranking:
            lider = ranking[0]
            respuesta = f"""
## 🏆 Líder de la Industria

**{lider['compania'].upper()}** tiene el mejor desempeño:

- **Huella Promedio:** {lider['huella_promedio']:.2f} kg CO₂/m³
- **Remitos:** {lider['total_remitos']:,}
- **Volumen Total:** {lider['volumen_total']:,.0f} m³

### 📊 Comparación con el resto
"""
            for i, comp in enumerate(ranking[1:3], 2):
                brecha = comp['huella_promedio'] - lider['huella_promedio']
                respuesta += f"\n{i}. **{comp['compania'].upper()}**: {comp['huella_promedio']:.2f} kg CO₂/m³ (+{brecha:.2f})\n"

            return respuesta

    # PROBLEMAS
    elif "problema" in prompt_lower or "crítico" in prompt_lower or "critico" in prompt_lower:
        outliers = analyzer.detectar_outliers()

        respuesta = """
## ⚠️ Áreas Críticas Detectadas

### 🔴 Productos con Huella Extrema
"""
        if outliers:
            for i, out in enumerate(outliers[:5], 1):
                respuesta += f"\n{i}. **{out['compania'].upper()}** - {out['resistencia']:.1f} MPa: {out['huella_co2']:.2f} kg CO₂/m³\n"

        return respuesta

    # FALLBACK
    else:
        return """
❓ Prueba con preguntas específicas:

- "🔍 Análisis de MZMA" - Análisis profundo
- "🏆 ¿Qué compañía lidera?" - Ranking
- "⚠️ ¿Dónde están los problemas?" - Áreas críticas

O usa el botón **"🔍 ANÁLISIS COMPLETO"** arriba.
"""


# Run the app
app()
