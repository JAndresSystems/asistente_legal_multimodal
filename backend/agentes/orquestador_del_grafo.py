# backend/agentes/orquestador_del_grafo.py

from langgraph.graph import StateGraph, END
from .estado_del_grafo import EstadoDelGrafo
# ¡IMPORTANTE! Importamos todos los nodos que hemos implementado.
from .nodos_del_grafo import (
    nodo_agente_triaje,
    nodo_agente_determinador_competencias,
    nodo_agente_repartidor,
    nodo_agente_juridico,
    nodo_agente_generador_documentos
)

# 1. Definir el grafo de estados
workflow = StateGraph(EstadoDelGrafo)

# 2. Añadir cada uno de nuestros agentes como un "nodo" en el grafo.
#    Les damos un nombre unico en minusculas.
print("SETUP-LANGGRAPH: Añadiendo nodos al grafo...")
workflow.add_node("agente_triaje", nodo_agente_triaje)
workflow.add_node("agente_determinador_competencias", nodo_agente_determinador_competencias)
workflow.add_node("agente_repartidor", nodo_agente_repartidor)
workflow.add_node("agente_juridico", nodo_agente_juridico)
workflow.add_node("agente_generador_documentos", nodo_agente_generador_documentos)
print("-> Nodos añadidos.")

# 3. Definir las conexiones (las "aristas") entre los nodos.

# El punto de entrada del flujo de trabajo es el agente de triaje.
workflow.set_entry_point("agente_triaje")

# Despues del triaje, necesitamos tomar una decision.
def decidir_siguiente_paso_despues_del_triaje(estado: EstadoDelGrafo) -> str:
    """
    Funcion de decision. Revisa el resultado del triaje y dirige el flujo.
    """
    print("--- Decision: Evaluando resultado del triaje... ---")
    resultado_triaje = estado.get("resultado_triaje")
    
    # Si el caso es admisible, continuamos con la cadena de analisis.
    if resultado_triaje and resultado_triaje.get("admisible"):
        print("-> Veredicto: Admisible. Continuando a Determinador de Competencias.")
        return "agente_determinador_competencias"
    
    # Si no es admisible, el flujo de trabajo termina aqui.
    else:
        print("-> Veredicto: No Admisible. Finalizando el flujo de trabajo.")
        return END

# Creamos una arista condicional desde el triaje.
workflow.add_conditional_edges(
    "agente_triaje",
    decidir_siguiente_paso_despues_del_triaje,
    {
        "agente_determinador_competencias": "agente_determinador_competencias",
        END: END
    }
)

# Creamos las aristas secuenciales para el resto del flujo.
# Despues de determinar competencias, va al repartidor.
workflow.add_edge("agente_determinador_competencias", "agente_repartidor")
# Despues del repartidor, ejecuta al agente juridico.
workflow.add_edge("agente_repartidor", "agente_juridico")
# Despues del agente juridico, ejecuta al generador de documentos.
workflow.add_edge("agente_juridico", "agente_generador_documentos")
# Despues de generar el documento, el flujo de trabajo termina.
workflow.add_edge("agente_generador_documentos", END)

# 4. Compilar el grafo en un objeto ejecutable.
grafo_compilado = workflow.compile()
print("SUCCESS (LANGGRAPH): Grafo de agentes completo y compilado exitosamente.")