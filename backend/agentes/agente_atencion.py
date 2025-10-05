# backend/agentes/agente_atencion.py

from typing import Dict
from langgraph.graph import StateGraph, END

from .estado_chat import EstadoChat

from ..herramientas.herramienta_rag import buscar_en_base_de_conocimiento
from ..herramientas.herramientas_lenguaje import generar_respuesta_texto

def nodo_agente_atencion(estado: EstadoChat) -> Dict[str, str]:
    """
    Este es el nodo principal del Agente de Atencion. Responde FAQs usando RAG.
    """
    print("--- Ejecutando Nodo: Agente de Atencion (Chatbot de FAQs) ---")
    pregunta = estado["pregunta_usuario"]
    
    print(f"Pregunta recibida del usuario: '{pregunta}'")
    
    lista_contexto_faqs = buscar_en_base_de_conocimiento(
        consulta=pregunta,
        area_competencia="faqs"
    )
    
    contexto_faqs = "\n\n---\n\n".join(lista_contexto_faqs)
    
    print(f"Contexto recuperado del RAG: {contexto_faqs[:200]}...")

    # --- AQUI ESTA LA CORRECCION ---
    # 1. Construimos el prompt completo en una sola variable.
    #    Combinamos las instrucciones (prompt de sistema), el contexto y la pregunta.
    prompt_completo = f"""
    Eres un asistente virtual amable y servicial del Consultorio Juridico.
    Tu mision es responder la pregunta del usuario de forma clara y concisa.
    Basa tu respuesta EXCLUSIVAMENTE en el siguiente contexto que contiene el
    reglamento y las preguntas frecuentes del consultorio.
    Si la respuesta no esta en el contexto, indica amablemente que no tienes
    esa informacion y sugiere contactar al consultorio directamente.

    --- CONTEXTO DEL REGLAMENTO ---
    {contexto_faqs}
    --- FIN DEL CONTEXTO ---

    PREGUNTA DEL USUARIO: {pregunta}

    RESPUESTA AMABLE Y CONCISA:
    """

    # 2. Llamamos a la funcion con un UNICO argumento 'prompt'.
    respuesta_final = generar_respuesta_texto(prompt=prompt_completo)
    
    print(f"Respuesta generada por el agente: '{respuesta_final}'")

    return {"respuesta_agente": respuesta_final}

# --- Construccion del Grafo (se mantiene igual) ---

grafo_atencion = StateGraph(EstadoChat)
grafo_atencion.add_node("agente_atencion", nodo_agente_atencion)
grafo_atencion.set_entry_point("agente_atencion")
grafo_atencion.add_edge("agente_atencion", END)
grafo_atencion_compilado = grafo_atencion.compile()

print("SUCCESS (LANGGRAPH): Grafo del Agente de Atencion compilado exitosamente.")