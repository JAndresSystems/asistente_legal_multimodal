# backend/agentes/estado_chat.py

from typing import TypedDict, Optional

class EstadoChat(TypedDict):
    """
    Define la estructura de datos simple para el flujo del Agente de Atencion.

    Actua como la memoria a corto plazo para una sola interaccion de chat.
    Contiene la pregunta del usuario y el espacio para la respuesta del agente.

    Atributos:
        pregunta_usuario (str): La pregunta exacta que el usuario escribe en el chat.
        respuesta_agente (Optional[str]): El texto que el agente genera como respuesta.
                                          Es opcional porque estara vacio al inicio.
    """
    # Dato de entrada que inicia el flujo.
    pregunta_usuario: str

    # Campo que el agente llenara con su resultado.
    respuesta_agente: Optional[str]