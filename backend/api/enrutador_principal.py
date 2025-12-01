import json
import re
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from ..base_de_datos import obtener_sesion
from .modelos_compartidos import PreguntaChat, Evidencia
from ..agentes.agente_atencion import grafo_atencion_compilado
from typing import Dict, Any

router_chat = APIRouter(prefix="/api/chat", tags=["Chat de Atencion"])
router_evidencias = APIRouter(prefix="/api/evidencias", tags=["Gestión de Evidencias"])

def _limpiar_respuesta_final(estado_final_del_grafo: dict) -> dict:
    """
    Función de limpieza robusta. Extrae el JSON anidado de la respuesta del LLM
    y lo devuelve como el objeto principal.
    """
    respuesta_agente = estado_final_del_grafo.get("respuesta_agente", {})
    texto_sucio = respuesta_agente.get("respuesta_texto", "")

    # Intenta encontrar un bloque JSON dentro de ```json ... ``` o un JSON suelto.
    match = re.search(r'\{.*\}', texto_sucio, re.DOTALL)
    if match:
        try:
            # Si encuentra un JSON y lo puede parsear, esa es nuestra respuesta limpia.
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            # Si el JSON está malformado, pasamos al fallback.
            pass

    # Fallback: si no hay JSON o falla el parseo, devolvemos una estructura válida
    # para que el frontend no se rompa, usando el texto sucio como mensaje.
    return {
        "respuesta_texto": texto_sucio or "No pude procesar la respuesta.",
        "iniciar_triaje": False
    }

@router_chat.post("/", response_model=Dict[str, Any])
def conversar_con_agente_atencion(pregunta: PreguntaChat):
    """
    Endpoint para interactuar con el Agente de Atencion.
    VERSIÓN FINAL CORREGIDA: Usa una función de limpieza que sí funciona.
    """
    try:
        print(f"\n--- [API /chat] Peticion recibida. Pregunta: '{pregunta.pregunta}'")
        
        input_dict = pregunta.model_dump(exclude_unset=True)
        estado_inicial_chat = {
            "pregunta_usuario": input_dict.get("pregunta", ""),
            "historial_chat": input_dict.get("historial_chat", [])
        }
        
        print(f"--- [API /chat] Invocando el grafo del agente con el estado: {estado_inicial_chat}")
        
        estado_final_chat = grafo_atencion_compilado.invoke(estado_inicial_chat)
        
        print(f"--- [API /chat] Grafo ejecutado. Respuesta original del agente: {estado_final_chat.get('respuesta_agente')}")
        
        respuesta_limpia = _limpiar_respuesta_final(estado_final_chat)
        
        print(f"--- [API /chat] Respuesta final limpia para frontend: {respuesta_limpia}")
        
        return respuesta_limpia

    except Exception as e:
        print(f"--- [API /chat] ERROR CRITICO: {e}")
        raise HTTPException(status_code=500, detail="Ocurrio un error interno en el servidor al procesar el chat.")

@router_evidencias.get("/{id_evidencia}/estado", response_model=Evidencia)
def obtener_estado_de_evidencia(id_evidencia: int, sesion: Session = Depends(obtener_sesion)):
    evidencia = sesion.get(Evidencia, id_evidencia)
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    return evidencia