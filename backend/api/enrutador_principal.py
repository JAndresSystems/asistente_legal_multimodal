# backend/api/enrutador_principal.py

from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
import shutil
from pathlib import Path

from sqlmodel import Session
from ..base_de_datos import obtener_sesion
from .modelos_compartidos import (
    Caso, CasoCreacion, Evidencia, CasoLecturaConEvidencias,
    PreguntaChat, RespuestaChat,SolicitudAnalisis,Cuenta  
)
from ..tareas import procesar_evidencia_tarea

from ..agentes.agente_atencion import grafo_atencion_compilado

from ..seguridad.jwt_manager import obtener_cuenta_actual

# --- CONFIGURACION DE LOS ENRUTADORES ---

# Hacemos que TODOS los endpoints en router_casos requieran autenticacion
router_casos = APIRouter(
    prefix="/casos", 
    tags=["Gestion de Casos"],
    dependencies=[Depends(obtener_cuenta_actual)] # <-- ¡Guardian asignado!
)
# El router de chat permanece publico
router_chat = APIRouter(prefix="/chat", tags=["Chat de Atencion"])



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



# --- ENDPOINTS DE GESTION DE CASOS  ---
@router_casos.post("", response_model=CasoLecturaConEvidencias, status_code=201)
def crear_caso(
    caso_a_crear: CasoCreacion, 
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual) # <-- Obtenemos la cuenta del token
):
    """
    Docstring:
    Crea un nuevo caso asociado al usuario autenticado.
    El 'id_usuario' se obtiene del token, no del cuerpo de la peticion.
    """
    # El modelo 'CasoCreacion' ya no necesita el id_usuario, pero lo ignoramos
    # por ahora para no romper el frontend. La fuente de verdad es el token.
    if not cuenta_actual.usuario:
        raise HTTPException(status_code=403, detail="La cuenta no tiene un perfil de usuario asociado.")
        
    nuevo_caso_db = Caso(
        descripcion_hechos=caso_a_crear.descripcion_hechos,
        id_usuario=cuenta_actual.usuario.id
    )
    sesion.add(nuevo_caso_db)
    sesion.commit()
    sesion.refresh(nuevo_caso_db)
    return nuevo_caso_db

# @router_casos.get("", response_model=list[CasoLecturaConEvidencias])
# def listar_casos(sesion: Session = Depends(obtener_sesion)):
#     casos = sesion.query(Caso).all()
#     return casos

@router_casos.get("/{id_caso}", response_model=CasoLecturaConEvidencias)
def obtener_caso_por_id(
    id_caso: int, 
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    caso = sesion.get(Caso, id_caso)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    # --- REGLA DE AUTORIZACION ---
    # Un usuario solo puede ver sus propios casos.
    if caso.id_usuario != cuenta_actual.usuario.id:
        raise HTTPException(status_code=403, detail="No tiene permiso para acceder a este caso.")
        
    return caso

@router_casos.post("/{id_caso}/subir-evidencia-simple", response_model=Evidencia)
def subir_evidencia_simple(id_caso: int, archivo: UploadFile = File(...), sesion: Session = Depends(obtener_sesion)):
    """
    Docstring:
    Sube un archivo de evidencia, lo guarda en disco y crea el registro en la BD.
    NO inicia ninguna tarea de analisis. Es una operacion rapida.
    """
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
        estado="subido", # Nuevo estado para indicar que solo esta guardado
        nombre_archivo=archivo.filename
    )
    sesion.add(nueva_evidencia_db)
    sesion.commit()
    sesion.refresh(nueva_evidencia_db)

    print(f"API: Archivo '{archivo.filename}' guardado para el Caso ID {id_caso}.")
    
    return nueva_evidencia_db

# 2. Nuevo endpoint para iniciar el analisis consolidado
@router_casos.post("/{id_caso}/analizar")
def analizar_caso_completo(id_caso: int, solicitud: SolicitudAnalisis, sesion: Session = Depends(obtener_sesion)):
    """
    Docstring:
    Inicia la tarea de analisis consolidado para un caso, espera el resultado
    y lo devuelve.
    """
    caso_actual = sesion.get(Caso, id_caso)
    if not caso_actual:
        raise HTTPException(status_code=404, detail="El caso no fue encontrado")
    if not caso_actual.evidencias:
        raise HTTPException(status_code=400, detail="No se pueden analizar casos sin evidencias.")

    print(f"API: Solicitud de analisis para el Caso ID {id_caso}. Encolando tarea...")
    
    # Llamamos a la tarea pasandole solo el ID del caso.
    tarea_resultado = procesar_evidencia_tarea.delay(id_caso, solicitud.texto_adicional_usuario)
    
    print(f"API: Tarea encolada con ID {tarea_resultado.id}. Esperando resultado...")
    
    try:
        estado_final = tarea_resultado.get(timeout=120)
    except Exception as e:
        print(f"API: Error esperando el resultado de la tarea: {e}")
        raise HTTPException(status_code=504, detail="El analisis del caso tardo demasiado en responder.")

    print(f"API: Analisis completado. Devolviendo estado final al frontend.")
    
    return estado_final