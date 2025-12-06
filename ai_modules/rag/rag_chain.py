"""
Chain de RAG para consultas
Piloto IA - FICEM BD

Integra retriever + LLM para responder preguntas.
Usa el enfoque moderno de LangChain con create_retrieval_chain.
"""

import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain_anthropic import ChatAnthropic
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

from ai_modules.rag.vector_store import VectorStoreManager
from ai_modules.rag.sql_tool import SQLTool

# Cargar variables de entorno
load_dotenv()


class RAGChain:
    """
    Chain de RAG que combina retrieval con generación de respuestas.
    Usa create_retrieval_chain (enfoque moderno de LangChain).
    """

    def __init__(
        self,
        llm_model: str = "qwen2.5:7b",
        temperature: float = 0.1,
        top_k: int = 5,
        use_claude: bool = False
    ):
        """
        Inicializa el chain de RAG.

        Args:
            llm_model: Modelo a usar (Ollama o Claude)
            temperature: Temperatura para generación (0-1)
            top_k: Número de documentos a recuperar
            use_claude: Si True, usa Claude API en lugar de Ollama
        """
        self.llm_model = llm_model
        self.temperature = temperature
        self.top_k = top_k
        self.use_claude = use_claude

        # Inicializar LLM según el proveedor
        if use_claude:
            # Usar Claude API
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY no encontrada en variables de entorno")

            print(f"🤖 Inicializando Claude: {llm_model}")
            self.llm = ChatAnthropic(
                model=llm_model,
                temperature=temperature,
                anthropic_api_key=api_key
            )
        else:
            # Usar Ollama local
            print(f"🤖 Inicializando Ollama: {llm_model}")
            self.llm = OllamaLLM(
                model=llm_model,
                base_url="http://localhost:11434",
                temperature=temperature
            )

        # Inicializar vector store manager
        self.vsm = VectorStoreManager()
        self.vsm.load_or_create_vectorstore()

        # Obtener retriever
        self.retriever = self.vsm.get_retriever(k=top_k)

        # Inicializar SQL tool
        self.sql_tool = SQLTool()

        # Crear chain
        self.chain = None
        self._create_chain()

    def _create_chain(self) -> None:
        """
        Crea el chain de RAG usando create_retrieval_chain.
        """
        # Prompt template personalizado
        system_prompt = """Eres un asistente experto en descarbonización de la industria del cemento y concreto.

Usa el siguiente contexto para responder la pregunta. Si no sabes la respuesta, di que no lo sabes, no inventes información.

IMPORTANTE: Cuando uses información de los documentos del contexto, SIEMPRE indica la fuente de la siguiente manera:
- Si es un dato específico, menciona: "según [nombre del documento]..."
- Si son múltiples fuentes, menciona: "de acuerdo con [doc1] y [doc2]..."
- Al final de tu respuesta, lista las fuentes consultadas

Contexto:
{context}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])

        # Crear document chain
        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)

        # Crear retrieval chain
        self.chain = create_retrieval_chain(self.retriever, question_answer_chain)

        print("✅ Chain de RAG creado")

    def query(self, question: str) -> Dict:
        """
        Realiza una consulta al sistema RAG.

        Args:
            question: Pregunta del usuario

        Returns:
            Diccionario con respuesta y fuentes
        """
        if not self.chain:
            raise ValueError("Chain no inicializado")

        print(f"\n❓ Pregunta: {question}")
        print("⏳ Procesando...")

        # Ejecutar query (create_retrieval_chain usa "input" en lugar de "query")
        result = self.chain.invoke({"input": question})

        # Formatear respuesta
        response = {
            "question": question,
            "answer": result["answer"],
            "sources": []
        }

        # Agregar fuentes (create_retrieval_chain retorna "context" con los docs)
        if "context" in result:
            for doc in result["context"]:
                source_info = {
                    "source": doc.metadata.get("source", "Unknown"),
                    "document_type": doc.metadata.get("document_type", "Unknown"),
                    "chunk_id": doc.metadata.get("chunk_id", 0),
                    "text_preview": doc.page_content[:200]
                }
                response["sources"].append(source_info)

        return response

    def query_simple(self, question: str) -> str:
        """
        Realiza una consulta y devuelve solo la respuesta.

        Args:
            question: Pregunta del usuario

        Returns:
            Respuesta del LLM
        """
        result = self.query(question)
        return result["answer"]

    def query_with_context(
        self,
        question: str,
        additional_context: Optional[str] = None
    ) -> Dict:
        """
        Realiza una consulta con contexto adicional.

        Args:
            question: Pregunta del usuario
            additional_context: Contexto adicional (ej: datos de BD)

        Returns:
            Diccionario con respuesta y fuentes
        """
        # Si hay contexto adicional, agregarlo a la pregunta
        if additional_context:
            enhanced_question = f"""
Contexto adicional de la base de datos:
{additional_context}

Pregunta: {question}
"""
        else:
            enhanced_question = question

        return self.query(enhanced_question)

    def query_hybrid(self, question: str) -> Dict:
        """
        Consulta híbrida que combina RAG con SQL según la pregunta.

        Detecta automáticamente si la pregunta requiere:
        - Datos numéricos/estadísticos → SQL
        - Conocimiento técnico/conceptual → RAG
        - Ambos → Combina SQL + RAG

        Args:
            question: Pregunta del usuario

        Returns:
            Diccionario con respuesta y fuentes
        """
        # Palabras clave que indican necesidad de SQL
        sql_keywords = [
            "cuál es", "cuántos", "promedio", "total", "suma",
            "mzma", "cemex", "2024", "2023", "2022",
            "huella promedio", "top", "mayor", "menor",
            "estadísticas", "datos de", "volumen"
        ]

        question_lower = question.lower()
        needs_sql = any(keyword in question_lower for keyword in sql_keywords)

        if needs_sql:
            print("🔍 Detectada consulta que requiere datos → usando SQL")

            # Intentar extraer parámetros de la pregunta
            sql_context = None

            # Detectar compañía y año
            if "mzma" in question_lower:
                compania = "MZMA"
            elif "cemex" in question_lower:
                compania = "CEMEX"
            elif "melón" in question_lower or "melon" in question_lower:
                compania = "melón_main_old"
            else:
                compania = None

            # Detectar año
            import re
            year_match = re.search(r'\b(202[0-9])\b', question)
            año = int(year_match.group(1)) if year_match else None

            # Consultar SQL según el tipo de pregunta
            if compania and ("huella" in question_lower or "promedio" in question_lower or "dosis" in question_lower or "cemento" in question_lower):
                result = self.sql_tool.get_huella_promedio_compania(compania, año)
                if result["success"] and result["rows"]:
                    data = result["rows"][0]

                    # Manejar None values de forma segura
                    num_remitos = data.get('num_remitos', 0) or 0
                    huella = data.get('huella_promedio') or 0
                    resistencia = data.get('resistencia_promedio') or 0
                    cemento = data.get('cemento_promedio') or 0
                    volumen = data.get('volumen_total') or 0

                    sql_context = f"""
Datos de {compania} {f'en {año}' if año else 'en todos los años'}:
- Número de remitos: {num_remitos:,}
- Huella promedio: {huella:.2f} kg CO₂/m³
- Resistencia promedio: {resistencia:.1f} MPa
- Contenido cemento promedio: {cemento:.0f} kg/m³
- Volumen total: {volumen:,.0f} m³
"""
            elif "top" in question_lower or "mayor" in question_lower:
                result = self.sql_tool.get_top_productos_huella(limit=5)
                if result["success"] and result["rows"]:
                    sql_context = "Top 5 productos con mayor huella:\n"
                    for i, row in enumerate(result["rows"], 1):
                        sql_context += f"{i}. {row['compania']} - {row['resistencia']} MPa: {row['huella_promedio']:.2f} kg CO₂/m³ ({row['volumen_total']:,.0f} m³)\n"

            # Combinar SQL context con RAG
            if sql_context:
                return self.query_with_context(question, sql_context)
            else:
                # Si no se pudo extraer info, usar solo RAG
                return self.query(question)
        else:
            # Pregunta conceptual/técnica → solo RAG
            print("📚 Consulta conceptual → usando RAG")
            return self.query(question)


class BenchmarkingChain(RAGChain):
    """
    Chain especializado para benchmarking.
    """

    def compare_with_benchmark(
        self,
        company_data: Dict,
        benchmark_type: str = "gcca"
    ) -> Dict:
        """
        Compara datos de empresa con benchmarks.

        Args:
            company_data: Diccionario con datos de la empresa
            benchmark_type: Tipo de benchmark (gcca, gnr, regional)

        Returns:
            Análisis comparativo
        """
        # Construir contexto desde datos
        context = f"""
Datos de la compañía:
- Nombre: {company_data.get('compania', 'N/A')}
- Año: {company_data.get('año', 'N/A')}
- Huella promedio: {company_data.get('huella_promedio', 'N/A')} kg CO₂/m³
- Resistencia típica: {company_data.get('resistencia_promedio', 'N/A')} MPa
- Volumen anual: {company_data.get('volumen_anual', 'N/A')} m³
"""

        question = f"""
Basándote en los datos de la compañía y los documentos técnicos disponibles:

1. ¿Cómo se compara esta huella de carbono con los benchmarks {benchmark_type.upper()}?
2. ¿En qué banda o categoría se ubicaría?
3. ¿Cuáles son las principales oportunidades de mejora?
4. ¿Qué tecnologías o prácticas recomiendas para reducir emisiones?

Proporciona una respuesta estructurada con números específicos cuando sea posible.
"""

        return self.query_with_context(question, context)

    def analyze_portfolio(self, products_data: List[Dict]) -> Dict:
        """
        Analiza un portafolio de productos.

        Args:
            products_data: Lista de productos con huella y volumen

        Returns:
            Análisis de portafolio
        """
        # Construir contexto
        context = "Portafolio de productos:\n"
        for i, product in enumerate(products_data, 1):
            context += f"""
{i}. {product.get('nombre', f'Producto {i}')}
   - Resistencia: {product.get('resistencia', 'N/A')} MPa
   - Huella: {product.get('huella_co2', 'N/A')} kg CO₂/m³
   - Volumen anual: {product.get('volumen', 'N/A')} m³
"""

        question = """
Analiza este portafolio de productos y recomienda:

1. ¿Qué productos deberían optimizarse primero (mayor impacto)?
2. ¿Cuáles tienen potencial de mejora factible?
3. ¿Qué estrategias específicas recomiendas para cada producto prioritario?
4. ¿Cuál sería la reducción estimada de emisiones si se implementan las mejoras?

Prioriza por impacto (volumen × huella) y factibilidad.
"""

        return self.query_with_context(question, context)


# Ejemplo de uso
if __name__ == "__main__":
    # Crear chain
    rag = RAGChain(temperature=0.1, top_k=5)

    # Test simple
    print("\n" + "=" * 70)
    print("TEST DE RAG CHAIN")
    print("=" * 70)

    questions = [
        "¿Cuáles son las principales tecnologías para reducir emisiones en cemento?",
        "¿Qué dice sobre el uso de combustibles alternativos?",
        "¿Cuáles son las metas de reducción de CO2 para 2030?"
    ]

    for q in questions:
        result = rag.query(q)
        print(f"\n❓ {result['question']}")
        print(f"💬 {result['answer']}")
        print(f"📚 Fuentes: {len(result['sources'])}")
        print("-" * 70)
