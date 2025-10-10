from langgraph.graph import StateGraph, END
import mimetypes
from .estado_del_grafo import EstadoDelGrafo

from .nodos_del_grafo import (
    nodo_agente_triaje,
    nodo_agente_analizador_pdf,
    nodo_agente_analizador_audio,
    nodo_agente_determinador_competencias,
    nodo_agente_repartidor,
    nodo_agente_juridico
)

workflow = StateGraph(EstadoDelGrafo)

workflow.add_node("agente_triaje", nodo_agente_triaje)
workflow.add_node("agente_analizador_pdf", nodo_agente_analizador_pdf)
workflow.add_node("agente_analizador_audio", nodo_agente_analizador_audio)
workflow.add_node("agente_determinador_competencias", nodo_agente_determinador_competencias)
workflow.add_node("agente_repartidor", nodo_agente_repartidor)
workflow.add_node("agente_juridico", nodo_agente_juridico)

workflow.set_entry_point("agente_triaje")

def enrutar_evidencia_despues_del_triaje(estado: EstadoDelGrafo) -> str:
    resultado_triaje = estado.get("resultado_triaje")
    if not resultado_triaje or not resultado_triaje.get("admisible"):
        return END
    ruta_archivo = estado["rutas_archivos_evidencia"][0]
    tipo_mime, _ = mimetypes.guess_type(ruta_archivo)
    if tipo_mime and "pdf" in tipo_mime:
        return "agente_analizador_pdf"
    if tipo_mime and ("audio" in tipo_mime or "mp3" in tipo_mime or "wav" in tipo_mime):
        return "agente_analizador_audio"
    return "agente_determinador_competencias"

workflow.add_conditional_edges("agente_triaje", enrutar_evidencia_despues_del_triaje)

workflow.add_edge("agente_analizador_pdf", "agente_determinador_competencias")
workflow.add_edge("agente_analizador_audio", "agente_determinador_competencias")
workflow.add_edge("agente_determinador_competencias", "agente_repartidor")

# ==============================================================================
# CORRECCION FINAL DEL FLUJO DE EJECUCION
# ==============================================================================
# El Agente Repartidor DEBE pasar el control al Agente Juridico.
workflow.add_edge("agente_repartidor", "agente_juridico")
# El flujo de admision termina DESPUES del analisis juridico inicial.
workflow.add_edge("agente_juridico", END)
# ==============================================================================

grafo_compilado = workflow.compile()
print("SUCCESS (LANGGRAPH): Grafo de admision compilado exitosamente.")