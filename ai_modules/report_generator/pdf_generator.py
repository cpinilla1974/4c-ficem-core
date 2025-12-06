"""
Generador de Informes PDF
Piloto IA - FICEM BD

Genera informes de benchmarking en formato PDF con:
- Datos de empresa
- Comparación con benchmarks
- Visualizaciones
- Análisis generados por IA
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
import io
import tempfile

# ReportLab para PDF
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.colors import HexColor

# Matplotlib para gráficos
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt
import numpy as np

# RAG y SQL
from ai_modules.rag.rag_chain import BenchmarkingChain
from ai_modules.rag.sql_tool import SQLTool


class BenchmarkingReportPDF:
    """
    Generador de informes de benchmarking en PDF.
    """

    def __init__(
        self,
        llm_model: str = "qwen2.5:3b",
        use_claude: bool = False,
        output_dir: str = "./reports"
    ):
        """
        Inicializa el generador de informes.

        Args:
            llm_model: Modelo LLM a usar
            use_claude: Si True, usa Claude API
            output_dir: Directorio de salida para PDFs
        """
        self.llm_model = llm_model
        self.use_claude = use_claude
        self.output_dir = output_dir

        # Crear directorio de salida si no existe
        os.makedirs(output_dir, exist_ok=True)

        # Inicializar RAG chain
        self.rag = BenchmarkingChain(
            llm_model=llm_model,
            temperature=0.1,
            top_k=5,
            use_claude=use_claude
        )

        # Inicializar SQL tool
        self.sql_tool = SQLTool()

    def _create_chart_huella_comparacion(
        self,
        company_data: Dict,
        benchmarks: Dict
    ) -> str:
        """
        Crea gráfico de comparación de huella.

        Args:
            company_data: Datos de la empresa
            benchmarks: Benchmarks de referencia

        Returns:
            Ruta al archivo de imagen temporal
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Datos
        labels = ['Empresa', 'Promedio Regional', 'GCCA Banda A', 'GCCA Banda C']
        values = [
            company_data.get('huella_promedio', 0),
            benchmarks.get('regional', 250),
            benchmarks.get('gcca_a', 150),
            benchmarks.get('gcca_c', 300)
        ]
        colors_bars = ['#2E86AB', '#A23B72', '#52B788', '#FCA311']

        # Crear barras
        bars = ax.bar(labels, values, color=colors_bars, alpha=0.8, edgecolor='black')

        # Personalización
        ax.set_ylabel('Huella CO₂ (kg/m³)', fontsize=12, fontweight='bold')
        ax.set_title('Comparación de Huella de Carbono', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        # Agregar valores sobre barras
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()

        # Guardar en archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()

        return temp_file.name

    def _create_chart_distribucion_resistencias(
        self,
        resistencias_data: List[Dict]
    ) -> str:
        """
        Crea gráfico de distribución de resistencias.

        Args:
            resistencias_data: Lista de datos de resistencias

        Returns:
            Ruta al archivo temporal
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Extraer datos
        resistencias = [d['resistencia'] for d in resistencias_data]
        huellas = [d['huella_promedio'] for d in resistencias_data]
        volumenes = [d['volumen_total'] for d in resistencias_data]

        # Normalizar volúmenes para tamaño de burbujas
        max_vol = max(volumenes) if volumenes else 1
        sizes = [v/max_vol * 1000 for v in volumenes]

        # Scatter plot
        scatter = ax.scatter(resistencias, huellas, s=sizes, alpha=0.6, 
                            c=range(len(resistencias)), cmap='viridis', 
                            edgecolors='black', linewidth=1)

        # Personalización
        ax.set_xlabel('Resistencia (MPa)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Huella CO₂ (kg/m³)', fontsize=12, fontweight='bold')
        ax.set_title('Distribución Resistencia vs Huella (tamaño = volumen)', 
                     fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')

        # Colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Productos', rotation=270, labelpad=15)

        plt.tight_layout()

        # Guardar
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()

        return temp_file.name

    def generate_company_report(
        self,
        compania: str,
        año: Optional[int] = None,
        benchmark_type: str = "gcca"
    ) -> str:
        """
        Genera informe de benchmarking para una compañía.

        Args:
            compania: Nombre de la compañía
            año: Año (opcional)
            benchmark_type: Tipo de benchmark (gcca, gnr, regional)

        Returns:
            Ruta al archivo PDF generado
        """
        print(f"\n📊 Generando informe de benchmarking para {compania}")

        # 1. Obtener datos de la empresa
        result = self.sql_tool.get_huella_promedio_compania(compania, año)
        
        if not result["success"] or not result["rows"]:
            raise ValueError(f"No se encontraron datos para {compania}")

        company_data = result["rows"][0]

        # 2. Obtener análisis de IA
        print("🤖 Generando análisis con IA...")
        ai_analysis = self.rag.compare_with_benchmark(
            company_data=company_data,
            benchmark_type=benchmark_type
        )

        # 3. Obtener distribución de productos
        query_productos = f"""
        SELECT
            resistencia,
            COUNT(*) as num_remitos,
            AVG(huella_co2) as huella_promedio,
            SUM(volumen) as volumen_total
        FROM remitos_concretos
        WHERE LOWER(compania) = LOWER('{compania}')
        {'AND año = ' + str(año) if año else ''}
        GROUP BY resistencia
        ORDER BY volumen_total DESC
        LIMIT 10
        """
        result_productos = self.sql_tool.execute_query(query_productos)
        productos_data = result_productos["rows"] if result_productos["success"] else []

        # 4. Crear PDF
        year_str = str(año) if año else "todos_los_años"
        filename = f"benchmarking_{compania}_{year_str}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#2E86AB'),
            alignment=TA_CENTER,
            spaceAfter=30
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#2E86AB'),
            spaceAfter=12
        )

        # Título
        story.append(Paragraph(f"Informe de Benchmarking", title_style))
        story.append(Paragraph(f"{compania} - {año if año else 'Histórico'}", styles['Heading2']))
        story.append(Spacer(1, 0.3*inch))

        # Fecha de generación
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        story.append(Paragraph(f"Generado: {fecha}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))

        # Sección 1: Resumen Ejecutivo
        story.append(Paragraph("1. Resumen Ejecutivo", heading_style))
        
        summary_data = [
            ['Métrica', 'Valor'],
            ['Número de remitos', f"{company_data.get('num_remitos', 0):,}"],
            ['Huella promedio', f"{company_data.get('huella_promedio', 0):.2f} kg CO₂/m³"],
            ['Resistencia promedio', f"{company_data.get('resistencia_promedio', 0):.1f} MPa"],
            ['Contenido cemento', f"{company_data.get('cemento_promedio', 0):.0f} kg/m³"],
            ['Volumen total', f"{company_data.get('volumen_total', 0):,.0f} m³"]
        ]

        table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))

        # Sección 2: Análisis de IA
        story.append(Paragraph("2. Análisis Comparativo", heading_style))
        
        # Parsear respuesta de IA
        ai_text = ai_analysis.get('answer', 'No disponible')
        for line in ai_text.split('\n'):
            if line.strip():
                story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))

        story.append(Spacer(1, 0.3*inch))

        # Sección 3: Gráficos
        story.append(PageBreak())
        story.append(Paragraph("3. Visualizaciones", heading_style))

        # Gráfico 1: Comparación de huella
        benchmarks_ref = {
            'regional': 250,
            'gcca_a': 150,
            'gcca_c': 300
        }
        chart1_path = self._create_chart_huella_comparacion(company_data, benchmarks_ref)
        story.append(Image(chart1_path, width=6*inch, height=3.6*inch))
        story.append(Spacer(1, 0.3*inch))

        # Gráfico 2: Distribución de productos
        if productos_data:
            chart2_path = self._create_chart_distribucion_resistencias(productos_data)
            story.append(Image(chart2_path, width=6*inch, height=3.6*inch))
            story.append(Spacer(1, 0.3*inch))

        # Sección 4: Top Productos
        story.append(PageBreak())
        story.append(Paragraph("4. Top Productos por Volumen", heading_style))

        if productos_data:
            productos_table_data = [['Resistencia', 'Huella', 'Volumen', 'Remitos']]
            for prod in productos_data[:10]:
                productos_table_data.append([
                    f"{prod.get('resistencia', 0):.0f} MPa",
                    f"{prod.get('huella_promedio', 0):.2f}",
                    f"{prod.get('volumen_total', 0):,.0f} m³",
                    f"{prod.get('num_remitos', 0):,}"
                ])

            prod_table = Table(productos_table_data, colWidths=[1.5*inch, 1.5*inch, 1.8*inch, 1.2*inch])
            prod_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2E86AB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
            ]))
            story.append(prod_table)

        story.append(Spacer(1, 0.3*inch))

        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_text = f"Informe generado por Piloto IA FICEM BD | {fecha}"
        story.append(Paragraph(footer_text, styles['Normal']))

        # Construir PDF
        doc.build(story)

        # Limpiar archivos temporales
        if 'chart1_path' in locals():
            os.unlink(chart1_path)
        if 'chart2_path' in locals():
            os.unlink(chart2_path)

        print(f"✅ Informe generado: {filepath}")
        return filepath


# Ejemplo de uso
if __name__ == "__main__":
    generator = BenchmarkingReportPDF(
        llm_model="qwen2.5:3b",
        use_claude=False,
        output_dir="./reports"
    )

    # Generar informe para MZMA 2024
    pdf_path = generator.generate_company_report(
        compania="MZMA",
        año=2024,
        benchmark_type="gcca"
    )

    print(f"\n📄 PDF generado: {pdf_path}")
