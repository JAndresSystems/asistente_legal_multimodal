from langgraph.graph import StateGraph, END
import mimetypes
from .estado_del_grafo import EstadoDelGrafo

from .nodos_del_grafo import (
    nodo_agente_triaje,
    nodo_agente_analizador_pdf,
    nodo_agente_analizador_audio,
    nodo_agente_determinador_competencias,
    nodo_agente_repartidor,
    nodo_agente_juridico,
    nodo_agente_generador_documentos
)

workflow = StateGraph(EstadoDelGrafo)

print("SETUP-LANGGRAPH: Añadiendo todos los nodos al grafo multimodal...")
workflow.add_node("agente_triaje", nodo_agente_triaje)
workflow.add_node("agente_analizador_pdf", nodo_agente_analizador_pdf)
workflow.add_node("agente_analizador_audio", nodo_agente_analizador_audio)
workflow.add_node("agente_determinador_competencias", nodo_agente_determinador_competencias)
workflow.add_node("agente_repartidor", nodo_agente_repartidor)
# Los agentes auxiliares se mantienen definidos pero no en el flujo principal
workflow.add_node("agente_juridico", nodo_agente_juridico)
workflow.add_node("agente_generador_documentos", nodo_agente_generador_documentos)
print("-> Nodos añadidos exitosamente.")

workflow.set_entry_point("agente_triaje")

def enrutar_evidencia_despues_del_triaje(estado: EstadoDelGrafo) -> str:
    print("--- Decision: Enrutando evidencia por tipo de archivo... ---")
    resultado_triaje = estado.get("resultado_triaje")
    if not resultado_triaje or not resultado_triaje.get("admisible"):
        print("-> Veredicto: No Admisible. Finalizando flujo de trabajo.")
        return END

    ruta_archivo = estado["rutas_archivos_evidencia"][0]
    tipo_mime, _ = mimetypes.guess_type(ruta_archivo)
    print(f"-> Evidencia: {ruta_archivo}, Tipo MIME detectado: {tipo_mime}")

    if tipo_mime:
        if "pdf" in tipo_mime:
            print("-> Decision: Enrutando al Agente Analizador de PDFs.")
            return "agente_analizador_pdf"
        elif "audio" in tipo_mime:
            print("-> Decision: Enrutando al Agente Analizador de Audio.")
            return "agente_analizador_audio"

    print("-> Decision: Tipo no especializado. Enrutando a Determinador de Competencias.")
    return "agente_determinador_competencias"

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

workflow.add_edge("agente_analizador_pdf", "agente_determinador_competencias")
workflow.add_edge("agente_analizador_audio", "agente_determinador_competencias")
workflow.add_edge("agente_determinador_competencias", "agente_repartidor")

# ==============================================================================
# INICIO DE LA CORRECCION
# El proceso de analisis inicial termina despues de asignar el caso.
workflow.add_edge("agente_repartidor", END)
# FIN DE LA CORRECCION
# ==============================================================================

grafo_compilado = workflow.compile()
print("SUCCESS (LANGGRAPH): Grafo multimodal completo y final compilado exitosamente.")