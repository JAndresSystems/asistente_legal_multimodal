# backend/agentes/orquestador_del_grafo.py

from langgraph.graph import StateGraph, END
import mimetypes
from .estado_del_grafo import EstadoDelGrafo

# --- 1. IMPORTACIÓN COMPLETA DE TODOS LOS NODOS ---
# Importamos todas las funciones de nodo que componen nuestro flujo de trabajo.
from .nodos_del_grafo import (
    nodo_agente_triaje,
    nodo_agente_analizador_pdf,
    nodo_agente_analizador_audio,
    nodo_agente_determinador_competencias,
    nodo_agente_repartidor,
    nodo_agente_juridico,
    nodo_agente_generador_documentos
)

# --- 2. CONSTRUCCIÓN DEL GRAFO ---
# Creamos la instancia del grafo, asociandola a la estructura de nuestro estado.
workflow = StateGraph(EstadoDelGrafo)

# 3. AÑADIR TODOS LOS NODOS AL GRAFO
# Cada nodo representa un agente o una funcion en nuestro sistema.
print("SETUP-LANGGRAPH: Añadiendo todos los nodos al grafo multimodal...")
workflow.add_node("agente_triaje", nodo_agente_triaje)
workflow.add_node("agente_analizador_pdf", nodo_agente_analizador_pdf)
workflow.add_node("agente_analizador_audio", nodo_agente_analizador_audio)
workflow.add_node("agente_determinador_competencias", nodo_agente_determinador_competencias)
workflow.add_node("agente_repartidor", nodo_agente_repartidor)
workflow.add_node("agente_juridico", nodo_agente_juridico)
workflow.add_node("agente_generador_documentos", nodo_agente_generador_documentos)
print("-> Nodos añadidos exitosamente.")

# 4. DEFINIR EL PUNTO DE ENTRADA DEL FLUJO
# Le decimos al grafo que la primera tarea a ejecutar es siempre el 'agente_triaje'.
workflow.set_entry_point("agente_triaje")

# 5. DEFINIR LA LÓGICA DE ENRUTAMIENTO (LAS CONEXIONES)

# 5.1. Función de Decisión Multimodal después del Triaje
def enrutar_evidencia_despues_del_triaje(estado: EstadoDelGrafo) -> str:
    """
    Esta función es el corazón de la multimodalidad.
    Inspecciona el estado y el tipo de evidencia para decidir qué agente
    especializado debe actuar a continuación.
    """
    print("--- Decision: Enrutando evidencia por tipo de archivo... ---")
    
    # Primero, verificamos la decisión del triaje. Si no es admisible, el flujo termina.
    resultado_triaje = estado.get("resultado_triaje")
    if not resultado_triaje or not resultado_triaje.get("admisible"):
        print("-> Veredicto: No Admisible. Finalizando flujo de trabajo.")
        return END

    # Si es admisible, inspeccionamos el tipo de archivo de la evidencia.
    ruta_archivo = estado["rutas_archivos_evidencia"][0]
    tipo_mime, _ = mimetypes.guess_type(ruta_archivo)
    print(f"-> Evidencia: {ruta_archivo}, Tipo MIME detectado: {tipo_mime}")

    if tipo_mime:
        if "pdf" in tipo_mime:
            print("-> Decision: Enrutando al Agente Analizador de PDFs.")
            return "agente_analizador_pdf"
        elif "audio" in tipo_mime or "mp3" in tipo_mime or "wav" in tipo_mime or "m4a" in tipo_mime:
            print("-> Decision: Enrutando al Agente Analizador de Audio.")
            return "agente_analizador_audio"

    # Si el tipo de archivo no es especializado (ej. una imagen .jpg o .txt),
    # se salta el análisis profundo y pasa directamente a la clasificación.
    print("-> Decision: Tipo no especializado. Enrutando a Determinador de Competencias.")
    return "agente_determinador_competencias"

# 5.2. Añadir la Arista Condicional
# Desde 'agente_triaje', el siguiente paso depende del resultado de la función 'enrutar_evidencia'.
workflow.add_conditional_edges(
    "agente_triaje",
    enrutar_evidencia_despues_del_triaje,
    {
        "agente_analizador_pdf": "agente_analizador_pdf",
        "agente_analizador_audio": "agente_analizador_audio",
        "agente_determinador_competencias": "agente_determinador_competencias",
        END: END
    }
)

# 5.3. Añadir las Aristas Secuenciales (El flujo principal)
# La salida de los agentes especializados converge en el determinador de competencias.
workflow.add_edge("agente_analizador_pdf", "agente_determinador_competencias")
workflow.add_edge("agente_analizador_audio", "agente_determinador_competencias")

# A partir de la determinación de competencias, la cadena es lineal.
workflow.add_edge("agente_determinador_competencias", "agente_repartidor")
workflow.add_edge("agente_repartidor", "agente_juridico")
workflow.add_edge("agente_juridico", "agente_generador_documentos")

# El último agente de la cadena apunta al final del flujo de trabajo.
workflow.add_edge("agente_generador_documentos", END)


# 6. COMPILAR EL GRAFO
# Este paso finaliza la definición del flujo y crea un objeto ejecutable.
grafo_compilado = workflow.compile()

print("SUCCESS (LANGGRAPH): Grafo multimodal completo y final compilado exitosamente.")