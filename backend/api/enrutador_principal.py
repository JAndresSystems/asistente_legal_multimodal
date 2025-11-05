# C:\react\asistente_legal_multimodal\backend\api\enrutador_principal.py
from fastapi import APIRouter, HTTPException, File, UploadFile, Depends, status
import shutil
from pathlib import Path
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel

from ..base_de_datos import obtener_sesion
from .modelos_compartidos import (
    Caso, CasoCreacion, Evidencia, Nota, NotaCreacion, NotaLectura, 
    PreguntaChat, RespuestaChat, SolicitudAnalisis, Cuenta,
    Usuario, CasoLecturaUsuario, EstadoCaso, CasoDetalleUsuario,
    EvidenciaLecturaSimple, Asignacion, EstadoEvidencia,CasoLecturaConEvidencias
)
from ..tareas import procesar_evidencia_tarea
from ..agentes.agente_atencion import grafo_atencion_compilado
from ..seguridad.jwt_manager import obtener_cuenta_actual








# --- CONFIGURACION DE ENRUTADORES ---
router_casos = APIRouter(
    prefix="/api/casos",
    tags=["Casos (Ciudadano)"],
    dependencies=[Depends(obtener_cuenta_actual)]
)
router_expedientes = APIRouter(
    prefix="/api/expedientes",
    tags=["Expedientes (Estudiante)"],
    dependencies=[Depends(obtener_cuenta_actual)]
)
router_chat = APIRouter(
    prefix="/api/chat", 
    tags=["Chat de Atencion"]
)
router_evidencias = APIRouter(
    prefix="/api/evidencias", 
    tags=["Gestión de Evidencias"],
    dependencies=[Depends(obtener_cuenta_actual)]
)

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
def obtener_mis_casos(sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    if not cuenta_actual.usuario:
        raise HTTPException(status_code=404, detail="Perfil de usuario no encontrado.")
    casos = sesion.exec(select(Caso).where(Caso.id_usuario == cuenta_actual.usuario.id, Caso.estado != EstadoCaso.RECHAZADO).order_by(Caso.fecha_creacion.desc())).all()
    return casos


@router_expedientes.get("/mis-asignaciones", response_model=List[CasoLecturaUsuario])
def obtener_mis_asignaciones(sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    if not hasattr(cuenta_actual, 'estudiante') or not cuenta_actual.estudiante:
        raise HTTPException(status_code=403, detail="Esta cuenta no tiene un perfil de estudiante asociado.")
    
    id_estudiante = cuenta_actual.estudiante.id
    
    # Modificacion: Ahora obtenemos los casos de todas las asignaciones, sin importar su estado.
    # El frontend se encargara de diferenciar entre 'pendiente' y 'aceptado'.
    asignaciones = sesion.exec(
        select(Asignacion).where(Asignacion.id_estudiante == id_estudiante)
    ).all()

    if not asignaciones:
        return []
        
    ids_casos = [asig.id_caso for asig in asignaciones]
    casos = sesion.exec(select(Caso).where(Caso.id.in_(ids_casos)).order_by(Caso.fecha_creacion.desc())).all()
    return casos

@router_expedientes.post("/{id_caso}/aceptar", status_code=status.HTTP_200_OK)
def aceptar_asignacion(
    id_caso: int,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    if not cuenta_actual.estudiante:
        raise HTTPException(status_code=403, detail="Accion no permitida.")

    asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == id_caso, Asignacion.id_estudiante == cuenta_actual.estudiante.id)).first()
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignacion no encontrada.")
    if asignacion.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Esta asignacion ya ha sido procesada.")

    asignacion.estado = "aceptado"
    caso = sesion.get(Caso, id_caso)
    if caso:
        caso.estado = EstadoCaso.ASIGNADO
        sesion.add(caso)

    sesion.add(asignacion)
    sesion.commit()
    return {"mensaje": f"Caso {id_caso} aceptado exitosamente."}

@router_expedientes.post("/{id_caso}/rechazar", status_code=status.HTTP_200_OK)
def rechazar_asignacion(
    id_caso: int,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    if not cuenta_actual.estudiante:
        raise HTTPException(status_code=403, detail="Accion no permitida.")
        
    asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == id_caso, Asignacion.id_estudiante == cuenta_actual.estudiante.id)).first()
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignacion no encontrada.")
    if asignacion.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Esta asignacion ya ha sido procesada.")

    asignacion.estado = "rechazado"
    caso = sesion.get(Caso, id_caso)
    if caso:
        # Devolvemos el caso al estado de revision para una posible reasignacion
        caso.estado = EstadoCaso.EN_REVISION 
        sesion.add(caso)

    sesion.add(asignacion)
    sesion.commit()
    # TODO: En un futuro, aqui se podria disparar una tarea para reasignar el caso.
    return {"mensaje": f"Caso {id_caso} rechazado. Se notificara al administrador."}



@router_expedientes.post("/{id_caso}/subir-documento", response_model=Evidencia)
def subir_documento_estudiante(
    id_caso: int, 
    archivo: UploadFile = File(...), 
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Permite a un estudiante subir un documento a un caso que ha aceptado.
    """
    if not cuenta_actual.estudiante:
        raise HTTPException(status_code=403, detail="Solo los estudiantes pueden subir documentos.")

    # Validacion de seguridad: El estudiante debe estar asignado y haber aceptado el caso.
    asignacion = sesion.exec(
        select(Asignacion).where(
            Asignacion.id_caso == id_caso, 
            Asignacion.id_estudiante == cuenta_actual.estudiante.id,
            Asignacion.estado == "aceptado"
        )
    ).first()
    
    if not asignacion:
        raise HTTPException(status_code=403, detail="No tiene permiso para subir documentos a este caso.")

    # Lógica de guardado de archivo (similar a la del ciudadano)
    ruta_guardado_caso = Path("backend/archivos_subidos") / str(id_caso)
    ruta_guardado_caso.mkdir(parents=True, exist_ok=True)
    ruta_archivo_final = ruta_guardado_caso / archivo.filename
    
    with open(ruta_archivo_final, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
        
    # Creación del registro en BD, incluyendo el autor de la subida.
    nueva_evidencia_db = Evidencia(
        id_caso=id_caso, 
        ruta_archivo=str(ruta_archivo_final), 
        nombre_archivo=archivo.filename,
        tipo=archivo.content_type,
        subido_por_id_cuenta=cuenta_actual.id  # <-- CAMBIO CLAVE AQUI
    )
  
    sesion.add(nueva_evidencia_db)
    sesion.commit()
    sesion.refresh(nueva_evidencia_db)
    
    return nueva_evidencia_db


@router_expedientes.post("/{id_caso}/crear-nota", response_model=NotaLectura, status_code=status.HTTP_201_CREATED)
def crear_nota_estudiante(
    id_caso: int,
    solicitud: NotaCreacion,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Permite a un estudiante añadir una nota de texto a un caso que ha aceptado.
    """
    if not cuenta_actual.estudiante:
        raise HTTPException(status_code=403, detail="Solo los estudiantes pueden crear notas.")

    # Validacion de seguridad: El estudiante debe estar asignado y haber aceptado el caso.
    asignacion = sesion.exec(
        select(Asignacion).where(
            Asignacion.id_caso == id_caso,
            Asignacion.id_estudiante == cuenta_actual.estudiante.id,
            Asignacion.estado == "aceptado"
        )
    ).first()
    if not asignacion:
        raise HTTPException(status_code=403, detail="No tiene permiso para añadir notas a este caso.")

    # Creación del objeto Nota en la base de datos
    nueva_nota = Nota(
        id_caso=id_caso,
        contenido=solicitud.contenido,
        id_cuenta_autor=cuenta_actual.id
    )
    sesion.add(nueva_nota)
    sesion.commit()
    sesion.refresh(nueva_nota)
    
    return nueva_nota


@router_expedientes.get("/{id_caso}", response_model=CasoDetalleUsuario)
def obtener_detalle_expediente(id_caso: int, sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    # Tu validación de permisos es perfecta.
    if not hasattr(cuenta_actual, 'estudiante') or not cuenta_actual.estudiante:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")
    
    # Esta consulta ya te da acceso a todo lo que necesitas.
    asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == id_caso, Asignacion.id_estudiante == cuenta_actual.estudiante.id)).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada o sin permisos.")

    caso = asignacion.caso
    if not caso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso asociado a la asignación no encontrado.")
    
    # --- INICIO DE LA CORRECCIÓN ---

    # 1. Creamos la respuesta base a partir del objeto 'caso'.
    respuesta = CasoDetalleUsuario.model_validate(caso)

    # 2. Poblamos los nombres usando las relaciones del objeto 'asignacion'.
    if asignacion.estudiante:
        respuesta.estudiante_asignado = asignacion.estudiante.nombre_completo
        # El área la obtenemos a través del estudiante de la asignación.
        if asignacion.estudiante.area:
            respuesta.area_asignada = asignacion.estudiante.area.nombre
            
    if asignacion.asesor:
        respuesta.asesor_asignado = asignacion.asesor.nombre_completo

    # 3. Tu lógica para procesar evidencias es correcta y se mantiene.
    if caso.evidencias:
        respuesta.evidencias = []
        for evidencia in caso.evidencias:
            ruta_normalizada = str(evidencia.ruta_archivo).replace("\\", "/")
            prefijo = "backend/archivos_subidos/"
            ruta_relativa = ruta_normalizada[len(prefijo):] if ruta_normalizada.startswith(prefijo) else ruta_normalizada
            url_final_archivo = f"/archivos_subidos/{ruta_relativa}"
            respuesta.evidencias.append(
                EvidenciaLecturaSimple(
                    id=evidencia.id,
                    nombre_archivo=evidencia.nombre_archivo,
                    ruta_archivo=url_final_archivo,
                    estado=evidencia.estado
                )
            )
            
    return respuesta



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
def obtener_caso_por_id(id_caso: int, sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    caso = sesion.get(Caso, id_caso)
    if not caso or (not cuenta_actual.usuario or caso.id_usuario != cuenta_actual.usuario.id):
        raise HTTPException(status_code=404, detail="Caso no encontrado o sin permisos.")

    respuesta = CasoDetalleUsuario.model_validate(caso)
    
    # Poblar datos de la asignación si existe
    if caso.asignaciones:
        asignacion = caso.asignaciones[0]
        if asignacion.estudiante:
            respuesta.estudiante_asignado = asignacion.estudiante.nombre_completo
            # --- INICIO DE LA CORRECCION ---
            # Accedemos a la relación .area y luego a su atributo .nombre
            if asignacion.estudiante.area:
                respuesta.area_asignada = asignacion.estudiante.area.nombre
            # --- FIN DE LA CORRECCION ---
        if asignacion.asesor:
            respuesta.asesor_asignado = asignacion.asesor.nombre_completo
    
    # Poblar URLs de evidencias
    if caso.evidencias:
        respuesta.evidencias = [
             EvidenciaLecturaSimple(
                id=ev.id,
                nombre_archivo=ev.nombre_archivo,
                ruta_archivo=str(ev.ruta_archivo).replace("\\", "/").replace("backend/", "/"),
                estado=ev.estado
            ) for ev in caso.evidencias
        ]
            
    return respuesta

@router_evidencias.get("/{id_evidencia}/estado", response_model=Evidencia)
def obtener_estado_de_evidencia(id_evidencia: int, sesion: Session = Depends(obtener_sesion)):
    evidencia = sesion.get(Evidencia, id_evidencia)
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    return evidencia



@router_casos.post("/{id_caso}/subir-evidencia-simple", response_model=Evidencia)
def subir_evidencia_simple(
    id_caso: int, 
    archivo: UploadFile = File(...), 
    sesion: Session = Depends(obtener_sesion)
):
    caso_actual = sesion.get(Caso, id_caso)
    if not caso_actual: 
        raise HTTPException(status_code=404, detail="El caso no fue encontrado")

    ruta_guardado_caso = Path("backend/archivos_subidos") / str(id_caso)
    ruta_guardado_caso.mkdir(parents=True, exist_ok=True)
    
    ruta_archivo_final = ruta_guardado_caso / archivo.filename
    
    with open(ruta_archivo_final, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
        
    
    # crear la evidencia, tambien guardamos su tipo de contenido (MIME type).
    nueva_evidencia_db = Evidencia(
        id_caso=id_caso, 
        ruta_archivo=str(ruta_archivo_final), 
        estado="subido", 
        nombre_archivo=archivo.filename,
        tipo=archivo.content_type  
    )
  
    
    sesion.add(nueva_evidencia_db)
    sesion.commit()
    sesion.refresh(nueva_evidencia_db)
    
    return nueva_evidencia_db



@router_casos.post("/{id_caso}/analizar")
def analizar_caso_completo(id_caso: int, solicitud: SolicitudAnalisis, sesion: Session = Depends(obtener_sesion)):
    """
    Inicia la tarea de análisis y ESPERA a que se complete.
    Esta es la lógica correcta para el flujo interactivo del Agente de Triaje.
    """
    caso_actual = sesion.get(Caso, id_caso)
    if not caso_actual or not caso_actual.evidencias: 
        raise HTTPException(status_code=400, detail="No se pueden analizar casos sin evidencias.")
    
    # Se inicia la tarea en segundo plano...
    tarea_resultado = procesar_evidencia_tarea.delay(id_caso, solicitud.texto_adicional_usuario)
    
    try:
        # ...y el servidor ESPERA aquí hasta que la tarea termine o falle por timeout.
        estado_final = tarea_resultado.get(timeout=180) # Timeout de 3 minutos
        return estado_final
    except Exception as e:
        # Si la tarea tarda más de 3 minutos, se lanza el error 504.
        raise HTTPException(status_code=504, detail=f"El analisis del caso tardo demasiado en responder: {e}")






@router_expedientes.post("/documentos/{id_evidencia}/enviar-a-revision", status_code=status.HTTP_200_OK)
def enviar_documento_a_revision(
    id_evidencia: int,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Permite a un estudiante cambiar el estado de un documento de 'subido' a 'en_revision'.
    """
    # 1. Validar que el usuario es un estudiante
    if not cuenta_actual.estudiante:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acción no permitida para este rol.")

    # 2. Obtener el documento (evidencia) y validar su existencia
    documento = sesion.get(Evidencia, id_evidencia)
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")

    # 3. Validar que el estudiante tiene permiso sobre el caso de este documento
    asignacion = sesion.exec(
        select(Asignacion).where(
            Asignacion.id_caso == documento.id_caso,
            Asignacion.id_estudiante == cuenta_actual.estudiante.id,
            Asignacion.estado == "aceptado"
        )
    ).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permiso para modificar este documento.")

    # 4. Validar que el documento fue subido por el estudiante
    if documento.subido_por_id_cuenta != cuenta_actual.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puede enviar a revisión los documentos que usted ha subido.")

    # 5. Validar que el estado actual del documento es 'subido'
    if documento.estado != EstadoEvidencia.SUBIDO.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El documento no se puede enviar a revisión desde el estado actual ('{documento.estado}').")

    # 6. Actualizar el estado y guardar en la base de datos
    documento.estado = EstadoEvidencia.EN_REVISION.value
    sesion.add(documento)
    sesion.commit()
    sesion.refresh(documento)

    return {"mensaje": f"El documento '{documento.nombre_archivo}' ha sido enviado a revisión."}    