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
        
        # 4. Extraemos y devolvemos solo el texto de los documentos encontrados.
        documentos_encontrados = resultados['documents'][0] if resultados['documents'] else []
        
        print(f"--- [HERRAMIENTA RAG] Se encontraron {len(documentos_encontrados)} fragmentos relevantes.")
        
        return documentos_encontrados

    except Exception as e:
        print(f"--- [HERRAMIENTA RAG] ERROR: Ocurrió un error durante la búsqueda vectorial: {e}")
        # Devolvemos una lista vacía en caso de error para no detener el flujo.
        return []