# backend/agentes/orquestador_del_grafo.py

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
workflow.add_node("agente_analizador_pdf", nodo_agente_analizador_pdf)
workflow.add_node("agente_analizador_audio", nodo_agente_analizador_audio)
workflow.add_node("agente_determinador_competencias", nodo_agente_determinador_competencias)
workflow.add_node("agente_repartidor", nodo_agente_repartidor)
workflow.add_node("agente_juridico", nodo_agente_juridico)

workflow.set_entry_point("agente_triaje")

# ==============================================================================
# INICIO DE LA MODIFICACION: Reescribimos la funcion de enrutamiento
# ==============================================================================
def decision_despues_del_triaje(estado: EstadoDelGrafo) -> str:
    """
    Docstring:
    Esta es la funcion de decision clave del grafo. Despues del triaje,
    decide el siguiente paso basado en el resultado.
    
    1. Si la informacion es insuficiente, pide mas.
    2. Si el caso no es admisible, lo envia al nodo de rechazo.
    3. Si es admisible y la info es suficiente, lo envia al analizador correcto.
    """
    print("\n--- [ORQUESTADOR] Tomando decision despues del triaje ---")
    resultado_triaje = estado.get("resultado_triaje")

    if not resultado_triaje:
        print("--- [ORQUESTADOR] Decision: No hay resultado de triaje. Terminando.")
        return END

    if not resultado_triaje.get("informacion_suficiente"):
        print("--- [ORQUESTADOR] Decision: Informacion insuficiente. Solicitando mas datos.")
        return "solicitar_informacion_adicional"

    # AQUI ESTA EL CAMBIO: Si no es admisible, va al nodo de rechazo
    if not resultado_triaje.get("admisible"):
        print("--- [ORQUESTADOR] Decision: Caso no admisible. Preparando respuesta de rechazo.")
        return "preparar_respuesta_rechazo"
        
    print("--- [ORQUESTADOR] Decision: Caso admisible. Enrutando a analizador por tipo de archivo.")
    ruta_archivo = estado["rutas_archivos_evidencia"][0]
    tipo_mime, _ = mimetypes.guess_type(ruta_archivo)
    
    if tipo_mime:
        if "pdf" in tipo_mime:
            return "agente_analizador_pdf"
        if "audio" in tipo_mime or "mp3" in tipo_mime or "wav" in tipo_mime or "mpeg" in tipo_mime:
            return "agente_analizador_audio"
            
    return "agente_determinador_competencias"

workflow.add_conditional_edges(
    "agente_triaje",
    decision_despues_del_triaje
)

# Los nodos de solicitud y rechazo son puntos finales para esta ejecucion.
workflow.add_edge("solicitar_informacion_adicional", END)
workflow.add_edge("preparar_respuesta_rechazo", END) # <-- Nueva conexion a END
# ==============================================================================
# FIN DE LA MODIFICACION
# ==============================================================================

# El resto del flujo lineal para un caso exitoso se mantiene igual
workflow.add_edge("agente_analizador_pdf", "agente_determinador_competencias")
workflow.add_edge("agente_analizador_audio", "agente_determinador_competencias")
workflow.add_edge("agente_determinador_competencias", "agente_repartidor")
workflow.add_edge("agente_repartidor", "agente_juridico")
workflow.add_edge("agente_juridico", END)

grafo_compilado = workflow.compile()
print("SUCCESS (LANGGRAPH): Grafo de admision con ciclo de decision compilado exitosamente.")