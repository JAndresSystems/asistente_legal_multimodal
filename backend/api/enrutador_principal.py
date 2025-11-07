# C:\react\asistente_legal_multimodal\backend\api\enrutador_principal.py
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

# Importaciones mínimas necesarias para las funciones que quedan
from ..base_de_datos import obtener_sesion
from .modelos_compartidos import PreguntaChat, RespuestaChat, Evidencia
from ..agentes.agente_atencion import grafo_atencion_compilado



# Definimos los routers que SÍ pertenecen a este archivo general
router_chat = APIRouter(prefix="/api/chat", tags=["Chat de Atencion"])
router_evidencias = APIRouter(prefix="/api/evidencias", tags=["Gestión de Evidencias"])




# --- ENDPOINT DEL CHAT DE ATENCION ---
@router_chat.post("/", response_model=RespuestaChat)
def conversar_con_agente_atencion(pregunta: PreguntaChat):
    """
    Endpoint para interactuar con el Agente de Atencion.
    Conectado al grafo de LangGraph original.
    """
    try:
        print(f"\n--- [API /chat] Peticion recibida. Pregunta: '{pregunta.pregunta}'")
        estado_inicial_chat = {"pregunta_usuario": pregunta.pregunta}
        print(f"--- [API /chat] Invocando el grafo del agente con el estado: {estado_inicial_chat}")
        estado_final_chat = grafo_atencion_compilado.invoke(estado_inicial_chat)
        print(f"--- [API /chat] Grafo ejecutado. Estado final recibido: {estado_final_chat}")
        respuesta_generada = estado_final_chat.get("respuesta_agente", "Error: No se pudo obtener una respuesta del agente.")
        print(f"--- [API /chat] Respuesta extraida del estado: '{respuesta_generada}'")
        return RespuestaChat(respuesta=respuesta_generada)
    except Exception as e:
        print(f"--- [API /chat] ERROR CRITICO: {e}")
        raise HTTPException(status_code=500, detail="Ocurrio un error interno en el servidor al procesar el chat.")

# --- ENDPOINTS DE GESTION DE CASOS ---

@router_evidencias.get("/{id_evidencia}/estado", response_model=Evidencia)
def obtener_estado_de_evidencia(id_evidencia: int, sesion: Session = Depends(obtener_sesion)):
    evidencia = sesion.get(Evidencia, id_evidencia)
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    return evidencia













    






