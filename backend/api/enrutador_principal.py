# backend/api/enrutador_principal.py

from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
import shutil
from pathlib import Path

from sqlmodel import Session
from ..base_de_datos import obtener_sesion
from .modelos_compartidos import (
    Caso, CasoCreacion, Evidencia, CasoLecturaConEvidencias,
    PreguntaChat, RespuestaChat
)
from ..tareas import procesar_evidencia_tarea
# ==============================================================================
# INICIO DE LA RESTAURACION
# Volvemos a importar el grafo compilado, que es lo que este enrutador espera.
# ==============================================================================
from ..agentes.agente_atencion import grafo_atencion_compilado
# ==============================================================================
# FIN DE LA RESTAURACION
# ==============================================================================


# --- CONFIGURACION DE ENRUTADORES ---
router_casos = APIRouter(prefix="/casos", tags=["Gestion de Casos"])
router_chat = APIRouter(prefix="/chat", tags=["Chat de Atencion"])


# ==============================================================================
# INICIO DE LA RESTAURACION
# Volvemos al cuerpo original de la funcion que invoca el grafo.
# Se han añadido prints para depuracion y claridad.
# ==============================================================================
@router_chat.post("", response_model=RespuestaChat)
def conversar_con_agente_atencion(pregunta: PreguntaChat):
    """
    Docstring:
    Endpoint para interactuar con el Agente de Atencion.
    Recibe la pregunta del usuario, la pasa al grafo de LangGraph del agente
    y devuelve la respuesta generada.

    Args:
        pregunta (PreguntaChat): El objeto con el texto de la pregunta del usuario.

    Returns:
        RespuestaChat: El objeto con el texto de la respuesta del agente.
    """
    try:
        print(f"\n--- [API /chat] Peticion recibida. Pregunta: '{pregunta.pregunta}'")
        
        # 1. Preparamos el diccionario de entrada para el grafo.
        estado_inicial_chat = {"pregunta_usuario": pregunta.pregunta}
        print(f"--- [API /chat] Invocando el grafo del agente con el estado: {estado_inicial_chat}")

        # 2. Invocamos el grafo y esperamos el resultado.
        estado_final_chat = grafo_atencion_compilado.invoke(estado_inicial_chat)
        print(f"--- [API /chat] Grafo ejecutado. Estado final recibido: {estado_final_chat}")

        # 3. Extraemos la respuesta del diccionario de salida.
        #    La clave 'respuesta_agente' debe existir en el estado final.
        respuesta_generada = estado_final_chat.get("respuesta_agente", "Error: No se pudo obtener una respuesta del agente.")
        print(f"--- [API /chat] Respuesta extraida del estado: '{respuesta_generada}'")

        # 4. Devolvemos la respuesta en el formato correcto.
        return RespuestaChat(respuesta=respuesta_generada)
        
    except Exception as e:
        print(f"--- [API /chat] ERROR CRITICO: Ha ocurrido una excepcion no controlada en el endpoint: {e}")
        # En caso de un error inesperado, devolvemos un error 500.
        raise HTTPException(status_code=500, detail="Ocurrio un error interno en el servidor al procesar el chat.")
# ==============================================================================
# FIN DE LA RESTAURACION
# ==============================================================================


# --- ENDPOINTS DE GESTION DE CASOS (Sin cambios) ---
@router_casos.post("", response_model=CasoLecturaConEvidencias, status_code=201)
def crear_caso(caso_a_crear: CasoCreacion, sesion: Session = Depends(obtener_sesion)):
    nuevo_caso_db = Caso.from_orm(caso_a_crear)
    sesion.add(nuevo_caso_db)
    sesion.commit()
    sesion.refresh(nuevo_caso_db)
    return nuevo_caso_db

@router_casos.get("", response_model=list[CasoLecturaConEvidencias])
def listar_casos(sesion: Session = Depends(obtener_sesion)):
    casos = sesion.query(Caso).all()
    return casos

@router_casos.get("/{id_caso}", response_model=CasoLecturaConEvidencias)
def obtener_caso_por_id(id_caso: int, sesion: Session = Depends(obtener_sesion)):
    caso = sesion.get(Caso, id_caso)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    return caso

@router_casos.post("/{id_caso}/evidencia", response_model=Evidencia)
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
        estado="encolado",
        nombre_archivo=archivo.filename 
    )
    sesion.add(nueva_evidencia_db)
    sesion.commit()
    sesion.refresh(nueva_evidencia_db)

    procesar_evidencia_tarea.delay(nueva_evidencia_db.id)

    return nueva_evidencia_db