# backend/herramientas/herramienta_rag.py

from typing import List
from ..configuracion_vectores import obtener_almacen_de_vectores, generar_embedding

def buscar_en_base_de_conocimiento(consulta: str, n_resultados: int = 5) -> List[str]:
    """
    Realiza una búsqueda de similitud en la base de datos vectorial (ChromaDB)
    y devuelve los fragmentos de texto más relevantes.

    Args:
        consulta (str): La pregunta o texto para buscar.
        n_resultados (int): El número de fragmentos más relevantes a devolver.

    Returns:
        List[str]: Una lista de los textos de los fragmentos encontrados.
    """
    print(f"\n--- [HERRAMIENTA RAG] Realizando búsqueda vectorial para: '{consulta[:50]}...'")
    
    try:
        # 1. Obtenemos acceso a la colección de ChromaDB.
        almacen = obtener_almacen_de_vectores()
        coleccion = almacen["coleccion"]
        
        # 2. Convertimos la consulta del usuario en un vector (embedding).
        # Es crucial que usemos la misma función que usamos para la ingesta.
        query_embedding = generar_embedding(consulta)
        
        # 3. Realizamos la búsqueda en la colección.
        # ChromaDB buscará los 'n_resultados' vectores más cercanos al de nuestra consulta.
        resultados = coleccion.query(
            query_embeddings=[query_embedding],
            n_results=n_resultados
        )
        
        print(f"--- [HERRAMIENTA RAG] Resultados raw de ChromaDB: {resultados}") # Línea de debug opcional, puedes quitarla luego
        
        # 4. Extraemos y devolvemos solo el texto de los documentos encontrados.
        # CORRECCIÓN: Verificamos si 'documents' es una lista y si tiene elementos antes de acceder a [0].
        # ChromaDB puede devolver {'documents': [], 'metadatas': [], ...} si no hay resultados,
        # o {'documents': [['doc1', 'doc2']], ...} si hay resultados.
        documentos_encontrados = []
        if isinstance(resultados, dict) and 'documents' in resultados:
            docs_lista = resultados['documents']
            if docs_lista and len(docs_lista) > 0 and isinstance(docs_lista[0], list):
                 # Asumiendo que docs_lista[0] contiene los documentos reales
                 documentos_encontrados = docs_lista[0] # Accedemos al primer (y único) subconjunto de resultados
            # Si docs_lista está vacío o no es una lista de listas, documentos_encontrados sigue siendo []
        else:
            # Si resultados no es un dict o no tiene 'documents', devolvemos lista vacía
            print("--- [HERRAMIENTA RAG] Advertencia: La respuesta de ChromaDB no tiene el formato esperado.")
        
        print(f"--- [HERRAMIENTA RAG] Se encontraron {len(documentos_encontrados)} fragmentos relevantes.")
        
        return documentos_encontrados

    except Exception as e:
        print(f"--- [HERRAMIENTA RAG] ERROR: Ocurrió un error durante la búsqueda vectorial: {e}")
        # Devolvemos una lista vacía en caso de error para no detener el flujo.
        return []