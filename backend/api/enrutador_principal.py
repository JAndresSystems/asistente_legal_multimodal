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
from ..agentes.agente_atencion import grafo_atencion_compilado

# --- CONFIGURACION DE ENRUTADORES (CORREGIDO) ---
# Eliminamos el argumento 'trailing_slash=False' que causaba el error.
router_casos = APIRouter(prefix="/casos", tags=["Gestion de Casos"])
router_chat = APIRouter(prefix="/chat", tags=["Chat de Atencion"])

# --- ENDPOINT DEL CHATBOT (Estable) ---
@router_chat.post("", response_model=RespuestaChat)
def conversar_con_agente_atencion(pregunta: PreguntaChat):
    estado_inicial_chat = {"pregunta_usuario": pregunta.pregunta}
    estado_final_chat = grafo_atencion_compilado.invoke(estado_inicial_chat)
    respuesta_generada = estado_final_chat.get("respuesta_agente", "Error al procesar la pregunta.")
    return RespuestaChat(respuesta=respuesta_generada)

# --- ENDPOINTS DE GESTION DE CASOS (Estables) ---
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
        
    print(f"API: Creando registro de evidencia para el archivo: {archivo.filename}")
    nueva_evidencia_db = Evidencia(
        id_caso=id_caso,
        ruta_archivo=str(ruta_archivo_final),
        estado="encolado" 
    )
    sesion.add(nueva_evidencia_db)
    sesion.commit()
    sesion.refresh(nueva_evidencia_db)

    print(f"API: Encolando tarea en Celery para evidencia ID: {nueva_evidencia_db.id}")
    procesar_evidencia_tarea.delay(nueva_evidencia_db.id)

    return nueva_evidencia_db

@router_casos.get("/evidencias/{id_evidencia}/estado", response_model=dict)
def obtener_estado_evidencia(id_evidencia: int, sesion: Session = Depends(obtener_sesion)):
    evidencia = sesion.get(Evidencia, id_evidencia)
    if not evidencia:
        raise HTTPException(status_code=404, detail="La evidencia no fue encontrada")
    
    return {"estado": evidencia.estado, "reporte": evidencia.reporte_analisis}