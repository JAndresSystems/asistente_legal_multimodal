# backend/configuracion_vectores.py

import chromadb
import google.generativeai as genai
import os
from dotenv import load_dotenv
import importlib.util # Añadimos esta linea para importar dinamicamente

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

    # --- INICIO DE LA NUEVA LOGICA: Ingesta inicial si la colección está vacía ---
    conteo_docs = coleccion.count()
    print(f">>> Colección '{NOMBRE_DE_LA_COLECCION}' contiene {conteo_docs} documentos.")
    if conteo_docs == 0:
        print(">>> La colección está vacía. Iniciando proceso de ingestión automática...")
        try:
            # Importar y ejecutar el script de ingestión dinámicamente
            # Construimos la ruta absoluta al archivo de ingestión
            ruta_script_ingesta = os.path.abspath(os.path.join(os.path.dirname(__file__), "scripts", "ingestar_documentos.py"))
            print(f">>> Intentando importar script de ingestión desde: {ruta_script_ingesta}")

            # Cargamos el modulo dinamicamente
            spec = importlib.util.spec_from_file_location("ingestar_documentos", ruta_script_ingesta)
            if spec is None or spec.loader is None:
                raise ImportError(f"No se pudo crear un spec o loader para {ruta_script_ingesta}")
            modulo_ingesta = importlib.util.module_from_spec(spec)
            # Ejecutamos el archivo como un modulo
            spec.loader.exec_module(modulo_ingesta)

            # Llamamos a la función main() del modulo importado
            modulo_ingesta.main()

            print(">>> Proceso de ingestión automática completado.")
            # Volvemos a obtener la colección después de la ingestión
            # por si acaso el proceso de ingestión la manipuló de forma diferente
            coleccion = cliente_chroma.get_or_create_collection(name=NOMBRE_DE_LA_COLECCION)
            print(f">>> Tras la ingestión, la colección '{NOMBRE_DE_LA_COLECCION}' contiene {coleccion.count()} documentos.")
        except ImportError as e:
            print(f">>> ERROR: No se pudo importar o ejecutar el script de ingestión: {e}")
            print(">>> Asegúrese de que el archivo 'backend/scripts/ingestar_documentos.py' y la función 'main()' existan.")
            raise
        except AttributeError as e:
            print(f">>> ERROR: La función 'main' no se encontró en el script de ingestión: {e}")
            raise
        except Exception as e:
            print(f">>> ERROR durante la ingestión automática: {e}")
            raise # Relanzamos la excepción para que el backend falle si la ingestión falla critica y necesariamente
    else:
        print(f">>> Colección '{NOMBRE_DE_LA_COLECCION}' ya tiene datos. Saltando ingestión inicial.")
    # --- FIN DE LA NUEVA LOGICA ---

    print(">>> INICIALIZACIÓN COMPLETADA.")

    _singleton_instances["vector_store"] = {
        "cliente": cliente_chroma,
        "coleccion": coleccion, # Devolvemos la colección, ya sea vacía o llena
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