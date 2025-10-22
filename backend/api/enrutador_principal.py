# C:\react\asistente_legal_multimodal\backend\api\enrutador_principal.py
from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
import shutil
from pathlib import Path
from sqlmodel import Session, select
from typing import List

from ..base_de_datos import obtener_sesion
from .modelos_compartidos import (
    Caso, CasoCreacion, Evidencia, CasoLecturaConEvidencias,
    PreguntaChat, RespuestaChat, SolicitudAnalisis, Cuenta,
    Usuario, CasoLecturaUsuario, EstadoCaso, CasoDetalleUsuario,
    EvidenciaLecturaSimple
)
from ..tareas import procesar_evidencia_tarea
from ..agentes.agente_atencion import grafo_atencion_compilado
from ..seguridad.jwt_manager import obtener_cuenta_actual

# --- CONFIGURACION DE ENRUTADORES ---
router_casos = APIRouter(prefix="/casos", tags=["Gestion de Casos"], dependencies=[Depends(obtener_cuenta_actual)])
router_chat = APIRouter(prefix="/chat", tags=["Chat de Atencion"])
router_evidencias = APIRouter(prefix="/evidencias", tags=["Gestion de Evidencias"], dependencies=[Depends(obtener_cuenta_actual)])

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
@router_casos.get("/mis-casos", response_model=List[CasoLecturaUsuario])
def obtener_mis_casos(
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Endpoint para que un usuario obtenga la lista de sus casos ACTIVOS.
    (Ahora filtra los casos rechazados).
    """
    if not cuenta_actual.usuario:
        raise HTTPException(status_code=404, detail="Perfil de usuario no encontrado.")
    
    casos_del_usuario = sesion.exec(
        select(Caso).where(
            Caso.id_usuario == cuenta_actual.usuario.id,
            Caso.estado != EstadoCaso.RECHAZADO
        ).order_by(Caso.fecha_creacion.desc())
    ).all()
    return casos_del_usuario

@router_casos.post("", response_model=CasoLecturaConEvidencias, status_code=201)
def crear_caso(caso_a_crear: CasoCreacion, sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    if not cuenta_actual.usuario:
        raise HTTPException(status_code=403, detail="La cuenta no tiene un perfil de usuario asociado.")
    nuevo_caso_db = Caso(descripcion_hechos=caso_a_crear.descripcion_hechos, id_usuario=cuenta_actual.usuario.id)
    sesion.add(nuevo_caso_db)
    sesion.commit()
    sesion.refresh(nuevo_caso_db)
    return nuevo_caso_db

@router_casos.get("/{id_caso}", response_model=CasoDetalleUsuario)
def obtener_caso_por_id(
    id_caso: int,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Obtiene los detalles completos y enriquecidos de un caso para la vista
    del usuario ciudadano, incluyendo la informacion de la asignacion.
    """
    caso = sesion.get(Caso, id_caso)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    if not cuenta_actual.usuario or caso.id_usuario != cuenta_actual.usuario.id:
        raise HTTPException(status_code=403, detail="No tiene permiso para acceder a este caso.")

    respuesta = CasoDetalleUsuario.model_validate(caso)

    # ==============================================================================
    # INICIO DE LA CORRECCION: Reemplazamos la logica de rutas por una mas robusta
    # ==============================================================================
    if caso.evidencias:
      respuesta.evidencias = []
      for evidencia in caso.evidencias:
          # Convertimos la ruta a un string y reemplazamos las barras invertidas
          # para asegurar consistencia entre sistemas operativos.
          ruta_normalizada = str(evidencia.ruta_archivo).replace("\\", "/")
          
          # Eliminamos el prefijo si existe, de lo contrario usamos la ruta tal cual.
          prefijo = "backend/archivos_subidos/"
          if ruta_normalizada.startswith(prefijo):
              ruta_relativa = ruta_normalizada[len(prefijo):]
          else:
              ruta_relativa = ruta_normalizada

          respuesta.evidencias.append(
              EvidenciaLecturaSimple(
                  id=evidencia.id,
                  nombre_archivo=evidencia.nombre_archivo,
                  ruta_archivo=ruta_relativa
              )
          )
    # ==============================================================================
    # FIN DE LA CORRECCION
    # ==============================================================================

    if not caso.reporte_consolidado:
        respuesta.reporte_consolidado = None

    if caso.asignaciones:
        asignacion = caso.asignaciones[0]
        if asignacion.estudiante:
            respuesta.estudiante_asignado = asignacion.estudiante.nombre_completo
            respuesta.area_asignada = asignacion.estudiante.area_especialidad
        if asignacion.asesor:
            respuesta.asesor_asignado = asignacion.asesor.nombre_completo
            
    return respuesta

@router_evidencias.get("/{id_evidencia}/estado", response_model=Evidencia)
def obtener_estado_de_evidencia(id_evidencia: int, sesion: Session = Depends(obtener_sesion)):
    evidencia = sesion.get(Evidencia, id_evidencia)
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    return evidencia

@router_casos.post("/{id_caso}/subir-evidencia-simple", response_model=Evidencia)
def subir_evidencia_simple(id_caso: int, archivo: UploadFile = File(...), sesion: Session = Depends(obtener_sesion)):
    caso_actual = sesion.get(Caso, id_caso)
    if not caso_actual: raise HTTPException(status_code=404, detail="El caso no fue encontrado")
    ruta_guardado_caso = Path("backend/archivos_subidos") / str(id_caso)
    ruta_guardado_caso.mkdir(parents=True, exist_ok=True)
    ruta_archivo_final = ruta_guardado_caso / archivo.filename
    with open(ruta_archivo_final, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
    nueva_evidencia_db = Evidencia(id_caso=id_caso, ruta_archivo=str(ruta_archivo_final), estado="subido", nombre_archivo=archivo.filename)
    sesion.add(nueva_evidencia_db)
    sesion.commit()
    sesion.refresh(nueva_evidencia_db)
    return nueva_evidencia_db

@router_casos.post("/{id_caso}/analizar")
def analizar_caso_completo(id_caso: int, solicitud: SolicitudAnalisis, sesion: Session = Depends(obtener_sesion)):
    caso_actual = sesion.get(Caso, id_caso)
    if not caso_actual or not caso_actual.evidencias: raise HTTPException(status_code=400, detail="No se pueden analizar casos sin evidencias.")
    tarea_resultado = procesar_evidencia_tarea.delay(id_caso, solicitud.texto_adicional_usuario)
    try:
        estado_final = tarea_resultado.get(timeout=120)
        return estado_final
    except Exception as e:
        raise HTTPException(status_code=504, detail=f"El analisis del caso tardo demasiado en responder.")