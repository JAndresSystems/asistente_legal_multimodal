# backend/crear_vectores.py
import os
import glob
import uuid
from backend.configuracion_vectores import obtener_almacen_de_vectores, generar_embedding

# --- CONFIGURACIÓN ---
RUTA_DATOS = os.path.join("backend", "datos", "base_de_conocimiento_juridico")

def cargar_y_vectorizar():
    print("--- INICIO DE VECTORIZACIÓN INTELIGENTE (OPTIMIZADA PARA RAGAS) ---")
    
    almacen = obtener_almacen_de_vectores()
    coleccion = almacen["coleccion"]
    
    # 1. Limpiar memoria
    print("🧹 Limpiando memoria antigua...")
    try:
        todos = coleccion.get()
        if todos['ids']:
            coleccion.delete(ids=todos['ids'])
    except Exception as e:
        print(f"Nota: Base nueva o vacía ({e})")

    # 2. Buscar archivos
    patron = os.path.join(RUTA_DATOS, "**", "*.txt")
    archivos = glob.glob(patron, recursive=True)
    print(f"📂 Procesando {len(archivos)} archivos...")

    total_chunks = 0

    for ruta in archivos:
        nombre = os.path.basename(ruta)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                texto = f.read()

            # --- ESTRATEGIA DE CHUNKING (LA CLAVE DEL ÉXITO) ---
            # En lugar de dividir solo por párrafos, agrupamos párrafos
            # para que el contexto nunca quede "huerfano".
            parrafos_crudos = texto.split("\n\n")
            chunks_finales = []
            
            # Unimos párrafos de 2 en 2 con solapamiento
            # Ejemplo: [P1+P2], [P2+P3], [P3+P4]...
            for i in range(len(parrafos_crudos)):
                # Tomamos el actual y el siguiente (si existe)
                chunk_actual = parrafos_crudos[i]
                if i < len(parrafos_crudos) - 1:
                    chunk_actual += "\n\n" + parrafos_crudos[i+1]
                
                if len(chunk_actual) > 50: # Solo info relevante
                    # Agregamos el nombre del archivo al inicio para dar contexto fuerte
                    chunk_con_contexto = f"FUENTE: {nombre}\nCONTENIDO:\n{chunk_actual}"
                    chunks_finales.append(chunk_con_contexto)

            # 3. Guardar en BD
            ids = [f"{nombre}_{i}_{uuid.uuid4().hex[:6]}" for i in range(len(chunks_finales))]
            embeddings = [generar_embedding(c) for c in chunks_finales]
            metadatas = [{"fuente": nombre} for _ in chunks_finales]

            if ids:
                coleccion.add(ids=ids, embeddings=embeddings, documents=chunks_finales, metadatas=metadatas)
                total_chunks += len(ids)
                print(f"   ✅ {nombre}: {len(ids)} fragmentos indexados.")

        except Exception as e:
            print(f"   ❌ Error en {nombre}: {e}")

    print("--------------------------------------------------")
    print(f"🌟 MEMORIA REGENERADA: {total_chunks} fragmentos de alta calidad.")
    print("--------------------------------------------------")

if __name__ == "__main__":
    cargar_y_vectorizar()