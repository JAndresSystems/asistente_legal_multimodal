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
        
        print(f"--- [HERRAMIENTA RAG] Resultados raw de ChromaDB: {resultados}") # Línea de debug
        print(f"--- [HERRAMIENTA RAG] Tipo de resultados raw: {type(resultados)}") # Línea de debug

        # 4. Extraemos y devolvemos solo el texto de los documentos encontrados.
        # CORRECCIÓN: Manejo aún más defensivo de la respuesta de ChromaDB.
        documentos_encontrados = []
        
        # Verificamos si 'resultados' es un diccionario
        if not isinstance(resultados, dict):
            print(f"--- [HERRAMIENTA RAG] Advertencia: La respuesta de ChromaDB no es un diccionario, es {type(resultados)}.")
            return []
        
        # Verificamos si la clave 'documents' existe en el diccionario
        if 'documents' not in resultados:
            print(f"--- [HERRAMIENTA RAG] Advertencia: La clave 'documents' no está en la respuesta de ChromaDB.")
            return []
            
        docs_lista = resultados['documents']
        print(f"--- [HERRAMIENTA RAG] docs_lista raw: {docs_lista}, tipo: {type(docs_lista)}") # Línea de debug
        
        # Verificamos si docs_lista es una lista
        if not isinstance(docs_lista, list):
            print(f"--- [HERRAMIENTA RAG] Advertencia: 'documents' no es una lista, es {type(docs_lista)}.")
            # Aquí podría estar el problema: si docs_lista es un int, causaría el error en len()
            if isinstance(docs_lista, int):
                 print(f"--- [HERRAMIENTA RAG] ERROR DETECTADO: 'documents' es un entero: {docs_lista}.")
            return []
        
        # Verificamos si la lista de documentos tiene al menos un elemento
        if len(docs_lista) == 0:
            print("--- [HERRAMIENTA RAG] No se encontraron documentos (lista vacía).")
            return []
        
        # El primer nivel de la lista son las listas de resultados para cada embedding de consulta.
        # Como pasamos [query_embedding], solo esperamos un subconjunto: docs_lista[0].
        primer_subconjunto = docs_lista[0]
        print(f"--- [HERRAMIENTA RAG] primer_subconjunto: {primer_subconjunto}, tipo: {type(primer_subconjunto)}") # Línea de debug
        
        # Verificamos si el primer subconjunto es una lista
        if not isinstance(primer_subconjunto, list):
            print(f"--- [HERRAMIENTA RAG] Advertencia: El primer subconjunto de 'documents' no es una lista, es {type(primer_subconjunto)}.")
            if isinstance(primer_subconjunto, int): # Verificamos si es un entero aquí también
                 print(f"--- [HERRAMIENTA RAG] ERROR DETECTADO: El primer subconjunto es un entero: {primer_subconjunto}.")
            return []
        
        # Extraemos los documentos de texto
        documentos_encontrados = primer_subconjunto

        print(f"--- [HERRAMIENTA RAG] Se encontraron {len(documentos_encontrados)} fragmentos relevantes.")
        return documentos_encontrados

    except Exception as e:
        print(f"--- [HERRAMIENTA RAG] ERROR: Ocurrió un error durante la búsqueda vectorial: {e}")
        import traceback
        traceback.print_exc() # Imprime el traceback completo para depurar mejor
        # Devolvemos una lista vacía en caso de error para no detener el flujo.
        return []