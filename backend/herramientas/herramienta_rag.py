#C:\react\asistente_legal_multimodal\backend\herramientas\herramienta_rag.py
import os
import glob
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import faiss
import numpy as np
from typing import List, Dict

# --- CONFIGURACIÓN DEL RAG ---
MODELO_EMBEDDINGS = 'all-MiniLM-L6-v2'
RUTA_BASE = os.path.join(os.path.dirname(__file__), '..', 'datos', 'base_de_conocimiento_juridico')

# --- NUEVA ESTRUCTURA DE DATOS PARA MÚLTIPLES ÍNDICES ---
# Usaremos un diccionario para almacenar un índice FAISS y sus documentos por cada área de competencia.
indices_rag: Dict[str, Dict] = {}
modelo_embeddings = None

def inicializar_bases_de_conocimiento():
    """
    Carga, procesa y vectoriza TODAS las bases de conocimiento especializadas por área.
    Esta versión es robusta y omite carpetas vacías para evitar errores.
    """
    global indices_rag, modelo_embeddings
    
    if indices_rag: return

    try:
        print("TOOL-SETUP (RAG): Iniciando la carga de MÚLTIPLES bases de conocimiento...")
        print("TOOL-SETUP (RAG): Cargando el modelo de embeddings (SentenceTransformer)...")
        modelo_embeddings = SentenceTransformer(MODELO_EMBEDDINGS)

        for area_dir in os.listdir(RUTA_BASE):
            ruta_area = os.path.join(RUTA_BASE, area_dir)
            if os.path.isdir(ruta_area):
                area_competencia = area_dir
                print(f"--- Procesando área: {area_competencia} ---")

                textos_completos = []
                for filepath in glob.glob(os.path.join(ruta_area, "*.txt")):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        textos_completos.append(f.read())
                
                # --- CAMBIO CLAVE ---
                # Si no se encontraron archivos de texto, se omite esta área y se continúa.
                if not textos_completos:
                    print(f"    Advertencia: No se encontraron archivos .txt en {area_competencia}. Omitiendo.")
                    continue

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                documentos_fragmentados = text_splitter.create_documents(textos_completos)
                textos_fragmentados = [doc.page_content for doc in documentos_fragmentados]
                print(f"    - {len(textos_fragmentados)} fragmentos de texto encontrados.")

                embeddings = modelo_embeddings.encode(textos_fragmentados, convert_to_tensor=False)
                dimension_vector = embeddings.shape[1]
                indice_faiss = faiss.IndexFlatL2(dimension_vector)
                indice_faiss.add(np.array(embeddings, dtype=np.float32))

                indices_rag[area_competencia] = {
                    "indice": indice_faiss,
                    "fragmentos": textos_fragmentados
                }
                print(f"    - Índice para '{area_competencia}' creado exitosamente.")

        print("SUCCESS (RAG): Todas las bases de conocimiento especializadas han sido cargadas.")

    except Exception as e:
        print(f"ERROR-CRITICO (RAG): No se pudo inicializar una o más bases de conocimiento: {e}")
        indices_rag.clear()

def buscar_en_base_de_conocimiento(consulta: str, area_competencia: str, k: int = 3) -> List[str]:
    """
    Busca en la base de conocimiento específica del área de competencia.
    """
    if not indices_rag or area_competencia not in indices_rag:
        return [f"Error: La base de conocimiento para '{area_competencia}' no está disponible."]
    
    try:
        # 1. Seleccionar el índice y los fragmentos correctos.
        rag_especializado = indices_rag[area_competencia]
        indice_faiss = rag_especializado["indice"]
        fragmentos = rag_especializado["fragmentos"]
        
        # 2. Convertir la consulta en un vector (reutilizando el modelo ya cargado).
        vector_consulta = modelo_embeddings.encode([consulta])
        
        # 3. Buscar en el índice FAISS.
        distancias, indices = indice_faiss.search(np.array(vector_consulta, dtype=np.float32), k)
        
        # 4. Recuperar los fragmentos de texto.
        resultados = [fragmentos[i] for i in indices[0]]
        return resultados
        
    except Exception as e:
        print(f"ERROR (RAG): Fallo durante la búsqueda en '{area_competencia}': {e}")
        return [f"Error durante la búsqueda RAG: {e}"]

# Inicialización automática al importar el módulo.
inicializar_bases_de_conocimiento()