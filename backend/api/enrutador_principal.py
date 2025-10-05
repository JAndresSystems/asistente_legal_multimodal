# backend/api/enrutador_principal.py

from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
import shutil
from pathlib import Path

from sqlmodel import Session
from ..base_de_datos import obtener_sesion
# Importamos los modelos de API que necesitamos, incluyendo los nuevos para el chat
from .modelos_compartidos import (
    Caso, CasoCreacion, Evidencia, CasoLecturaConEvidencias,
    PreguntaChat, RespuestaChat
)
# Importamos la tarea de Celery para el procesamiento de evidencias
from ..tareas import procesar_evidencia_tarea
# ¡NUEVA IMPORTACION! Importamos el grafo compilado de nuestro Agente de Atencion
from ..agentes.agente_atencion import grafo_atencion_compilado

# --- CONFIGURACION DE LOS ENRUTADORES ---

# Creamos un enrutador para las funciones relacionadas con los casos
router_casos = APIRouter(
    prefix="/casos",
    tags=["Gestion de Casos"]
)

# Creamos un enrutador separado para nuestro nuevo chatbot
router_chat = APIRouter(
    prefix="/chat",
    tags=["Chat de Atencion"]
)


# --- ENDPOINT DEL NUEVO CHATBOT ---

@router_chat.post("/", response_model=RespuestaChat)
def conversar_con_agente_atencion(pregunta: PreguntaChat):
    """
    Endpoint para interactuar con el Agente de Atencion (Chatbot de FAQs).

    Recibe una pregunta del usuario, la procesa con el grafo de atencion y
    devuelve la respuesta generada por la IA.
    """
    print(f"INFO: [API-CHAT] Peticion recibida: '{pregunta.pregunta}'")
    
    # Preparamos el estado inicial para el grafo de atencion
    estado_inicial_chat = {"pregunta_usuario": pregunta.pregunta}
    
    # Invocamos el grafo y obtenemos el estado final
    estado_final_chat = grafo_atencion_compilado.invoke(estado_inicial_chat)
    
    respuesta_generada = estado_final_chat.get("respuesta_agente", 
                                               "Lo siento, ocurrio un error al procesar tu pregunta.")
    
    print(f"INFO: [API-CHAT] Respuesta enviada: '{respuesta_generada}'")
    
    # Devolvemos la respuesta en el formato definido por RespuestaChat
    return RespuestaChat(respuesta=respuesta_generada)


# --- ENDPOINTS EXISTENTES DE GESTION DE CASOS ---

@router_casos.post("/", response_model=CasoLecturaConEvidencias, status_code=201)
def crear_caso(caso_a_crear: CasoCreacion, sesion: Session = Depends(obtener_sesion)):
    nuevo_caso_db = Caso.model_validate(caso_a_crear)
    sesion.add(nuevo_caso_db)
    sesion.commit()
    sesion.refresh(nuevo_caso_db)
    return nuevo_caso_db

@router_casos.get("/", response_model=list[CasoLecturaConEvidencias])
def listar_casos(sesion: Session = Depends(obtener_sesion)):
    casos = sesion.query(Caso).all()
    return casos

@router_casos.post("/{id_caso}/evidencia", response_model=CasoLecturaConEvidencias)
def subir_evidencia(id_caso: int, archivo: UploadFile = File(...), sesion: Session = Depends(obtener_sesion)):
    caso_actual = sesion.get(Caso, id_caso)
    if not caso_actual:
        raise HTTPException(status_code=404, detail="El caso no fue encontrado")
    
    ruta_guardado_caso = Path("backend/archivos_subidos") / str(id_caso)
    ruta_guardado_caso.mkdir(parents=True, exist_ok=True)
    ruta_archivo_final = ruta_guardado_caso / archivo.filename
    
    with open(ruta_archivo_final, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
        
    nueva_evidencia_db = Evidencia(
        id_caso=id_caso,
        ruta_archivo=str(ruta_archivo_final),
        estado="encolado"
    )
    
    sesion.add(nueva_evidencia_db)
    sesion.commit()
    sesion.refresh(nueva_evidencia_db)
    sesion.refresh(caso_actual)

    procesar_evidencia_tarea.delay(nueva_evidencia_db.id)

    return caso_actual

@router_casos.get("/evidencias/{id_evidencia}/estado", response_model=dict)
def obtener_estado_evidencia(id_evidencia: int, sesion: Session = Depends(obtener_sesion)):
    evidencia = sesion.get(Evidencia, id_evidencia)
    if not evidencia:
        raise HTTPException(status_code=404, detail="La evidencia no fue encontrada")
    
    return {"estado": evidencia.estado, "reporte": evidencia.reporte_analisis}

# Finalmente, necesitamos combinar estos enrutadores en nuestro archivo `main.py`.
# Este archivo no lo cambiamos, pero lo haremos en el siguiente paso.