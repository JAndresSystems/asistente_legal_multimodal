# backend/agentes/agente_atencion.py

from typing import Dict
from langgraph.graph import StateGraph, END

# Suponiendo que el estado del chat se define en un archivo como este
from .estado_chat import EstadoChat 

from ..herramientas.herramienta_rag import buscar_en_base_de_conocimiento
from ..herramientas.herramientas_lenguaje import generar_respuesta_texto

def nodo_agente_atencion(estado: EstadoChat) -> Dict[str, str]:
    """
    Docstring:
    Este es el nodo principal del Agente de Atencion. Su funcion es generar
    una respuesta informativa y concisa a la pregunta del usuario, usando
    la nueva logica de "recepcionista virtual".

    Args:
        estado (EstadoChat): El estado del grafo que contiene la pregunta del usuario.

    Returns:
        Dict[str, str]: Un diccionario para actualizar el estado con la respuesta generada.
    """
    print("\n--- [AGENTE ATENCION] Iniciando ejecucion del nodo ---")
    pregunta = estado["pregunta_usuario"]
    print(f"--- [AGENTE ATENCION] Pregunta recibida: '{pregunta}'")
    
    try:
        # --- MODIFICACION: La llamada ahora es más simple ---
        lista_contexto_rag = buscar_en_base_de_conocimiento(consulta=pregunta, n_resultados=8)
        contexto_rag = "\n\n---\n\n".join(lista_contexto_rag)
        print(f"--- [AGENTE ATENCION] Contexto recuperado de RAG.")
    except Exception as e:
        print(f"--- [AGENTE ATENCION] ERROR: Fallo al buscar en RAG: {e}")
        contexto_rag = "No se pudo recuperar informacion de soporte."

    prompt_sistema = """
    Eres el recepcionista virtual del Consultorio Juridico. Tu unica mision es dar respuestas informativas y cortas.

    REGLAS ESTRICTAS E INQUEBRANTABLES:
    1.  Tus respuestas DEBEN ser clarar, amable , precisas de entender y faciles de entender; recuerda que estas 
    hablando con personas (usuarios) de baja formación academica con bajo conocimiento legal, debes explciarles 
    mostrarse paciente sin perder la objetividad por ningun motivo, es decir si ves que el usuario se esta deviando
    del tema intenta centrarlo en la conversación centrada del caso. Usa maximo dos o tres frases.
    2.  NO eres un abogado. NO puedes dar consejos legales, analizar, interpretar o calificar un caso.
    3.  En el momento en que el usuario este describiendo un caso, debes ir entendiendo de que se trata ponte en el rol 
    de un abogado experto y pideloe contexto sin usar demasiados contextos legales (es decir pidele contexto al usuario
    claramente que le estas pidiendo como informacion)
    4.  Tu objetivo final es que el usuario que tiene un problema legal use el boton "Tengo un caso y quiero registrarlo".
    5.  Usa la "Informacion de Soporte" para responder preguntas sobre el consultorio (horarios, costos, servicios). Si no sabes la respuesta, di que no tienes esa informacion.

    EJEMPLO DE INTERACCION:
    Usuario: "Hola, mi vecino me esta corriendo los linderos de mi finca y no se que hacer, estoy desesperado."
    Tu Respuesta: "Entiendo. Para poder ayudarte con tu situacion, el primer paso es registrar formalmente tu caso. Por favor, usa el boton 'Tengo un caso y quiero registrarlo' para comenzar."
    """

    prompt_final_para_llm = f"""
    {prompt_sistema}

    ---
    Informacion de Soporte (Contexto):
    {contexto_rag}
    ---

    Pregunta del Usuario:
    {pregunta}
    """

    try:
        
        respuesta_final = generar_respuesta_texto(prompt=prompt_final_para_llm)
        
        print(f"--- [AGENTE ATENCION] Respuesta generada por LLM: '{respuesta_final}'")
    except Exception as e:
        print(f"--- [AGENTE ATENCION] ERROR: Fallo al generar texto con LLM: {e}")
        respuesta_final = "Lo siento, estoy teniendo problemas para procesar tu solicitud en este momento."

    return {"respuesta_agente": respuesta_final}

# --- Construccion del Grafo  ---
grafo_atencion = StateGraph(EstadoChat)
grafo_atencion.add_node("agente_atencion", nodo_agente_atencion)
grafo_atencion.set_entry_point("agente_atencion")
grafo_atencion.add_edge("agente_atencion", END)
grafo_atencion_compilado = grafo_atencion.compile()

print("SUCCESS (LANGGRAPH): Grafo del Agente de Atencion compilado exitosamente.")