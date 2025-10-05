# backend/agentes/orquestador_del_grafo.py

from langgraph.graph import StateGraph, END
import mimetypes
from .estado_del_grafo import EstadoDelGrafo
# --- ¡IMPORTACION COMPLETA! ---
# Importamos TODOS los nodos que hemos construido y estabilizado.
from .nodos_del_grafo import (
    nodo_agente_triaje,
    nodo_agente_analizador_pdf,
    nodo_agente_analizador_audio,
    nodo_agente_determinador_competencias,
    nodo_agente_repartidor,
    nodo_agente_juridico,
    nodo_agente_generador_documentos
)

# --- Construccion del Grafo ---
workflow = StateGraph(EstadoDelGrafo)

# 1. Añadir TODOS los nodos al grafo
print("SETUP-LANGGRAPH: Añadiendo todos los nodos al grafo multimodal...")
workflow.add_node("agente_triaje", nodo_agente_triaje)
workflow.add_node("agente_analizador_pdf", nodo_agente_analizador_pdf)
workflow.add_node("agente_analizador_audio", nodo_agente_analizador_audio)
workflow.add_node("agente_determinador_competencias", nodo_agente_determinador_competencias)
workflow.add_node("agente_repartidor", nodo_agente_repartidor)
workflow.add_node("agente_juridico", nodo_agente_juridico)
workflow.add_node("agente_generador_documentos", nodo_agente_generador_documentos)
print("-> Nodos añadidos.")

# 2. Definir el punto de entrada
workflow.set_entry_point("agente_triaje")

# 3. Logica de enrutamiento multimodal (establecida en el paso anterior)
def enrutar_evidencia_despues_del_triaje(estado: EstadoDelGrafo) -> str:
    print("--- Decision: Enrutando evidencia por tipo de archivo... ---")
    resultado_triaje = estado.get("resultado_triaje")
    if not resultado_triaje or not resultado_triaje.get("admisible"):
        print("-> Veredicto: No Admisible. Finalizando flujo.")
        return END

    ruta_archivo = estado["rutas_archivos_evidencia"][0]
    tipo_mime, _ = mimetypes.guess_type(ruta_archivo)
    print(f"-> Evidencia: {ruta_archivo}, Tipo MIME detectado: {tipo_mime}")

    if tipo_mime:
        if "pdf" in tipo_mime:
            return "agente_analizador_pdf"
        elif "audio" in tipo_mime:
            return "agente_analizador_audio"

    return "agente_determinador_competencias"

# 4. Conectar la decision del triaje
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

# 5. --- RECONEXION DE LA CADENA PRINCIPAL ---
# La salida de CUALQUIER analizador especializado va al determinador de competencias.
workflow.add_edge("agente_analizador_pdf", "agente_determinador_competencias")
workflow.add_edge("agente_analizador_audio", "agente_determinador_competencias")

# Despues de determinar la competencia, el flujo continua a traves de los
# agentes que ya habiamos estabilizado.
workflow.add_edge("agente_determinador_competencias", "agente_repartidor")
workflow.add_edge("agente_repartidor", "agente_juridico")
workflow.add_edge("agente_juridico", "agente_generador_documentos")

# Despues del ultimo agente, el flujo de trabajo termina.
workflow.add_edge("agente_generador_documentos", END)


# 6. Compilar el grafo
grafo_compilado = workflow.compile()
print("SUCCESS (LANGGRAPH): Grafo multimodal completo reensamblado y compilado.")