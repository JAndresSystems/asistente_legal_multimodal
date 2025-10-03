from langgraph.graph import StateGraph, END
from .estado_del_grafo import EstadoDelGrafo

from .nodos_del_grafo import (
    nodo_agente_triaje,
    nodo_agente_determinador_competencias,
    nodo_agente_repartidor # <-- Importamos el nuevo nodo
)

workflow = StateGraph(EstadoDelGrafo)

# Registramos a nuestros tres agentes.
workflow.add_node("agente_triaje", nodo_agente_triaje)
workflow.add_node("agente_determinador_competencias", nodo_agente_determinador_competencias)
workflow.add_node("agente_repartidor", nodo_agente_repartidor) # <-- Lo añadimos al grafo

workflow.set_entry_point("agente_triaje")

def decidir_siguiente_paso_despues_del_triaje(estado: EstadoDelGrafo) -> str:
    print("--- Entrando en el Punto de Control: Decisión Post-Triaje ---")
    if estado.get("es_admisible"):
        print("    Veredicto: ADMISIBLE. Continuando a la determinación de competencia.")
        return "agente_determinador_competencias"
    else:
        print("    Veredicto: NO ADMISIBLE. Finalizando.")
        return END

workflow.add_conditional_edges(
    "agente_triaje",
    decidir_siguiente_paso_despues_del_triaje,
    {
        "agente_determinador_competencias": "agente_determinador_competencias",
        END: END
    }
)

# --- CAMBIO CLAVE ---
# Ahora, después de determinar la competencia, conectamos directamente al repartidor.
workflow.add_edge("agente_determinador_competencias", "agente_repartidor")

# Y después del repartidor, el flujo principal termina.
workflow.add_edge("agente_repartidor", END)

grafo_compilado = workflow.compile()
print("SETUP-LANGGRAPH: ¡Grafo de agentes con la cadena principal completa compilado!")