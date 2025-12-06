# Módulos de IA - FICEM BD

Sistema de Inteligencia Artificial para análisis de benchmarking y predicción de huella de carbono en la industria del cemento/concreto.

## 📁 Estructura

```
ai_modules/
├── rag/                    # Retrieval Augmented Generation
│   ├── embeddings.py      # Generación de embeddings
│   ├── vector_store.py    # Gestión de ChromaDB
│   ├── retriever.py       # Recuperación de contexto
│   ├── chains.py          # LangChain chains
│   └── prompts/           # Templates de prompts
├── ml/                     # Machine Learning
│   ├── preprocessor.py    # Feature engineering
│   ├── models.py          # Modelos ML
│   ├── predictor.py       # Predicción de huella
│   ├── anomaly_detector.py # Detección de outliers
│   └── saved_models/      # Modelos entrenados
└── report_generator/       # Generación de informes
    ├── pdf_generator.py
    ├── excel_generator.py
    └── templates/
```

## 🚀 Casos de Uso Principales

### 1. Benchmarking Comparativo (RAG)
Compara el desempeño de una compañía contra benchmarks regionales/internacionales.

```python
from ai_modules.rag.chains import BenchmarkingChain

chain = BenchmarkingChain()
response = chain.run("Compara MZMA 2024 con promedio regional y GCCA")
```

### 2. Predicción de Huella (ML)
Predice la huella CO₂ de un concreto antes de producirlo.

```python
from ai_modules.ml.predictor import HuellaPredictor

predictor = HuellaPredictor()
huella = predictor.predict(
    resistencia=25,
    contenido_cemento=320,
    tipo_cemento="CPC"
)
```

### 3. Detección de Anomalías (ML)
Identifica remitos con huellas anormales.

```python
from ai_modules.ml.anomaly_detector import AnomalyDetector

detector = AnomalyDetector()
anomalias = detector.detect(df_remitos, threshold=0.05)
```

### 4. Generación de Informes
Genera PDF/Excel con análisis completo.

```python
from ai_modules.report_generator import InformeGenerator

generator = InformeGenerator()
generator.generar_informe_benchmarking(
    compania="MZMA",
    año=2024,
    output_path="informe_mzma_2024.pdf"
)
```

## 🔧 Configuración

### 1. Variables de entorno (.env)
```bash
# Modelo LLM
OLLAMA_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434

# Embeddings
EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Vector Store
CHROMA_PERSIST_DIR=data/vector_store

# Base de datos
DB_PATH=/home/cpinilla/databases/ficem_bd/data
```

### 2. Instalar Ollama (modelo local)
Ver instrucciones en: [docs/INSTALACION_OLLAMA.md](../docs/INSTALACION_OLLAMA.md)

### 3. Instalar dependencias Python
```bash
source venv/bin/activate
pip install -r requirements_ia_piloto.txt
```

## 📊 Datos utilizados

### Datos de producción
- **remitos_concretos**: 255K+ remitos con huella CO₂
- **cementos**: Huellas por planta/año
- **plantas_latam**: 265 plantas geolocalizadas

### Datos de benchmarking
- **gnr_data**: 44 indicadores de 21 entidades
- **GCCA_EPD_5_1**: Bandas de clasificación
- **data_global**: Indicadores por país

### Documentos de referencia (para RAG)
- Metodología GCCA
- Mejores prácticas de reducción de huella
- Definiciones técnicas del sector

## 🧪 Testing

```bash
# Tests unitarios
pytest ai_modules/tests/

# Test de RAG
python -m ai_modules.rag.test_retrieval

# Test de predictor
python -m ai_modules.ml.test_predictor
```

## 📈 Métricas de desempeño

### RAG
- Precisión de respuestas: >85%
- Tiempo de respuesta: <10s
- Relevancia de contexto recuperado: >90%

### ML
- R² del predictor: >0.80
- RMSE: <20 kg CO₂/m³
- Recall detección anomalías: >80%

## 🔄 Workflow de desarrollo

1. **EDA**: Análisis exploratorio en `notebooks/`
2. **Prototipo**: Código experimental en notebooks
3. **Implementación**: Código productivo en `ai_modules/`
4. **Testing**: Validación en `ai_modules/tests/`
5. **Integración**: UI en `pages/ai/`

## 📝 Próximos pasos

- [ ] Completar FASE 1: EDA y preparación de datos
- [ ] FASE 2: Entrenar modelos ML
- [ ] FASE 3: Implementar RAG con Ollama
- [ ] FASE 4: Crear interfaces en Streamlit
- [ ] FASE 5: Testing y refinamiento

---

**Documentación completa**: [docs/PILOTO_IA_PLAN.md](../docs/PILOTO_IA_PLAN.md)
**Progreso**: [docs/PILOTO_IA_PROGRESO.json](../docs/PILOTO_IA_PROGRESO.json)
