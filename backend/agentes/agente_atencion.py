# backend/agentes/agente_atencion.py

import json
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from .estado_chat import EstadoChat 
from ..herramientas.herramienta_rag import buscar_en_base_de_conocimiento
from ..herramientas.herramientas_lenguaje import generar_respuesta_texto

def _formatear_historial(historial: List[Dict[str, str]]) -> str:
    """Función utilitaria para convertir el historial en un string legible para el LLM."""
    if not historial:
        return "No hay conversación previa."
    
    texto_formateado = ""
    for mensaje in historial:
        rol = "Usuario" if mensaje.get("autor") == "usuario" else "Asistente"
        texto_formateado += f"{rol}: {mensaje.get('texto')}\n"
    return texto_formateado.strip()

def nodo_agente_atencion(estado: EstadoChat) -> Dict[str, Any]:
    print("\n--- [AGENTE ATENCION] Iniciando ejecucion del nodo ---")
    pregunta_actual = estado["pregunta_usuario"]
    historial_chat = estado.get("historial_chat", []) # Obtenemos el historial del estado
    
    print(f"--- [AGENTE ATENCION] Pregunta recibida: '{pregunta_actual}'")
    print(f"--- [AGENTE ATENCION] Historial con {len(historial_chat)} mensajes recibido.")
    
    try:
        lista_contexto_rag = buscar_en_base_de_conocimiento(consulta=pregunta_actual, n_resultados=5)
        contexto_rag = "\n\n---\n\n".join(lista_contexto_rag)
        print(f"--- [AGENTE ATENCION] Contexto recuperado de RAG.")
    except Exception as e:
        print(f"--- [AGENTE ATENCION] ERROR: Fallo al buscar en RAG: {e}")
        contexto_rag = "No se pudo recuperar informacion de soporte."

    # (MODIFICACIÓN 1) Prompt mejorado para incluir la memoria del chat.
    prompt_sistema = f"""
    Eres un asistente virtual que SÓLO responde con formato JSON. Tu respuesta COMPLETA debe empezar con `{{` y terminar con `}}`. No añadas NADA antes o después del objeto JSON.
    --- REGLA DE CITAS Y FUENTES ---
    Al citar el contexto legal, elimina cualquier extensión de archivo (.txt, .pdf). Indica siempre que la jurisprudencia o norma fue recuperada de la "Base de Datos Vectorial Chroma DB
    REGLAS DE SALIDA JSON:
    1.  Tu salida DEBE SER SIEMPRE un objeto JSON válido.
    2.  El objeto JSON debe tener dos claves: "respuesta_texto" (string) y "iniciar_triaje" (boolean).
    3.  Usa "iniciar_triaje": true si detectas en la conversación que el usuario quiere registrar un caso. De lo contrario, usa "iniciar_triaje": false.
    4.  Tu "respuesta_texto" debe ser amable, concisa y tener en cuenta el contexto de la conversación anterior para no ser repetitivo.

    --- CONVERSACIÓN ANTERIOR ---
    {_formatear_historial(historial_chat)}
    --- FIN CONVERSACIÓN ANTERIOR ---
    """

    prompt_final_para_llm = f"""
    {prompt_sistema}

    ---
    Informacion de Soporte (Contexto):
    {contexto_rag}
    ---

    Pregunta Actual del Usuario:
    {pregunta_actual}
    """

    try:
        respuesta_llm = generar_respuesta_texto(prompt=prompt_final_para_llm)
        respuesta_parseada = json.loads(respuesta_llm)
        respuesta_final = respuesta_parseada

    except Exception as e:
        print(f"--- [AGENTE ATENCION] ADVERTENCIA: LLM no devolvió un JSON válido ({e}). Generando fallback.")
        texto_fallback = respuesta_llm if isinstance(respuesta_llm, str) and not respuesta_llm.startswith('{') else "Lo siento, tuve un problema para procesar tu respuesta."
        respuesta_final = {
            "respuesta_texto": texto_fallback,
            "iniciar_triaje": False
        }

    return {"respuesta_agente": respuesta_final}

# --- Construccion del Grafo (Sin cambios) ---
grafo_atencion = StateGraph(EstadoChat)
grafo_atencion.add_node("agente_atencion", nodo_agente_atencion)
grafo_atencion.set_entry_point("agente_atencion")
grafo_atencion.add_edge("agente_atencion", END)
grafo_atencion_compilado = grafo_atencion.compile()

print("SUCCESS (LANGGRAPH): Grafo del Agente de Atencion (con memoria) compilado exitosamente.")