"""
Módulo de generación de informes
Piloto IA - FICEM BD

Generadores de informes PDF y Excel con análisis de IA.
"""

from .pdf_generator import BenchmarkingReportPDF
from .excel_generator import BenchmarkingReportExcel

__all__ = [
    'BenchmarkingReportPDF',
    'BenchmarkingReportExcel'
]
