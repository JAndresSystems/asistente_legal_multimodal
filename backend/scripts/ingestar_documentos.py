# backend/scripts/ingestar_documentos.py

import os
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from pypdf import PdfReader # Asegúrate de tener este instalado: pip install pypdf
from langchain.text_splitter import RecursiveCharacterTextSplitter # Asegúrate de tener este instalado: pip install langchain
from dotenv import load_dotenv # Asegúrate de tener este instalado: pip install python-dotenv

# --- CARGA DE VARIABLES DE ENTORNO ---
# Cargamos .env desde el directorio de scripts, asumiendo que está en la raíz del backend
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("La variable de entorno GOOGLE_API_KEY no ha sido configurada en el script de ingestión.")

# --- CONFIGURACION LOCAL DEL SCRIPT ---
# Usamos las mismas constantes para asegurar consistencia
DIRECTORIO_PERSISTENTE_LOCAL = "chroma_db_data" # Debe coincidir con el del backend
NOMBRE_COLECCION_LOCAL = "normativa_colombiana" # Debe coincidir con el del backend
NOMBRE_MODELO_EMBEDDINGS_LOCAL = "models/embedding-001" # Nombre del modelo de Google

# --- INICIALIZACION LOCAL DE COMPONENTES ---
# 1. Inicializar la API de Google localmente
genai.configure(api_key=GOOGLE_API_KEY)

# 2. Inicializar el cliente de ChromaDB localmente
cliente_chroma_local = chromadb.PersistentClient(path=DIRECTORIO_PERSISTENTE_LOCAL)

# 3. Obtener (o crear si no existe) la colección local
coleccion_local = cliente_chroma_local.get_or_create_collection(name=NOMBRE_COLECCION_LOCAL)

def generar_embedding_local(texto: str):
    """
    Genera un embedding usando la API de Google GenAI.
    Esta función es local al script de ingestión.
    """
    resultado = genai.embed_content(
        model=NOMBRE_MODELO_EMBEDDINGS_LOCAL, # Usamos la constante local
        content=texto,
        task_type="RETRIEVAL_DOCUMENT"
    )
    return resultado['embedding']

def cargar_documentos_local(directorio: str) -> list[dict]:
    """
    Recorre el directorio, lee archivos .txt y .pdf, y devuelve una lista
    de diccionarios, cada uno con el contenido y la fuente del archivo.
    Esta función es local al script de ingestión.
    """
    documentos = []
    print(f"Buscando documentos en: {directorio}")
    for root, _, files in os.walk(directorio):
        for file in files:
            ruta_completa = os.path.join(root, file)
            contenido = ""
            if file.endswith(".pdf"):
                try:
                    reader = PdfReader(ruta_completa)
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
                documentos.append({"contenido": contenido, "fuente": file})
    return documentos

def dividir_texto_en_fragmentos_local(documentos: list[dict]) -> list[dict]:
    """
    Toma la lista de documentos y los divide en fragmentos más pequeños (chunks)
    con un ligero solapamiento para no perder contexto.
    Esta función es local al script de ingestión.
    """
    # Esta herramienta de Langchain es experta en dividir texto de forma inteligente.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Cada fragmento tendrá un máximo de 1000 caracteres.
        chunk_overlap=200, # Los fragmentos se solaparán en 200 caracteres.
        length_function=len,
    )
    fragmentos = []
    for doc in documentos:
        chunks = text_splitter.split_text(doc["contenido"])
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
    Esta función NO debe importar ni llamar a ninguna funcion que use 'obtener_almacen_de_vectores'.
    """
    print("\n--- INICIANDO PROCESO DE INGESTA DE DOCUMENTOS (Script Autonomo) ---")

    # 1. Cargar y leer todos los documentos de la base de conocimiento
    # Usamos la constante definida en este mismo archivo o una relativa si se prefiere
    directorio_base_conocimiento = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos", "base_de_conocimiento_juridico")
    documentos_leidos = cargar_documentos_local(directorio_base_conocimiento)

    # 2. Dividir los documentos en fragmentos manejables
    fragmentos = dividir_texto_en_fragmentos_local(documentos_leidos)

    # 3. Procesar y guardar en ChromaDB en lotes para eficiencia
    print("\nGenerando embeddings y guardando en ChromaDB... (esto puede tardar unos minutos)")
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