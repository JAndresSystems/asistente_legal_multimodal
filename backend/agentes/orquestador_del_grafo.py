# backend/agentes/orquestador_del_grafo.py
import json
from langgraph.graph import StateGraph, END
import mimetypes
from .estado_del_grafo import EstadoDelGrafo

# ==============================================================================
# INICIO DE LA MODIFICACION: Importamos el nuevo nodo
# ==============================================================================
from .nodos_del_grafo import (
    nodo_agente_triaje,
    nodo_solicitar_informacion_adicional, 
    nodo_preparar_respuesta_rechazo,
    nodo_preparar_respuesta_aceptacion, 
    nodo_agente_analizador_pdf,
    nodo_agente_analizador_audio,
    nodo_agente_determinador_competencias,
    nodo_agente_repartidor,
    nodo_agente_juridico
)
# ==============================================================================
# FIN DE LA MODIFICACION
# ==============================================================================

workflow = StateGraph(EstadoDelGrafo)

# Añadimos todos los nodos, incluyendo el nuevo
workflow.add_node("agente_triaje", nodo_agente_triaje)
workflow.add_node("solicitar_informacion_adicional", nodo_solicitar_informacion_adicional)
workflow.add_node("preparar_respuesta_rechazo", nodo_preparar_respuesta_rechazo)
workflow.add_node("preparar_respuesta_aceptacion", nodo_preparar_respuesta_aceptacion)
workflow.add_node("agente_analizador_pdf", nodo_agente_analizador_pdf)
workflow.add_node("agente_analizador_audio", nodo_agente_analizador_audio)
workflow.add_node("agente_determinador_competencias", nodo_agente_determinador_competencias)
workflow.add_node("agente_repartidor", nodo_agente_repartidor)
workflow.add_node("agente_juridico", nodo_agente_juridico)

workflow.set_entry_point("agente_triaje")



def decision_despues_del_triaje(estado: EstadoDelGrafo) -> str:
    """
    Función de decisión clave.
    CORREGIDO: Ahora reconoce correctamente 'ADMISSIBLE' y lo enruta
    hacia la aceptación, solucionando el bug crítico de rechazo por seguridad.
    """
    print("\n--- [ORQUESTADOR] Tomando decision despues del triaje ---")
    resultado_triaje_dict = estado.get("resultado_triaje")

    if not resultado_triaje_dict:
        print("--- [ORQUESTADOR] Decision: No hay resultado de triaje. Terminando.")
        return END

    # La clave es 'decision_triaje', no 'decision'
    decision = resultado_triaje_dict.get("decision_triaje")
    print(f"--- [ORQUESTADOR] Decisión del agente: {decision}")

    if decision == "FALTA_INFORMACION":
        return "solicitar_informacion_adicional"
    elif decision == "NO_ADMISSIBLE":
        return "preparar_respuesta_rechazo"
    # --- ESTA ES LA CORRECCIÓN CRÍTICA ---
    elif decision == "ADMISSIBLE":
        return "preparar_respuesta_aceptacion"
    # --- FIN DE LA CORRECCIÓN CRÍTICA ---
    else:
        print(f"--- [ORQUESTADOR] ADVERTENCIA: Decisión desconocida '{decision}'. Rechazando por seguridad.")
        return "preparar_respuesta_rechazo"



workflow.add_conditional_edges(
    "agente_triaje",
    decision_despues_del_triaje
)

workflow.add_edge("solicitar_informacion_adicional", END)
workflow.add_edge("preparar_respuesta_rechazo", END)

# --- ¡NUEVA CONEXIÓN! ---
# Después de notificar la aceptación, el flujo interno continúa hacia la clasificación.
workflow.add_edge("preparar_respuesta_aceptacion", "agente_determinador_competencias")

# El resto del flujo se modifica para que parta desde la clasificación,
# ya que la decisión del tipo de archivo ya no es necesaria aquí.
workflow.add_edge("agente_determinador_competencias", "agente_repartidor")
workflow.add_edge("agente_repartidor", "agente_juridico")
workflow.add_edge("agente_juridico", END)

# Eliminamos las viejas conexiones directas que ahora son redundantes
# workflow.add_edge("agente_analizador_pdf", "agente_determinador_competencias")
# workflow.add_edge("agente_analizador_audio", "agente_determinador_competencias")

grafo_compilado = workflow.compile()
print("SUCCESS (LANGGRAPH): Grafo de admision con ciclo de decision compilado exitosamente.")