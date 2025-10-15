# backend/agentes/orquestador_del_grafo.py

from langgraph.graph import StateGraph, END
import mimetypes
from .estado_del_grafo import EstadoDelGrafo

# ==============================================================================
# INICIO DE LA MODIFICACION: Importamos el nuevo nodo
# ==============================================================================
from .nodos_del_grafo import (
    nodo_agente_triaje,
    nodo_solicitar_informacion_adicional, # <-- Nuevo nodo importado
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
    2. Si el caso no es admisible, termina el flujo.
    3. Si es admisible y la info es suficiente, lo envia al analizador correcto.
    """
    print("\n--- [ORQUESTADOR] Tomando decision despues del triaje ---")
    resultado_triaje = estado.get("resultado_triaje")

    # Caso 1: El triaje no produjo un resultado valido. Terminamos por seguridad.
    if not resultado_triaje:
        print("--- [ORQUESTADOR] Decision: No hay resultado de triaje. Terminando.")
        return END

    # Caso 2: La informacion NO es suficiente. Hay que preguntar al usuario.
    if not resultado_triaje.get("informacion_suficiente"):
        print("--- [ORQUESTADOR] Decision: Informacion insuficiente. Solicitando mas datos.")
        return "solicitar_informacion_adicional"

    # Caso 3: La informacion es suficiente, pero el caso NO es admisible.
    if not resultado_triaje.get("admisible"):
        print("--- [ORQUESTADOR] Decision: Caso no admisible. Terminando.")
        return END
        
    # Caso 4: La informacion es suficiente y el caso es admisible. Continuamos al analisis.
    print("--- [ORQUESTADOR] Decision: Caso admisible. Enrutando a analizador por tipo de archivo.")
    ruta_archivo = estado["rutas_archivos_evidencia"][0]
    tipo_mime, _ = mimetypes.guess_type(ruta_archivo)
    
    if tipo_mime:
        if "pdf" in tipo_mime:
            return "agente_analizador_pdf"
        if "audio" in tipo_mime or "mp3" in tipo_mime or "wav" in tipo_mime or "mpeg" in tipo_mime:
            return "agente_analizador_audio"
            
    # Si no es PDF ni audio, va directo a determinar competencias.
    return "agente_determinador_competencias"

# Conectamos la salida del triaje a nuestra nueva funcion de decision
workflow.add_conditional_edges(
    "agente_triaje",
    decision_despues_del_triaje
)

# El nodo de solicitud de informacion es un punto final para esta ejecucion del grafo.
workflow.add_edge("solicitar_informacion_adicional", END)
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