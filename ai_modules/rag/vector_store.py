"""
Gestor de Vector Store (ChromaDB)
Piloto IA - FICEM BD

Maneja la base de datos vectorial para RAG.
"""

from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma


class VectorStoreManager:
    """
    Gestiona ChromaDB para almacenar y recuperar embeddings.
    """

    def __init__(
        self,
        persist_directory: str = "data/vector_store/chroma_db",
        collection_name: str = "ficem_tech_docs",
        embedding_model: str = "mxbai-embed-large"
    ):
        """
        Inicializa el gestor de vector store.

        Args:
            persist_directory: Directorio para persistir ChromaDB
            collection_name: Nombre de la colección
            embedding_model: Modelo de Ollama para embeddings
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.collection_name = collection_name

        # Configurar embeddings con Ollama
        print(f"🔧 Inicializando embeddings con {embedding_model}...")
        self.embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url="http://localhost:11434"
        )

        # Inicializar cliente ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory)
        )

        # Vectorstore (se carga o crea)
        self.vectorstore = None

    def load_or_create_vectorstore(self) -> Chroma:
        """
        Carga el vectorstore existente o crea uno nuevo.

        Returns:
            Instancia de Chroma
        """
        print(f"📂 Cargando vectorstore: {self.collection_name}")

        self.vectorstore = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings
        )

        # Verificar si ya tiene datos
        try:
            count = self.vectorstore._collection.count()
            if count > 0:
                print(f"✅ Vectorstore cargado: {count} documentos existentes")
            else:
                print(f"📝 Vectorstore creado (vacío)")
        except:
            print(f"📝 Vectorstore creado (nuevo)")

        return self.vectorstore

    def add_documents(self, documents: List[Dict]) -> None:
        """
        Agrega documentos al vectorstore.

        Args:
            documents: Lista de documentos con formato:
                [{"text": "...", "metadata": {...}}, ...]
        """
        if not self.vectorstore:
            self.load_or_create_vectorstore()

        if not documents:
            print("⚠️  No hay documentos para agregar")
            return

        # Extraer textos y metadatos
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]

        print(f"📝 Agregando {len(documents)} documentos al vectorstore...")

        # Agregar en lotes para evitar problemas de memoria
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]

            self.vectorstore.add_texts(
                texts=batch_texts,
                metadatas=batch_metadatas
            )

            print(f"  ✓ Lote {i // batch_size + 1}: {len(batch_texts)} docs")

        print(f"✅ {len(documents)} documentos agregados exitosamente")

    def search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Busca documentos relevantes.

        Args:
            query: Consulta de búsqueda
            k: Número de resultados
            filter: Filtros de metadatos

        Returns:
            Lista de documentos relevantes con scores
        """
        if not self.vectorstore:
            self.load_or_create_vectorstore()

        # Búsqueda por similitud
        if filter:
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter
            )
        else:
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k
            )

        # Formatear resultados
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            })

        return formatted_results

    def get_retriever(self, k: int = 5, search_type: str = "similarity"):
        """
        Obtiene un retriever de LangChain.

        Args:
            k: Número de documentos a recuperar
            search_type: Tipo de búsqueda ('similarity', 'mmr')

        Returns:
            Retriever de LangChain
        """
        if not self.vectorstore:
            self.load_or_create_vectorstore()

        return self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k}
        )

    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del vectorstore.

        Returns:
            Diccionario con estadísticas
        """
        if not self.vectorstore:
            self.load_or_create_vectorstore()

        try:
            count = self.vectorstore._collection.count()

            # Obtener TODOS los metadatos para extraer fuentes únicas
            all_data = self.vectorstore._collection.get(
                include=['metadatas']
            )

            sources = set()
            doc_types = set()

            if all_data and 'metadatas' in all_data:
                for meta in all_data['metadatas']:
                    if meta:
                        if 'source' in meta:
                            sources.add(meta['source'])
                        if 'document_type' in meta:
                            doc_types.add(meta['document_type'])

            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "unique_sources": len(sources),
                "sources": sorted(list(sources)),  # Ordenar alfabéticamente
                "document_types": sorted(list(doc_types))
            }
        except Exception as e:
            print(f"Error obteniendo stats: {e}")
            return {"error": str(e)}

    def clear_collection(self) -> None:
        """
        Elimina todos los documentos de la colección.
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"✅ Colección '{self.collection_name}' eliminada")
            self.vectorstore = None
        except Exception as e:
            print(f"Error eliminando colección: {e}")


# Ejemplo de uso
if __name__ == "__main__":
    # Inicializar
    vsm = VectorStoreManager()
    vsm.load_or_create_vectorstore()

    # Ver stats
    stats = vsm.get_stats()
    print("\n📊 Estadísticas del vectorstore:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
