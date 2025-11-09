# backend/scripts/ingestar_documentos.py

import os
import chromadb # Importar ChromaDB directamente
import google.generativeai as genai # Importar la API de Google directamente
from pypdf import PdfReader # Importar PdfReader correctamente
from langchain.text_splitter import RecursiveCharacterTextSplitter # Importar el splitter de LangChain
from dotenv import load_dotenv # Importar para cargar variables de entorno localmente

# --- CARGA DE VARIABLES DE ENTORNO ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("La variable de entorno GOOGLE_API_KEY no ha sido configurada para el script de ingestión.")

# --- CONSTANTES LOCALES PARA EL SCRIPT ---
# Asegúrate de que coincidan con las usadas por el backend
DIRECTORIO_PERSISTENTE_LOCAL = "chroma_db_data" # Debe coincidir con el del backend
NOMBRE_DE_LA_COLECCION_LOCAL = "normativa_colombiana" # Debe coincidir con el del backend
# --- INICIO DE LA CORRECCION: Guardamos el nombre del modelo como string ---
NOMBRE_MODELO_EMBEDDINGS_LOCAL = "models/embedding-001" # Debe coincidir con el del backend
# --- FIN DE LA CORRECCION ---
DIRECTORIO_BASE_CONOCIMIENTO_LOCAL = "backend/datos/base_de_conocimiento_juridico" # Ruta a tus archivos

# --- CONFIGURACION DE LA API DE GOOGLE (LOCAL AL SCRIPT) ---
genai.configure(api_key=GOOGLE_API_KEY)

def generar_embedding_local(texto: str):
    """
    Genera un embedding usando la API de Google Generative AI.
    Esta funcion es local al script de ingestión.
    """
    # --- INICIO DE LA CORRECCION ---
    # La función embed_content es de alto nivel, no necesita el objeto del modelo,
    # solo su nombre en formato string.
    resultado = genai.embed_content(
        model=NOMBRE_MODELO_EMBEDDINGS_LOCAL, # Pasamos el string directamente
        content=texto,
        task_type="RETRIEVAL_DOCUMENT" # Asegúrate del tipo de tarea correcto
    )
    return resultado['embedding']
    # --- FIN DE LA CORRECCION ---

def cargar_documentos_local(directorio: str) -> list[dict]:
    """
    Recorre el directorio, lee archivos .txt y .pdf, y devuelve una lista
    de diccionarios, cada uno con el contenido y la fuente del archivo.
    Esta funcion es local al script de ingestión.
    """
    documentos = []
    print(f"Buscando documentos en: {directorio}")
    for root, _, files in os.walk(directorio):
        for file in files:
            ruta_completa = os.path.join(root, file)
            contenido = ""
            if file.endswith(".pdf"):
                try:
                    reader = PdfReader(ruta_completa) # Usar PdfReader
                    for page in reader.pages:
                        contenido += page.extract_text() or ""
                    print(f"  -> [PDF] Leído: {file}")
                except Exception as e:
                    print(f"  -> [ERROR] No se pudo leer el PDF {file}: {e}")
            elif file.endswith(".txt"):
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                    print(f"  -> [TXT] Leído: {file}")
                except Exception as e:
                    print(f"  -> [ERROR] No se pudo leer el TXT {file}: {e}")

            if contenido:
                documentos.append({"contenido": contenido, "fuente": file}) # Añadir a la lista global 'documentos'
    return documentos

def dividir_texto_en_fragmentos_local(documentos: list[dict]) -> list[dict]:
    """
    Toma la lista de documentos y los divide en fragmentos más pequeños (chunks)
    con un ligero solapamiento para no perder contexto.
    Esta funcion es local al script de ingestión.
    """
    # Esta herramienta de Langchain es experta en dividir texto de forma inteligente.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Cada fragmento tendrá un máximo de 1000 caracteres.
        chunk_overlap=200, # Los fragmentos se solaparán en 200 caracteres.
        length_function=len,
    )
    fragmentos = []
    for doc in documentos:
        chunks = text_splitter.split_text(doc["contenido"]) # Usar split_text
        for i, chunk_text in enumerate(chunks):
            fragmentos.append({
                "texto": chunk_text,
                "metadata": {"fuente": doc["fuente"], "fragmento_nro": i}
            })
    print(f"\nTotal de documentos divididos en {len(fragmentos)} fragmentos.")
    return fragmentos

def main():
    """
    Función principal que orquesta todo el proceso de ingesta.
    Esta función NO debe importar ni llamar a ninguna funcion que use 'obtener_almacen_de_vectores' del backend principal.
    """
    print("\n--- INICIANDO PROCESO DE INGESTA DE DOCUMENTOS (Script Autonomo) ---")

    # 1. Inicializar ChromaDB localmente para este script
    cliente_chroma_local = chromadb.PersistentClient(path=DIRECTORIO_PERSISTENTE_LOCAL)
    coleccion_local = cliente_chroma_local.get_or_create_collection(name=NOMBRE_DE_LA_COLECCION_LOCAL)
    print(f">>> Conectado a la colección '{NOMBRE_DE_LA_COLECCION_LOCAL}' para ingestión.")

    # 2. Cargar y leer todos los documentos de la base de conocimiento
    documentos_leidos = cargar_documentos_local(DIRECTORIO_BASE_CONOCIMIENTO_LOCAL)

    # 3. Dividir los documentos en fragmentos manejables
    fragmentos = dividir_texto_en_fragmentos_local(documentos_leidos)

    # 4. Procesar y guardar en ChromaDB en lotes para eficiencia
    print("\nGenerando embeddings y guardando en ChromaDB local... (esto puede tardar unos minutos)")
    batch_size = 100
    total_fragmentos = len(fragmentos)

    for i in range(0, total_fragmentos, batch_size):
        lote = fragmentos[i:i+batch_size]

        ids = [f"frag_{i+j}" for j in range(len(lote))]
        textos_lote = [item["texto"] for item in lote]
        metadatas_lote = [item["metadata"] for item in lote]

        # Generamos los embeddings para todo el lote de una vez usando la funcion local
        embeddings_lote = [generar_embedding_local(texto) for texto in textos_lote]

        # Añadimos el lote a la colección LOCAL de ChromaDB
        coleccion_local.add(
            embeddings=embeddings_lote,
            documents=textos_lote,
            metadatas=metadatas_lote,
            ids=ids
        )
        print(f"  -> Lote {i//batch_size + 1} procesado. ({min(i+batch_size, total_fragmentos)}/{total_fragmentos} fragmentos)")

    print("\n--- ¡PROCESO DE INGESTA COMPLETADO EXITOSAMENTE! ---")
    print(f"La colección '{coleccion_local.name}' ahora contiene {coleccion_local.count()} vectores.")
    print("--- FIN DE LA INGESTA AUTOMATICA ---\n")


if __name__ == "__main__":
    main()