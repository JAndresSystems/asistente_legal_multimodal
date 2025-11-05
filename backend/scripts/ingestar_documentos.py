#C:\react\asistente_legal_multimodal\backend\scripts\ingestar_documentos.py


# backend/scripts/ingestar_documentos.py

import os
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Importamos las funciones de nuestro archivo de configuración
from backend.configuracion_vectores import obtener_almacen_de_vectores, generar_embedding

# La ruta a la carpeta que contiene todos nuestros documentos de conocimiento
DIRECTORIO_BASE_CONOCIMIENTO = "backend/datos/base_de_conocimiento_juridico"

def cargar_documentos(directorio: str) -> list[dict]:
    """
    Recorre el directorio, lee archivos .txt y .pdf, y devuelve una lista
    de diccionarios, cada uno con el contenido y la fuente del archivo.
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

def dividir_texto_en_fragmentos(documentos: list[dict]) -> list[dict]:
    """
    Toma la lista de documentos y los divide en fragmentos más pequeños (chunks)
    con un ligero solapamiento para no perder contexto.
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
    """
    print("--- INICIANDO PROCESO DE INGESTA DE DOCUMENTOS ---")
    
    # 1. Obtener la conexión a la base de datos vectorial
    almacen = obtener_almacen_de_vectores()
    coleccion = almacen["coleccion"]
    
    # 2. Cargar y leer todos los documentos de la base de conocimiento
    documentos_leidos = cargar_documentos(DIRECTORIO_BASE_CONOCIMIENTO)
    
    # 3. Dividir los documentos en fragmentos manejables
    fragmentos = dividir_texto_en_fragmentos(documentos_leidos)
    
    # 4. Procesar y guardar en ChromaDB en lotes para eficiencia
    print("\nGenerando embeddings y guardando en ChromaDB... (esto puede tardar unos minutos)")
    batch_size = 100
    total_fragmentos = len(fragmentos)
    
    for i in range(0, total_fragmentos, batch_size):
        lote = fragmentos[i:i+batch_size]
        
        ids = [f"frag_{i+j}" for j in range(len(lote))]
        textos_lote = [item["texto"] for item in lote]
        metadatas_lote = [item["metadata"] for item in lote]
        
        # Generamos los embeddings para todo el lote de una vez
        embeddings = [generar_embedding(texto) for texto in textos_lote]
        
        # Añadimos el lote a la colección de ChromaDB
        coleccion.add(
            embeddings=embeddings,
            documents=textos_lote,
            metadatas=metadatas_lote,
            ids=ids
        )
        print(f"  -> Lote {i//batch_size + 1} procesado. ({min(i+batch_size, total_fragmentos)}/{total_fragmentos} fragmentos)")

    print("\n--- ¡PROCESO DE INGESTA COMPLETADO EXITOSAMENTE! ---")
    print(f"La colección '{coleccion.name}' ahora contiene {coleccion.count()} vectores.")

if __name__ == "__main__":
    main()