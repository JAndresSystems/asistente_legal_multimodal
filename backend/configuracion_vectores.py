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
NOMBRE_MODELO_EMBEDDINGS = "models/embedding-001"

def obtener_almacen_de_vectores():
    """
    Función Singleton para conectarse a una base de datos ChromaDB YA EXISTENTE.
    No intenta crearla ni poblarla.
    """
    global _singleton_instances

    if "vector_store" in _singleton_instances:
        return _singleton_instances["vector_store"]

    print(">>> CONECTANDO AL ALMACEN DE VECTORES EXISTENTE...")

    genai.configure(api_key=GOOGLE_API_KEY)
    cliente_chroma = chromadb.PersistentClient(path=DIRECTORIO_PERSISTENTE)
    coleccion = cliente_chroma.get_collection(name=NOMBRE_DE_LA_COLECCION)
    
    print(f">>> Conexión exitosa. La colección '{NOMBRE_DE_LA_COLECCION}' contiene {coleccion.count()} documentos.")
    _singleton_instances["vector_store"] = {
        "cliente": cliente_chroma,
        "coleccion": coleccion,
    }
    return _singleton_instances["vector_store"]

def generar_embedding(texto: str):
    """
    Toma un fragmento de texto y utiliza el modelo de Google para convertirlo
    en un vector (embedding).
    """
    resultado = genai.embed_content(
        model=NOMBRE_MODELO_EMBEDDINGS,
        content=texto,
        task_type="RETRIEVAL_DOCUMENT"
    )
    return resultado['embedding']