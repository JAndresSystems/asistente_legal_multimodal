# backend/configuracion_vectores.py

import chromadb
import google.generativeai as genai
import os
from dotenv import load_dotenv

# --- CARGA DE VARIABLES DE ENTORNO ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("La variable de entorno GOOGLE_API_KEY no ha sido configurada.")

# --- CONFIGURACION GLOBAL (SINGLETON) ---
_singleton_instances = {}

# --- CONSTANTES ---
DIRECTORIO_PERSISTENTE = "chroma_db_data"
NOMBRE_DE_LA_COLECCION = "normativa_colombiana"
# --- INICIO DE LA CORRECCION: Guardamos el nombre del modelo como string ---
NOMBRE_MODELO_EMBEDDINGS = "models/embedding-001"
# --- FIN DE LA CORRECCION ---

def obtener_almacen_de_vectores():
    """
    Función Singleton para obtener el cliente de ChromaDB, la colección
    y el modelo de embeddings.
    """
    global _singleton_instances

    if "vector_store" in _singleton_instances:
        return _singleton_instances["vector_store"]

    print(">>> INICIALIZANDO ALMACEN DE VECTORES (CHROMA DB y GOOGLE EMBEDDINGS)...")

    # 1. Configurar la API de Google
    genai.configure(api_key=GOOGLE_API_KEY)

    # 2. Inicializar el cliente de ChromaDB.
    cliente_chroma = chromadb.PersistentClient(path=DIRECTORIO_PERSISTENTE)

    # 3. Obtener (o crear si no existe) nuestra colección de vectores.
    coleccion = cliente_chroma.get_or_create_collection(name=NOMBRE_DE_LA_COLECCION)

    print(">>> INICIALIZACIÓN COMPLETADA.")

    _singleton_instances["vector_store"] = {
        "cliente": cliente_chroma,
        "coleccion": coleccion,
    }
    return _singleton_instances["vector_store"]

# --- FUNCION DE UTILIDAD PARA GENERAR EMBEDDINGS (CORREGIDA) ---
def generar_embedding(texto: str):
    """
    Toma un fragmento de texto y utiliza el modelo de Google para convertirlo
    en un vector (embedding).
    """
    # --- INICIO DE LA CORRECCION ---
    # La función embed_content es de alto nivel, no necesita el objeto del modelo,
    # solo su nombre en formato string.
    resultado = genai.embed_content(
        model=NOMBRE_MODELO_EMBEDDINGS, # Pasamos el string directamente
        content=texto,
        task_type="RETRIEVAL_DOCUMENT"
    )
    return resultado['embedding']
    # --- FIN DE LA CORRECCION ---