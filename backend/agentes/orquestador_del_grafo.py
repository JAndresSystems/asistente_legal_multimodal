#backend\agentes\orquestador_del_grafo.py
from langgraph.graph import StateGraph, END
from .estado_del_grafo import EstadoDelGrafo

# La importación respeta el nombre de su archivo 'nodos_del_grafo.py'
from .nodos_del_grafo import (
    nodo_agente_triaje,
    nodo_agente_determinador_competencias,
    nodo_agente_repartidor,
    nodo_agente_juridico
)

workflow = StateGraph(EstadoDelGrafo)

workflow.add_node("agente_triaje", nodo_agente_triaje)
workflow.add_node("agente_determinador_competencias", nodo_agente_determinador_competencias)
workflow.add_node("agente_repartidor", nodo_agente_repartidor)
workflow.add_node("agente_juridico", nodo_agente_juridico)

workflow.set_entry_point("agente_triaje")

def decidir_siguiente_paso_despues_del_triaje(estado: EstadoDelGrafo) -> str:
    if estado.get("es_admisible"):
        return "agente_determinador_competencias"
    else:
        return END

workflow.add_conditional_edges(
    "agente_triaje",
    decidir_siguiente_paso_despues_del_triaje,
    { "agente_determinador_competencias": "agente_determinador_competencias", END: END }
)

workflow.add_edge("agente_determinador_competencias", "agente_repartidor")
workflow.add_edge("agente_repartidor", "agente_juridico")
workflow.add_edge("agente_juridico", END)

grafo_compilado = workflow.compile()
print("SETUP-LANGGRAPH: Grafo con Agente Juridico (RAG) integrado y compilado!")